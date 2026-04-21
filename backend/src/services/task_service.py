"""
Task service - orchestrates task creation and processing workflow.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, Callable
import logging
from datetime import datetime
from pathlib import Path
import json
import asyncio
import cv2
import hashlib
from time import perf_counter

import redis.asyncio as redis

from ..repositories.task_repository import TaskRepository
from ..repositories.source_repository import SourceRepository
from ..repositories.clip_repository import ClipRepository
from ..repositories.cache_repository import CacheRepository
from .video_service import VideoService
from ..config import Config
from ..clip_editor import (
    trim_clip_file,
    split_clip_file,
    merge_clip_files,
    overlay_custom_captions,
)
from ..video_utils import parse_timestamp_to_seconds

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task workflow orchestration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository()
        self.source_repo = SourceRepository()
        self.clip_repo = ClipRepository()
        self.cache_repo = CacheRepository()
        self.video_service = VideoService()
        self.config = Config()
        
        # New Phase 2 Services
        from .analytics_service import AnalyticsService
        from .webhook_service import WebhookService
        self.analytics = AnalyticsService()
        self.webhooks = WebhookService()

    @staticmethod
    def _build_cache_key(url: str, source_type: str, processing_mode: str) -> str:
        payload = f"{source_type}|{processing_mode}|{url.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _is_stale_queued_task(self, task: Dict[str, Any]) -> bool:
        """Detect queued tasks that have likely stalled due to worker issues."""
        if task.get("status") != "queued":
            return False

        created_at = task.get("created_at")
        updated_at = task.get("updated_at") or created_at

        if not created_at or not updated_at:
            return False

        # Handle SQLite returning datetimes as strings
        if isinstance(created_at, str):
            try:
                from dateutil import parser
                created_at = parser.parse(created_at)
            except (ImportError, ValueError):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    return False
                    
        if isinstance(updated_at, str):
            try:
                from dateutil import parser
                updated_at = parser.parse(updated_at)
            except (ImportError, ValueError):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                except ValueError:
                    return False

        now = (
            datetime.now(updated_at.tzinfo)
            if getattr(updated_at, "tzinfo", None)
            else datetime.utcnow()
        )
        age_seconds = (now - updated_at).total_seconds()
        return age_seconds >= self.config.queued_task_timeout_seconds

    async def create_task_with_source(
        self,
        user_id: str,
        url: str,
        title: Optional[str] = None,
        font_family: str = "TikTokSans-Regular",
        font_size: int = 24,
        font_color: str = "#FFFFFF",
        caption_template: str = "default",
        include_broll: bool = False,
        processing_mode: str = "fast",
        enable_bypass: bool = False,
        enable_zoom: bool = False,
        enable_blur_bg: bool = False,
        target_language: Optional[str] = None,
        task_mode: str = "clips",
        narration_script: Optional[str] = None,
        tts_voice: Optional[str] = None,
    ) -> str:
        """
        Create a new task with associated source.
        Returns the task ID.
        """
        if not await self.task_repo.user_exists(self.db, user_id):
            if self.config.self_host or user_id == "local_user":
                from sqlalchemy import text
                # Ensure local user exists with required name and email
                await self.db.execute(
                    text("""
                        INSERT OR IGNORE INTO users (id, name, email, "emailVerified") 
                        VALUES (:id, :name, :email, :email_verified)
                    """),
                    {
                        "id": user_id, 
                        "name": "Local User", 
                        "email": f"{user_id}@local.supoclip.com",
                        "email_verified": False
                    }
                )
                await self.db.commit()
            else:
                raise ValueError(f"User {user_id} not found")

        # Determine source type
        source_type = self.video_service.determine_source_type(url)

        # Get or generate title
        if not title:
            if source_type in ("youtube", "bilibili", "douyin"):
                title = await self.video_service.get_video_title(url)
            else:
                title = "Uploaded Video"

        # Create source
        source_id = await self.source_repo.create_source(
            self.db, source_type=source_type, title=title, url=url
        )

        # Create task
        task_id = await self.task_repo.create_task(
            self.db,
            user_id=user_id,
            source_id=source_id,
            status="queued",
            font_family=font_family,
            font_size=font_size,
            font_color=font_color,
            caption_template=caption_template,
            include_broll=include_broll,
            processing_mode=processing_mode,
            enable_bypass=enable_bypass,
            enable_zoom=enable_zoom,
            enable_blur_bg=enable_blur_bg,
            target_language=target_language,
            task_mode=task_mode,
            narration_script=narration_script,
            tts_voice=tts_voice,
        )

        logger.info(f"Created task {task_id} for user {user_id}")
        return task_id

    async def analyze_video_for_dubbing(self, url: str) -> Dict[str, Any]:
        """
        Download video, transcribe, and generate a localized script preview.
        """
        from ..ai import get_smart_script_for_dubbing
        
        source_type = self.video_service.determine_source_type(url)
        title = await self.video_service.get_video_title(url)
        
        # 1. Get video
        if source_type in ("youtube", "bilibili", "douyin"):
            video_path = await self.video_service.download_video(url)
            if not video_path:
                raise ValueError("Failed to download video")
        else:
            video_path = self.video_service.resolve_local_video_path(url)
            if not video_path.exists():
                raise ValueError("Video file not found")
        
        # 2. Transcribe
        transcript = await self.video_service.generate_transcript(video_path)
        
        # 3. Analyze & Rewrite
        segments = await get_smart_script_for_dubbing(transcript, title)
        
        return {
            "title": title,
            "transcript": transcript,
            "segments": segments
        }

    async def process_task(
        self,
        task_id: str,
        url: str,
        source_type: str,
        font_family: str = "TikTokSans-Regular",
        font_size: int = 24,
        font_color: str = "#FFFFFF",
        caption_template: str = "default",
        processing_mode: str = "fast",
        output_format: str = "vertical",
        add_subtitles: bool = True,
        enable_bypass: bool = False,
        enable_zoom: bool = False,
        enable_blur_bg: bool = False,
        target_language: Optional[str] = None,
        task_mode: str = "clips",
        narration_script: Optional[str] = None,
        tts_voice: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        should_cancel: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Process a task: download video, analyze, create clips.
        Returns processing results.
        """
        if task_mode == "full_dubbing":
            return await self._process_full_dubbing(
                task_id=task_id,
                url=url,
                source_type=source_type,
                narration_script=narration_script,
                tts_voice=tts_voice,
                progress_callback=progress_callback,
                should_cancel=should_cancel,
            )

        try:
            logger.info(f"Starting processing for task {task_id}")
            started_at = datetime.utcnow()
            stage_timings: Dict[str, float] = {}
            cache_key = self._build_cache_key(url, source_type, processing_mode)

            cache_entry = await self.cache_repo.get_cache(self.db, cache_key)
            cached_transcript = (
                cache_entry.get("transcript_text") if cache_entry else None
            )
            cached_analysis_json = (
                cache_entry.get("analysis_json") if cache_entry else None
            )
            cache_hit = bool(cached_transcript and cached_analysis_json)

            await self.task_repo.update_task_runtime_metadata(
                self.db,
                task_id,
                started_at=started_at,
                cache_hit=cache_hit,
            )

            # Update status to processing
            await self.task_repo.update_task_status(
                self.db,
                task_id,
                "processing",
                progress=0,
                progress_message="Starting...",
            )

            # Progress callback wrapper
            async def update_progress(
                progress: int, message: str, status: str = "processing"
            ):
                await self.task_repo.update_task_status(
                    self.db,
                    task_id,
                    status,
                    progress=progress,
                    progress_message=message,
                )
                if progress_callback:
                    await progress_callback(progress, message, status)

            # Process video with progress updates
            pipeline_start = perf_counter()
            result = await self.video_service.process_video_complete(
                url=url,
                source_type=source_type,
                font_family=font_family,
                font_size=font_size,
                font_color=font_color,
                caption_template=caption_template,
                processing_mode=processing_mode,
                output_format=output_format,
                add_subtitles=add_subtitles,
                enable_bypass=enable_bypass,
                enable_zoom=enable_zoom,
                enable_blur_bg=enable_blur_bg,
                target_language=target_language,
                tts_voice=tts_voice,
                task_mode=task_mode,
                cached_transcript=cached_transcript,
                cached_analysis_json=cached_analysis_json,
                progress_callback=update_progress,
                should_cancel=should_cancel,
            )
            stage_timings["pipeline_seconds"] = round(
                perf_counter() - pipeline_start, 3
            )

            await self.cache_repo.upsert_cache(
                self.db,
                cache_key=cache_key,
                source_url=url,
                source_type=source_type,
                transcript_text=result.get("transcript"),
                analysis_json=result.get("analysis_json"),
            )

            # Save clips to database
            await self.task_repo.update_task_status(
                self.db,
                task_id,
                "processing",
                progress=95,
                progress_message="Saving clips...",
            )

            clip_ids = []
            save_start = perf_counter()
            for i, clip_info in enumerate(result["clips"]):
                clip_id = await self.clip_repo.create_clip(
                    self.db,
                    task_id=task_id,
                    filename=clip_info["filename"],
                    file_path=clip_info["path"],
                    start_time=clip_info["start_time"],
                    end_time=clip_info["end_time"],
                    duration=clip_info["duration"],
                    text=clip_info["text"],
                    relevance_score=clip_info["relevance_score"],
                    reasoning=clip_info["reasoning"],
                    clip_order=i + 1,
                    virality_score=clip_info.get("virality_score", 0),
                    hook_score=clip_info.get("hook_score", 0),
                    engagement_score=clip_info.get("engagement_score", 0),
                    value_score=clip_info.get("value_score", 0),
                    shareability_score=clip_info.get("shareability_score", 0),
                    hook_type=clip_info.get("hook_type"),
                    rank=clip_info.get("rank", "C"),
                )
                clip_ids.append(clip_id)

            stage_timings["save_seconds"] = round(perf_counter() - save_start, 3)

            # Update task with clip IDs
            await self.task_repo.update_task_clips(self.db, task_id, clip_ids)

            # Mark as completed
            await self.task_repo.update_task_status(
                self.db,
                task_id,
                "completed",
                progress=100,
                progress_message="Complete!",
            )

            if progress_callback:
                await progress_callback(100, "Complete!", "completed")

            await self.task_repo.update_task_runtime_metadata(
                self.db,
                task_id,
                completed_at=datetime.utcnow(),
                stage_timings_json=json.dumps(stage_timings),
                error_code="",
            )

            # Phase 2: Log analytics and send webhook
            try:
                await self.analytics.log_clip_scores(task_id, source_type, result["clips"])
                await self.webhooks.send_notification(task_id, "completed", {
                    "clips_count": len(clip_ids),
                    "summary": result.get("summary")
                })
            except Exception as e:
                logger.error(f"Failed to process Phase 2 post-processing: {e}")

            logger.info(
                f"Task {task_id} completed successfully with {len(clip_ids)} clips"
            )

            return {
                "task_id": task_id,
                "clips_count": len(clip_ids),
                "segments": result.get("segments", []),
                "summary": result.get("summary", ""),
                "key_topics": result.get("key_topics", []),
            }

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            if str(e) == "Task cancelled":
                await self.task_repo.update_task_status(
                    self.db,
                    task_id,
                    "cancelled",
                    progress=0,
                    progress_message="Cancelled by user",
                )
                raise
            await self.task_repo.update_task_status(
                self.db, task_id, "error", progress_message=str(e)
            )
            error_code = "task_error"
            message = str(e).lower()
            if "download" in message:
                error_code = "download_error"
            elif "transcript" in message:
                error_code = "transcription_error"
            elif "analysis" in message:
                error_code = "analysis_error"
            elif "cancelled" in message:
                error_code = "cancelled"

            await self.task_repo.update_task_runtime_metadata(
                self.db,
                task_id,
                completed_at=datetime.utcnow(),
                error_code=error_code,
            )
            raise

    async def dub_clip(
        self, 
        task_id: str, 
        clip_id: str, 
        text: str, 
        voice: str = "vi-VN-NamMinhNeural"
    ) -> Dict[str, Any]:
        """Synthesize TTS for a clip and mix it into the video."""
        from ..services.tts_service import TTSService
        from ..clip_editor import mix_tts_with_video
        from pathlib import Path
        import uuid

        clip = await self.clip_repo.get_clip_by_id(self.db, clip_id)
        if not clip or clip.get("task_id") != task_id:
            raise ValueError("Clip not found or unauthorized")

        # Fallback to clip's existing text if provided text is empty
        if not text:
            text = clip.get("text") or ""
        
        if not text:
            raise ValueError("Text is required for dubbing (no transcript available)")

        # 1. Generate speech
        tts_filename = f"dub_{uuid.uuid4()}.mp3"
        tts_path = Path(self.config.temp_dir) / "clips" / tts_filename
        tts_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use edge-tts directly via our static helper
        await TTSService.generate_speech(text, voice, str(tts_path))
        
        if not tts_path.exists():
            raise ValueError("Failed to generate speech for dubbing")

        # 2. Mix with video
        input_video = Path(clip["file_path"])
        if not input_video.exists():
            raise ValueError(f"Original clip file not found at {input_video}")

        output_filename = f"dubbed_{clip['filename']}"
        output_path = Path(self.config.temp_dir) / "clips" / output_filename
        
        # Overlay TTS onto video with background ducking
        success = await mix_tts_with_video(str(input_video), str(tts_path), str(output_path))
        
        if not success or not output_path.exists():
            raise ValueError("Failed to mix TTS with video")

        # 3. Update database
        # Duration might have changed if TTS is longer, but usually we keep video length
        # For simplicity, we just update the path and text
        await self.clip_repo.update_clip(
            self.db,
            clip_id,
            filename=output_filename,
            file_path=str(output_path),
            start_time=clip["start_time"],
            end_time=clip["end_time"],
            duration=clip["duration"],
            text=text
        )

        # Cleanup tts temp file
        try:
            tts_path.unlink(missing_ok=True)
        except:
            pass

        return await self.clip_repo.get_clip_by_id(self.db, clip_id) or {}

    async def get_task_with_clips(self, task_id: str) -> Optional[Dict[str, Any]]:

        """Get task details with all clips."""
        task = await self.task_repo.get_task_by_id(self.db, task_id)

        if not task:
            return None

        if self._is_stale_queued_task(task):
            timeout_seconds = self.config.queued_task_timeout_seconds
            logger.warning(
                f"Task {task_id} stuck in queued status for over {timeout_seconds}s; marking as error"
            )
            await self.task_repo.update_task_status(
                self.db,
                task_id,
                "error",
                progress=0,
                progress_message=(
                    "Task timed out while waiting in queue. "
                    "Ensure the worker service is running and healthy (docker-compose logs -f worker)."
                ),
            )
            task = await self.task_repo.get_task_by_id(self.db, task_id)
            if not task:
                return None

        # Get clips
        clips = await self.clip_repo.get_clips_by_task(self.db, task_id)
        task["clips"] = clips
        task["clips_count"] = len(clips)

        return task

    async def get_user_tasks(
        self, user_id: str, limit: int = 50
    ) -> list[Dict[str, Any]]:
        """Get all tasks for a user."""
        return await self.task_repo.get_user_tasks(self.db, user_id, limit)

    async def delete_task(self, task_id: str) -> None:
        """Delete a task and all its associated clips."""
        # Delete all clips for this task
        await self.clip_repo.delete_clips_by_task(self.db, task_id)

        # Delete the task
        await self.task_repo.delete_task(self.db, task_id)

        logger.info(f"Deleted task {task_id} and all associated clips")

    async def update_task_settings(
        self,
        task_id: str,
        font_family: str,
        font_size: int,
        font_color: str,
        include_broll: bool,
        apply_to_existing: bool,
        enable_bypass: bool = False,
        enable_zoom: bool = False,
        enable_blur_bg: bool = False,
        target_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update task-level settings and optionally regenerate all clips."""
        await self.task_repo.update_task_settings(
            self.db,
            task_id,
            font_family,
            font_size,
            font_color,
            caption_template,
            include_broll,
            enable_bypass=enable_bypass,
            enable_zoom=enable_zoom,
            enable_blur_bg=enable_blur_bg,
            target_language=target_language,
        )

        if apply_to_existing:
            await self.regenerate_all_clips_for_task(
                task_id,
                font_family,
                font_size,
                font_color,
                caption_template,
                enable_bypass=enable_bypass,
                enable_zoom=enable_zoom,
                enable_blur_bg=enable_blur_bg,
                target_language=target_language,
            )

        return await self.get_task_with_clips(task_id) or {}

    async def regenerate_all_clips_for_task(
        self,
        task_id: str,
        font_family: str,
        font_size: int,
        font_color: str,
        caption_template: str,
        enable_bypass: bool = False,
        enable_zoom: bool = False,
        enable_blur_bg: bool = False,
        target_language: Optional[str] = None,
    ) -> None:
        """Regenerate all clips in a task using existing segment boundaries."""
        task = await self.task_repo.get_task_by_id(self.db, task_id)
        if not task:
            raise ValueError("Task not found")

        source_url = task.get("source_url")
        source_type = task.get("source_type")
        output_format = "vertical"
        add_subtitles = True

        # Preserve original output_format and add_subtitles from task creation (stored in Redis)
        redis_client = redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            decode_responses=True,
        )
        try:
            source_payload = await redis_client.get(f"task_source:{task_id}")
            if source_payload:
                parsed = json.loads(source_payload)
                of = parsed.get("output_format", output_format)
                if of in ("vertical", "original"):
                    output_format = of
                asub = parsed.get("add_subtitles", add_subtitles)
                if isinstance(asub, bool):
                    add_subtitles = asub
        finally:
            await redis_client.close()

        if not source_url or not source_type:
            raise ValueError("Task source URL is missing; cannot regenerate clips")

        clips = await self.clip_repo.get_clips_by_task(self.db, task_id)
        if not clips:
            return

        video_path: Path
        if source_type in ("youtube", "bilibili", "douyin"):
            downloaded = await self.video_service.download_video(source_url)
            if not downloaded:
                raise ValueError(
                    f"Failed to download source video ({source_type}) for regeneration"
                )
            video_path = Path(downloaded)
        else:
            video_path = self.video_service.resolve_local_video_path(source_url)
            if not video_path.exists():
                raise ValueError("Source video file no longer exists")

        segments = [
            {
                "start_time": clip["start_time"],
                "end_time": clip["end_time"],
                "text": clip.get("text") or "",
                "relevance_score": clip.get("relevance_score", 0.5),
                "reasoning": clip.get("reasoning")
                or "Regenerated with updated settings",
                "virality_score": clip.get("virality_score", 0),
                "hook_score": clip.get("hook_score", 0),
                "engagement_score": clip.get("engagement_score", 0),
                "value_score": clip.get("value_score", 0),
                "shareability_score": clip.get("shareability_score", 0),
                "hook_type": clip.get("hook_type"),
            }
            for clip in clips
        ]

        clips_info = await self.video_service.create_video_clips(
            video_path,
            segments,
            font_family,
            font_size,
            font_color,
            caption_template,
            output_format,
            add_subtitles,
            enable_bypass=enable_bypass,
            enable_zoom=enable_zoom,
            enable_blur_bg=enable_blur_bg,
            target_language=target_language,
        )

        await self.clip_repo.delete_clips_by_task(self.db, task_id)

        clip_ids = []
        for i, clip_info in enumerate(clips_info):
            clip_id = await self.clip_repo.create_clip(
                self.db,
                task_id=task_id,
                filename=clip_info["filename"],
                file_path=clip_info["path"],
                start_time=clip_info["start_time"],
                end_time=clip_info["end_time"],
                duration=clip_info["duration"],
                text=clip_info.get("text") or "",
                relevance_score=clip_info.get("relevance_score", 0.5),
                reasoning=clip_info.get("reasoning")
                or "Regenerated with updated settings",
                clip_order=i + 1,
                virality_score=clip_info.get("virality_score", 0),
                hook_score=clip_info.get("hook_score", 0),
                engagement_score=clip_info.get("engagement_score", 0),
                value_score=clip_info.get("value_score", 0),
                shareability_score=clip_info.get("shareability_score", 0),
                hook_type=clip_info.get("hook_type"),
                rank=clip_info.get("rank", "C"),
            )
            clip_ids.append(clip_id)

        await self.task_repo.update_task_clips(self.db, task_id, clip_ids)

    async def trim_clip(
        self,
        task_id: str,
        clip_id: str,
        start_offset: float,
        end_offset: float,
    ) -> Dict[str, Any]:
        clip = await self.clip_repo.get_clip_by_id(self.db, clip_id)
        if not clip or clip["task_id"] != task_id:
            raise ValueError("Clip not found")

        input_path = Path(clip["file_path"])
        if not input_path.exists():
            raise ValueError("Clip file not found")

        output_path = trim_clip_file(
            input_path, Path(self.config.temp_dir) / "clips", start_offset, end_offset
        )
        clip_duration = max(0.1, clip["duration"] - start_offset - end_offset)

        start_seconds = parse_timestamp_to_seconds(clip["start_time"]) + start_offset
        end_seconds = start_seconds + clip_duration

        new_start = self._seconds_to_mmss(start_seconds)
        new_end = self._seconds_to_mmss(end_seconds)

        await self.clip_repo.update_clip(
            self.db,
            clip_id,
            output_path.name,
            str(output_path),
            new_start,
            new_end,
            clip_duration,
            clip.get("text") or "",
        )
        return (await self.clip_repo.get_clip_by_id(self.db, clip_id)) or {}

    async def split_clip(
        self, task_id: str, clip_id: str, split_time: float
    ) -> Dict[str, Any]:
        clip = await self.clip_repo.get_clip_by_id(self.db, clip_id)
        if not clip or clip["task_id"] != task_id:
            raise ValueError("Clip not found")

        input_path = Path(clip["file_path"])
        if not input_path.exists():
            raise ValueError("Clip file not found")

        first_path, second_path = split_clip_file(
            input_path, Path(self.config.temp_dir) / "clips", split_time
        )

        start_seconds = parse_timestamp_to_seconds(clip["start_time"])
        clamped_split = max(0.2, min(split_time, float(clip["duration"]) - 0.2))
        split_abs = start_seconds + clamped_split
        end_seconds = parse_timestamp_to_seconds(clip["end_time"])

        await self.clip_repo.update_clip(
            self.db,
            clip_id,
            first_path.name,
            str(first_path),
            clip["start_time"],
            self._seconds_to_mmss(split_abs),
            clamped_split,
            clip.get("text") or "",
        )

        await self.clip_repo.create_clip(
            self.db,
            task_id=task_id,
            filename=second_path.name,
            file_path=str(second_path),
            start_time=self._seconds_to_mmss(split_abs),
            end_time=self._seconds_to_mmss(end_seconds),
            duration=max(0.1, end_seconds - split_abs),
            text=clip.get("text") or "",
            relevance_score=clip.get("relevance_score", 0.5),
            reasoning=clip.get("reasoning") or "Split from original clip",
            clip_order=clip.get("clip_order", 1) + 1,
            virality_score=clip.get("virality_score", 0),
            hook_score=clip.get("hook_score", 0),
            engagement_score=clip.get("engagement_score", 0),
            value_score=clip.get("value_score", 0),
            shareability_score=clip.get("shareability_score", 0),
            hook_type=clip.get("hook_type"),
        )

        await self.clip_repo.reorder_task_clips(self.db, task_id)
        return {"message": "Clip split successfully"}

    async def merge_clips(self, task_id: str, clip_ids: list[str]) -> Dict[str, Any]:
        if len(clip_ids) < 2:
            raise ValueError("At least two clips are required to merge")

        clips = []
        for clip_id in clip_ids:
            clip = await self.clip_repo.get_clip_by_id(self.db, clip_id)
            if not clip or clip["task_id"] != task_id:
                raise ValueError("One or more clips not found")
            clips.append(clip)

        ordered = sorted(clips, key=lambda c: c.get("clip_order", 0))
        merged_path = merge_clip_files(
            [Path(c["file_path"]) for c in ordered],
            Path(self.config.temp_dir) / "clips",
        )

        start_time = ordered[0]["start_time"]
        end_time = ordered[-1]["end_time"]
        duration = sum(float(c.get("duration", 0.0)) for c in ordered)
        text = " ".join((c.get("text") or "").strip() for c in ordered if c.get("text"))

        first = ordered[0]
        await self.clip_repo.update_clip(
            self.db,
            first["id"],
            merged_path.name,
            str(merged_path),
            start_time,
            end_time,
            duration,
            text,
        )

        for clip in ordered[1:]:
            await self.clip_repo.delete_clip(self.db, clip["id"])

        await self.clip_repo.reorder_task_clips(self.db, task_id)
        return {"message": "Clips merged successfully", "clip_id": first["id"]}

    async def update_clip_captions(
        self,
        task_id: str,
        clip_id: str,
        caption_text: str,
        position: str,
        highlight_words: list[str],
    ) -> Dict[str, Any]:
        clip = await self.clip_repo.get_clip_by_id(self.db, clip_id)
        if not clip or clip["task_id"] != task_id:
            raise ValueError("Clip not found")

        input_path = Path(clip["file_path"])
        if not input_path.exists():
            raise ValueError("Clip file not found")

        output_path = overlay_custom_captions(
            input_path,
            Path(self.config.temp_dir) / "clips",
            caption_text,
            position,
            highlight_words,
        )

        await self.clip_repo.update_clip(
            self.db,
            clip_id,
            output_path.name,
            str(output_path),
            clip["start_time"],
            clip["end_time"],
            clip["duration"],
            caption_text,
        )
        return (await self.clip_repo.get_clip_by_id(self.db, clip_id)) or {}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Return aggregate processing performance metrics."""
        return await self.task_repo.get_performance_metrics(self.db)

    @staticmethod
    def _seconds_to_mmss(seconds: float) -> str:
        total = max(0, int(round(seconds)))
        minutes = total // 60
        secs = total % 60
        return f"{minutes:02d}:{secs:02d}"

    async def _process_full_dubbing(
        self,
        task_id: str,
        url: str,
        source_type: str,
        narration_script: Optional[str] = None,
        tts_voice: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        should_cancel: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Process a full video dubbing task: download, TTS, mix, save as one clip.
        """
        import edge_tts
        from pathlib import Path
        
        try:
            logger.info(f"Starting FULL DUBBING for task {task_id}")
            
            # 1. Download
            if progress_callback:
                await progress_callback(10, "Downloading full source...")
            
            if source_type in ("youtube", "bilibili", "douyin"):
                video_path_str = await self.video_service.download_video(url)
                if not video_path_str:
                    raise ValueError("Failed to download video")
                video_path = Path(video_path_str)
            else:
                video_path = self.video_service.resolve_local_video_path(url)
                if not video_path.exists():
                    raise ValueError("Video file not found")

            # 2. Extract Narration Script
            # narration_script is passed as a JSON string from the worker and originally from frontend
            if not narration_script:
                if progress_callback:
                    await progress_callback(20, "Generating narration script...")
                # Fallback to AI if not provided (though it should be)
                transcript = await self.video_service.generate_transcript(video_path)
                from ..ai import get_smart_script_for_dubbing
                title = await self.video_service.get_video_title(url)
                segments = await get_smart_script_for_dubbing(transcript, title)
                full_text = "\n\n".join([s["localized_narration"] for s in segments])
            else:
                try:
                    # narration_script is JSON string containing list of segments
                    segments = json.loads(narration_script)
                    full_text = "\n\n".join([s["localized_narration"] for s in segments])
                except Exception as e:
                    logger.error(f"Failed to parse narration script: {e}")
                    full_text = narration_script # fallback to raw text if it's not JSON

            # 3. TTS Synthesis & Mixing (Strict Sync)
            if progress_callback:
                await progress_callback(40, "Synthesizing and syncing Vietnamese narration...")
            
            temp_clips_dir = video_path.parent / f"temp_{task_id}"
            temp_clips_dir.mkdir(parents=True, exist_ok=True)
            
            audio_filters = []
            inputs = [f"-i {video_path}"]
            
            # Parallel TTS synthesis
            import asyncio
            async def synth(i, text, start_ms):
                if not text.strip(): return None
                clip_tts_path = temp_clips_dir / f"seg_{i}.wav"
                voice = tts_voice or "vi-VN-NamMinhNeural"
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(clip_tts_path))
                return (i, clip_tts_path, start_ms)

            synth_tasks = [synth(i, s["localized_narration"], int(s["start_time"] * 1000)) for i, s in enumerate(segments)]
            results = await asyncio.gather(*synth_tasks)
            
            valid_idx = 0
            for res in results:
                if res:
                    i, clip_tts_path, start_ms = res
                    inputs.append(f"-i {clip_tts_path}")
                    audio_filters.append(f"[{valid_idx+1}:a]adelay={start_ms}|{start_ms}[a{valid_idx}]")
                    valid_idx += 1

            if not audio_filters:
                raise ValueError("No valid narration segments to mix")

            bg_vol = "0.2"
            mix_inputs = valid_idx + 1
            filter_str = "; ".join(audio_filters)
            amix_inputs = "".join([f"[a{j}]" for j in range(valid_idx)])
            
            filter_complex = (
                f"{filter_str}; "
                f"[0:a]volume={bg_vol}[bg]; "
                f"[bg]{amix_inputs}amix=inputs={mix_inputs}:duration=longest,volume={mix_inputs}[outa]"
            )

            # 4. Final Rendering
            if progress_callback:
                await progress_callback(70, "Rendering final dubbed video...")
            
            output_filename = f"final_dubbed_{task_id}.mp4"
            output_path = Path(self.config.temp_dir) / "clips" / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                "ffmpeg", "-v", "error"
            ]
            # Add all inputs
            for inp in inputs:
                cmd.extend(inp.split())
            
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "0:v", "-map", "[outa]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(output_path), "-y"
            ])
            
            import subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"FFmpeg mixing failed (Return code: {process.returncode}): {error_msg}")
                raise ValueError(f"FFmpeg mixing failed: {error_msg}")

            if not output_path.exists():
                raise ValueError("FFmpeg mixing failed; output file not created")

            # 5. Save as a single clip for the task
            if progress_callback:
                await progress_callback(90, "Finalizing task...")

            # Get video duration for metadata using cv2
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = count / fps if fps > 0 else 0
            cap.release()

            clip_id = await self.clip_repo.create_clip(
                self.db,
                task_id=task_id,
                filename=output_filename,
                file_path=str(output_path),
                start_time=0,
                end_time=duration,
                duration=duration,
                text=full_text[:500] + "...",
                relevance_score=1.0,
                reasoning="Full Video Dubbing version",
                clip_order=1
            )

            await self.task_repo.update_task_clips(self.db, task_id, [clip_id])
            await self.task_repo.update_task_status(
                self.db, task_id, "completed", progress=100, progress_message="Dubbing complete!"
            )

            return {
                "task_id": task_id,
                "clips_count": 1,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Full Dubbing Error for task {task_id}: {e}", exc_info=True)
            await self.task_repo.update_task_status(self.db, task_id, "error", progress_message=str(e))
            raise
