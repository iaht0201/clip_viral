"""
Video service - handles video processing business logic.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Awaitable
import logging
import json

from ..utils.async_helpers import run_in_thread
from ..video_utils import get_video_transcript, create_clips_with_transitions
from ..ai import get_most_relevant_parts_by_transcript
from ..video_download_utils import (
    download_video,
    get_video_title,
    get_video_id,
)
from ..config import Config

logger = logging.getLogger(__name__)
config = Config()
UPLOAD_URL_PREFIX = "upload://"


class VideoService:
    """Service for video processing operations."""

    @staticmethod
    def resolve_local_video_path(url: str) -> Path:
        """Resolve uploaded-video references without exposing server filesystem paths."""
        if url.startswith(UPLOAD_URL_PREFIX):
            filename = Path(url.removeprefix(UPLOAD_URL_PREFIX)).name
            return Path(config.temp_dir) / "uploads" / filename
        return Path(url)

    @staticmethod
    async def download_video(url: str) -> Optional[Path]:
        """
        Download a video asynchronously.
        Runs the sync download_video in a thread pool.
        """
        logger.info(f"Starting video download: {url}")
        video_path = await run_in_thread(download_video, url)

        if not video_path:
            logger.error(f"Failed to download video: {url}")
            return None

        logger.info(f"Video downloaded successfully: {video_path}")
        return video_path

    @staticmethod
    async def get_video_title(url: str) -> str:
        """
        Get video title asynchronously.
        Returns a default title if retrieval fails.
        """
        try:
            title = await run_in_thread(get_video_title, url)
            return title or "Video"
        except Exception as e:
            logger.warning(f"Failed to get video title: {e}")
            return "Video"

    @staticmethod
    async def generate_transcript(
        video_path: Path, processing_mode: str = "balanced"
    ) -> str:
        """
        Generate transcript from video using AssemblyAI.
        Runs in thread pool to avoid blocking.
        """
        logger.info(f"Generating transcript for: {video_path}")
        speech_model = "best"
        if processing_mode == "fast":
            speech_model = config.fast_mode_transcript_model

        transcript = await run_in_thread(get_video_transcript, video_path, speech_model)
        logger.info(f"Transcript generated: {len(transcript)} characters")
        return transcript

    @staticmethod
    async def analyze_transcript(transcript: str) -> Any:
        """
        Analyze transcript with AI to find relevant segments.
        This is already async, no need to wrap.
        """
        logger.info("Starting AI analysis of transcript")
        relevant_parts = await get_most_relevant_parts_by_transcript(transcript)
        logger.info(
            f"AI analysis complete: {len(relevant_parts.most_relevant_segments)} segments found"
        )
        return relevant_parts

    @staticmethod
    async def create_video_clips(
        video_path: Path,
        segments: List[Dict[str, Any]],
        font_family: str = "TikTokSans-Regular",
        font_size: int = 24,
        font_color: str = "#FFFFFF",
        caption_template: str = "default",
        output_format: str = "vertical",
        add_subtitles: bool = True,
        enable_bypass: bool = False,
        enable_zoom: bool = False,
        enable_blur_bg: bool = False,
        target_language: Optional[str] = None,
        tts_voice: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create video clips from segments with transitions and optional subtitles.
        Runs in thread pool as video processing is CPU-intensive.
        output_format: 'vertical' (9:16) or 'original' (keep source size, faster).
        add_subtitles: False skips subtitles; with original format uses ffmpeg stream copy (no re-encode).
        """
        logger.info(f"Creating {len(segments)} video clips subtitles={add_subtitles}")
        clips_output_dir = Path(config.temp_dir) / "clips"
        clips_output_dir.mkdir(parents=True, exist_ok=True)

        clips_info = await create_clips_with_transitions(
            video_path,
            segments,
            clips_output_dir,
            font_family,
            font_size,
            font_color,
            caption_template,
            output_format,
            add_subtitles,
            enable_bypass,
            enable_zoom,
            enable_blur_bg,
            target_language,
            tts_voice,
        )

        logger.info(f"Successfully created {len(clips_info)} clips")
        return clips_info

    @staticmethod
    def determine_source_type(url: str) -> str:
        """Determine platform: YouTube, Bilibili, Douyin, or generic url."""
        lower_url = url.lower()
        if "youtube.com" in lower_url or "youtu.be" in lower_url:
            return "youtube"
        if "bilibili.com" in lower_url or "b23.tv" in lower_url:
            return "bilibili"
        if "douyin.com" in lower_url:
            return "douyin"
        
        # Check if it has a video ID (validates as scrapable content)
        if get_video_id(url):
             return "video_url"
             
        return "video_url"

    @staticmethod
    async def process_video_complete(
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
        tts_voice: Optional[str] = None,
        task_mode: str = "clips",
        cached_transcript: Optional[str] = None,
        cached_analysis_json: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str, str], Awaitable[None]]] = None,
        should_cancel: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> Dict[str, Any]:
        """
        Complete video processing pipeline.
        Returns dict with segments and clips info.

        progress_callback: Optional function to call with progress updates
                          Signature: async def callback(progress: int, message: str, status: str)
        """
        try:
            # Step 1: Get video path (download or use existing)
            if should_cancel and await should_cancel():
                raise Exception("Task cancelled")

            if progress_callback:
                await progress_callback(10, "Downloading video...", "processing")

            if source_type in ("youtube", "bilibili", "douyin"):
                video_path = await VideoService.download_video(url)
                if not video_path:
                    raise Exception("Failed to download video")
            else:
                video_path = VideoService.resolve_local_video_path(url)
                if not video_path.exists():
                    raise Exception("Video file not found")

            # Early Exit: download_only
            if task_mode == "download_only":
                return {
                    "clips": [{"filename": video_path.name, "path": str(video_path), "start_time": "00:00", "end_time": "00:00", "duration": 0.0, "text": "", "relevance_score": 1.0, "reasoning": "Original download"}],
                    "transcript": "",
                    "summary": "Original video download",
                    "analysis_json": "{}"
                }

            # Early Exit: srt_only
            if task_mode == "srt_only":
                if progress_callback:
                    await progress_callback(40, "Generating transcript...", "processing")
                words = await VideoService.generate_transcript(video_path)
                from ..video_utils import transcript_to_srt
                srt_content = transcript_to_srt(words)
                
                srt_path = video_path.with_suffix(".srt")
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(srt_content)
                    
                return {
                    "clips": [{"filename": srt_path.name, "path": str(srt_path), "start_time": "00:00", "end_time": "00:00", "duration": 0.0, "text": srt_content[:500], "relevance_score": 1.0, "reasoning": "SRT Export"}],
                    "transcript": srt_content,
                    "summary": "SRT Generation",
                    "analysis_json": "{}"
                }

            # Step 2: Generate transcript
            if should_cancel and await should_cancel():
                raise Exception("Task cancelled")

            if progress_callback:
                await progress_callback(30, "Generating transcript...", "processing")

            transcript = cached_transcript
            if not transcript:
                transcript = await VideoService.generate_transcript(
                    video_path, processing_mode=processing_mode
                )

            # Early Exit: srt_only
            if task_mode == "srt_only":
                srt_path = video_path.with_suffix(".srt")
                # srt generator helper would go here, for now we return transcript as srt text
                return {
                    "clips": [{"filename": srt_path.name, "path": str(srt_path), "start_time": "00:00", "end_time": "00:00", "duration": 0.0, "text": transcript, "relevance_score": 1.0, "reasoning": "Generated SRT"}],
                    "transcript": transcript,
                    "summary": "SRT Export",
                    "analysis_json": "{}"
                }

            # Early Exit: dub_only
            if task_mode == "dub_only":
                mp3_path = video_path.with_suffix(".mp3")
                # Generate/synth script helpers... (simplified for now)
                return {
                    "clips": [{"filename": mp3_path.name, "path": str(mp3_path), "start_time": "00:00", "end_time": "00:00", "duration": 0.0, "text": "Audio Synthesis", "relevance_score": 1.0, "reasoning": "Narrative Synthesis"}],
                    "transcript": "",
                    "summary": "Audio Synthesis",
                    "analysis_json": "{}"
                }

            # Step 3: AI analysis
            if should_cancel and await should_cancel():
                raise Exception("Task cancelled")

            if progress_callback:
                await progress_callback(
                    50, "Analyzing content with AI...", "processing"
                )

            relevant_parts = None
            if cached_analysis_json:
                try:
                    cached_analysis = json.loads(cached_analysis_json)
                    segments = cached_analysis.get("most_relevant_segments", [])

                    class _SimpleResult:
                        def __init__(self, payload: Dict[str, Any]):
                            self.summary = payload.get("summary")
                            self.key_topics = payload.get("key_topics")
                            self.most_relevant_segments = payload.get(
                                "most_relevant_segments", []
                            )

                    relevant_parts = _SimpleResult(
                        {
                            "summary": cached_analysis.get("summary"),
                            "key_topics": cached_analysis.get("key_topics", []),
                            "most_relevant_segments": segments,
                        }
                    )
                except Exception:
                    relevant_parts = None

            if relevant_parts is None:
                relevant_parts = await VideoService.analyze_transcript(transcript)

            # Step 4: Create clips
            if should_cancel and await should_cancel():
                raise Exception("Task cancelled")

            if progress_callback:
                await progress_callback(70, "Creating video clips...", "processing")

            raw_segments = relevant_parts.most_relevant_segments
            segments_json: List[Dict[str, Any]] = []
            for segment in raw_segments:
                if isinstance(segment, dict):
                    segments_json.append(
                        {
                            "start_time": segment.get("start_time"),
                            "end_time": segment.get("end_time"),
                            "text": segment.get("text", ""),
                            "relevance_score": segment.get("relevance_score", 0.0),
                            "reasoning": segment.get("reasoning", ""),
                            "virality_score": segment.get("virality", {}).get("total_score", 0) if isinstance(segment.get("virality"), dict) else (segment.get("virality").total_score if hasattr(segment.get("virality"), "total_score") else 0),
                            "hook_score": segment.get("virality", {}).get("hook_score", 0) if isinstance(segment.get("virality"), dict) else (segment.get("virality").hook_score if hasattr(segment.get("virality"), "hook_score") else 0),
                            "engagement_score": segment.get("virality", {}).get("engagement_score", 0) if isinstance(segment.get("virality"), dict) else (segment.get("virality").engagement_score if hasattr(segment.get("virality"), "engagement_score") else 0),
                            "value_score": segment.get("virality", {}).get("value_score", 0) if isinstance(segment.get("virality"), dict) else (segment.get("virality").value_score if hasattr(segment.get("virality"), "value_score") else 0),
                            "shareability_score": segment.get("virality", {}).get("shareability_score", 0) if isinstance(segment.get("virality"), dict) else (segment.get("virality").shareability_score if hasattr(segment.get("virality"), "shareability_score") else 0),
                            "hook_type": segment.get("virality", {}).get("hook_type", "attention") if isinstance(segment.get("virality"), dict) else (segment.get("virality").hook_type if hasattr(segment.get("virality"), "hook_type") else "attention"),
                            "rank": segment.get("virality", {}).get("rank", "C") if isinstance(segment.get("virality"), dict) else (segment.get("virality").rank if hasattr(segment.get("virality"), "rank") else "C"),
                        }
                    )
                else:
                    segments_json.append(
                        {
                            "start_time": segment.start_time,
                            "end_time": segment.end_time,
                            "text": segment.text,
                            "relevance_score": segment.relevance_score,
                            "reasoning": segment.reasoning,
                            "virality_score": segment.virality.total_score if hasattr(segment, "virality") and segment.virality else 0,
                            "hook_score": segment.virality.hook_score if hasattr(segment, "virality") and segment.virality else 0,
                            "engagement_score": segment.virality.engagement_score if hasattr(segment, "virality") and segment.virality else 0,
                            "value_score": segment.virality.value_score if hasattr(segment, "virality") and segment.virality else 0,
                            "shareability_score": segment.virality.shareability_score if hasattr(segment, "virality") and segment.virality else 0,
                            "hook_type": segment.virality.hook_type if hasattr(segment, "virality") and segment.virality else "attention",
                            "rank": segment.virality.rank if hasattr(segment, "virality") and segment.virality else "C",
                        }
                    )

            if processing_mode == "fast":
                segments_json = segments_json[: config.fast_mode_max_clips]

            clips_info = await VideoService.create_video_clips(
                video_path,
                segments_json,
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
                tts_voice=tts_voice,
            )

            if progress_callback:
                await progress_callback(90, "Finalizing clips...", "processing")

            return {
                "segments": segments_json,
                "clips": clips_info,
                "summary": relevant_parts.summary if relevant_parts else None,
                "key_topics": relevant_parts.key_topics if relevant_parts else None,
                "transcript": transcript,
                "analysis_json": json.dumps(
                    {
                        "summary": relevant_parts.summary if relevant_parts else None,
                        "key_topics": relevant_parts.key_topics
                        if relevant_parts
                        else [],
                        "most_relevant_segments": segments_json,
                    }
                ),
            }

        except Exception as e:
            logger.error(f"Error in video processing pipeline: {e}")
            raise
