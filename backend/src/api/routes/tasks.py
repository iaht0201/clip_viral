"""
Task API routes using refactored architecture.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
import json
import logging
import json
import re
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from ...database import get_db, AsyncSessionLocal
from ...services.task_service import TaskService
from ...services.billing_service import BillingService, BillingLimitExceeded
from ...auth_headers import get_signed_user_id, USER_ID_HEADER
from ...workers.job_queue import JobQueue
from ...config import Config
import redis.asyncio as redis

logger = logging.getLogger(__name__)
config = Config()
router = APIRouter(prefix="/tasks", tags=["tasks"])


# --- Schemas ---

class VideoSource(BaseModel):
    url: str
    title: Optional[str] = None

class FontOptions(BaseModel):
    font_family: Optional[str] = "TikTokSans-Regular"
    font_size: Optional[int] = 24
    font_color: Optional[str] = "#FFFFFF"

class CreateTaskRequest(BaseModel):
    """Full request for Viral Clips generation"""
    source: VideoSource
    font_options: Optional[FontOptions] = Field(default_factory=FontOptions)
    caption_template: Optional[str] = "default"
    include_broll: Optional[bool] = False
    processing_mode: Optional[str] = "fast"
    output_format: Optional[str] = "vertical"
    add_subtitles: Optional[bool] = True
    enable_bypass: Optional[bool] = False
    enable_zoom: Optional[bool] = False
    enable_blur_bg: Optional[bool] = False
    target_language: Optional[str] = None
    tts_voice: Optional[str] = None
    task_mode: Optional[str] = "clips"
    narration_script: Optional[str] = None

class SimpleTaskRequest(BaseModel):
    """Simplified request for Download, SRT, or Hub"""
    url: str
    title: Optional[str] = None
    target_language: Optional[str] = "vi"
    tts_voice: Optional[str] = None
    task_mode: Optional[str] = "download_only"


def _normalize_font_size(value: Any, default: int = 24) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(12, min(72, parsed))


def _normalize_font_color(value: Any, default: str = "#FFFFFF") -> str:
    if isinstance(value, str) and re.match(r"^#[0-9A-Fa-f]{6}$", value):
        return value.upper()
    return default


def _normalize_font_family(value: Any, default: str = "TikTokSans-Regular") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _get_user_id_from_headers(request: Request) -> str:
    """Get user ID. Monetization on: signed auth. Off: user_id or x-supoclip-user-id or default."""
    if config.monetization_enabled:
        try:
            return get_signed_user_id(request, config)
        except Exception:
            pass
    
    # Local / Mock mode: fallback to local_user if none provided
    user_id = request.headers.get("user_id") or request.headers.get(USER_ID_HEADER)
    if not user_id and config.self_host:
         return "local_user"
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User-ID header is missing")
    return user_id


async def _require_task_owner(
    request: Request, task_service: TaskService, db: AsyncSession, task_id: str
):
    """Ensure authenticated user owns the task."""
    user_id = _get_user_id_from_headers(request)

    task = await task_service.task_repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this task")

    return task


@router.get("/")
async def list_tasks(
    request: Request, db: AsyncSession = Depends(get_db), limit: int = 50
):
    """
    Get all tasks for the authenticated user.
    """
    user_id = _get_user_id_from_headers(request)

    try:
        task_service = TaskService(db)
        tasks = await task_service.get_user_tasks(user_id, limit)

        return {"tasks": tasks, "total": len(tasks)}
    except Exception as e:
        logger.error(f"Error retrieving user tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tasks: {str(e)}")


async def _execute_task_creation(
    db: AsyncSession,
    user_id: str,
    url: str,
    title: Optional[str] = None,
    font_family: str = "TikTokSans-Regular",
    font_size: int = 24,
    font_color: str = "#FFFFFF",
    caption_template: str = "default",
    include_broll: bool = False,
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
) -> Dict[str, Any]:
    """Shared implementation for all task creation routes"""
    try:
        billing_service = BillingService(db)
        await billing_service.assert_can_create_task(user_id)

        task_service = TaskService(db)

        # Create task
        task_id = await task_service.create_task_with_source(
            user_id=user_id,
            url=url,
            title=title,
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

        # Get source type for worker
        source_type = task_service.video_service.determine_source_type(url)

        # Enqueue job for worker
        job_id = await JobQueue.enqueue_processing_job(
            "process_video_task",
            processing_mode,
            task_id,
            url,
            source_type,
            user_id,
            font_family,
            font_size,
            font_color,
            caption_template,
            processing_mode,
            output_format,
            add_subtitles,
            enable_bypass,
            enable_zoom,
            enable_blur_bg,
            target_language,
            task_mode=task_mode,
            narration_script=narration_script,
            tts_voice=tts_voice,
        )

        # Save source metadata in Redis
        redis_client = redis.Redis(
            host=config.redis_host, port=config.redis_port, decode_responses=True
        )
        try:
            await redis_client.set(
                f"task_source:{task_id}",
                json.dumps({
                    "url": url,
                    "source_type": source_type,
                    "output_format": output_format,
                    "add_subtitles": add_subtitles,
                    "tts_voice": tts_voice,
                    "enable_bypass": enable_bypass,
                    "enable_zoom": enable_zoom,
                    "enable_blur_bg": enable_blur_bg,
                    "target_language": target_language,
                }),
                ex=60 * 60 * 24 * 7,
            )
        finally:
            await redis_client.close()

        logger.info(f"Task {task_id} created and job {job_id} enqueued (Mode: {task_mode})")

        return {
            "task_id": task_id,
            "job_id": job_id,
            "message": f"Task created and queued for processing as {task_mode}",
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BillingLimitExceeded as e:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "SUBSCRIPTION_REQUIRED",
                "message": "Active subscription required to create tasks.",
                "billing": e.summary,
            },
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")


async def _require_task_owner(
    request: Request, task_service: TaskService, db: AsyncSession, task_id: str
):
    """Ensure authenticated user owns the task."""
    user_id = _get_user_id_from_headers(request)

    task = await task_service.task_repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this task")

    return task


@router.get("/")
async def list_tasks(
    request: Request, db: AsyncSession = Depends(get_db), limit: int = 50
):
    """
    Get all tasks for the authenticated user.
    """
    user_id = _get_user_id_from_headers(request)

    try:
        task_service = TaskService(db)
        tasks = await task_service.get_user_tasks(user_id, limit)

        return {"tasks": tasks, "total": len(tasks)}

    except Exception as e:
        logger.error(f"Error retrieving user tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tasks: {str(e)}")


@router.post("/create")
@router.post("/create/clips")
async def create_clips_task(
    data: CreateTaskRequest, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """Full Viral Clips task creation (Old /create is now mapped here)"""
    user_id = _get_user_id_from_headers(request)
    
    font_family = _normalize_font_family(data.font_options.font_family)
    font_size = _normalize_font_size(data.font_options.font_size)
    font_color = _normalize_font_color(data.font_options.font_color)
    
    return await _execute_task_creation(
        db=db,
        user_id=user_id,
        url=data.source.url,
        title=data.source.title,
        font_family=font_family,
        font_size=font_size,
        font_color=font_color,
        caption_template=data.caption_template,
        include_broll=data.include_broll,
        processing_mode=data.processing_mode,
        output_format=data.output_format,
        add_subtitles=data.add_subtitles,
        enable_bypass=data.enable_bypass,
        enable_zoom=data.enable_zoom,
        enable_blur_bg=data.enable_blur_bg,
        target_language=data.target_language,
        task_mode=data.task_mode or "clips",
        narration_script=data.narration_script,
        tts_voice=data.tts_voice,
    )


@router.post("/create/download")
async def create_download_task(
    data: SimpleTaskRequest, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """Just download the video"""
    user_id = _get_user_id_from_headers(request)
    return await _execute_task_creation(
        db=db,
        user_id=user_id,
        url=data.url,
        title=data.title,
        task_mode="download_only"
    )


@router.post("/create/srt")
async def create_srt_task(
    data: SimpleTaskRequest, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """Extract transcript and convert to SRT"""
    user_id = _get_user_id_from_headers(request)
    return await _execute_task_creation(
        db=db,
        user_id=user_id,
        url=data.url,
        title=data.title,
        target_language=data.target_language,
        task_mode="srt_only"
    )


@router.post("/create/dub")
async def create_dub_task(
    data: SimpleTaskRequest, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """Full video dubbing or audio-only synthesis"""
    user_id = _get_user_id_from_headers(request)
    mode = data.task_mode if data.task_mode in ("full_dubbing", "dub_only") else "full_dubbing"
    return await _execute_task_creation(
        db=db,
        user_id=user_id,
        url=data.url,
        title=data.title,
        tts_voice=data.tts_voice,
        target_language=data.target_language,
        task_mode=mode
    )


@router.post("/analyze")
async def analyze_task(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Download and Analyze video to return a script preview.
    Used for Full Dubbing workflow.
    """
    data = await request.json()
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
        
    try:
        task_service = TaskService(db)
        result = await task_service.analyze_video_for_dubbing(url)
        return result
    except Exception as e:
        logger.error(f"Error analyzing task: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing task: {str(e)}")


@router.get("/billing/summary")
async def get_billing_summary(request: Request, db: AsyncSession = Depends(get_db)):
    """Get monetization status and current usage for authenticated user."""
    user_id = _get_user_id_from_headers(request)

    try:
        billing_service = BillingService(db)
        summary = await billing_service.get_usage_summary(user_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving billing summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving billing summary: {str(e)}",
        )


@router.get("/{task_id}")
async def get_task(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Get task details."""
    try:
        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        task = await task_service.get_task_with_clips(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving task: {str(e)}")


@router.get("/{task_id}/transcript")
async def get_task_transcript(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Get detailed transcript for the editor."""
    from ...video_utils import load_cached_transcript_data
    from pathlib import Path
    
    try:
        task_service = TaskService(db)
        task = await _require_task_owner(request, task_service, db, task_id)
        
        # Get source to find the video file
        source = await task_service.source_repo.get_source_by_id(db, task["source_id"])
        if not source:
             raise HTTPException(status_code=404, detail="Source not found")
             
        video_path = Path(source["url"])
        if not video_path.exists():
            # Try to resolve upload path
            video_path = task_service.video_service.resolve_local_video_path(source["url"])
            
        transcript_data = load_cached_transcript_data(video_path)
        if not transcript_data:
             # Check if we have it in the temp directory based on video ID
             video_id = get_video_id(source["url"])
             video_path = Path(config.temp_dir) / f"{video_id}.mp4" # Assumption
             transcript_data = load_cached_transcript_data(video_path)
             
        if not transcript_data:
            raise HTTPException(status_code=404, detail="Transcript cache not found")
            
        return transcript_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving transcript: {str(e)}")


@router.get("/{task_id}/video")
async def get_task_video(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Serve the video/upload file for the editor."""
    try:
        task_service = TaskService(db)
        task = await _require_task_owner(request, task_service, db, task_id)
        
        source = await task_service.source_repo.get_source_by_id(db, task["source_id"])
        if not source:
             raise HTTPException(status_code=404, detail="Source not found")
             
        video_path = Path(source["url"])
        if not video_path.exists():
            video_path = task_service.video_service.resolve_local_video_path(source["url"])
            
        if not video_path.exists():
            # Check for YouTube download in temp
            from ..video_download_utils import get_video_id
            video_id = get_video_id(source["url"])
            if video_id:
                video_path = Path(config.temp_dir) / f"{video_id}.mp4"
                
        if not video_path.exists():
             raise HTTPException(status_code=404, detail="Video file not found")
             
        return FileResponse(
            path=video_path,
            media_type="video/mp4",
            filename=video_path.name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving video: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving video: {str(e)}")


@router.get("/{task_id}/clips")
async def get_task_clips(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Get all clips for a task."""
    try:
        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        task = await task_service.get_task_with_clips(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": task_id,
            "clips": task.get("clips", []),
            "total_clips": len(task.get("clips", [])),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving clips: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving clips: {str(e)}")


@router.get("/{task_id}/progress")
async def get_task_progress_sse(task_id: str, request: Request):
    """
    SSE endpoint for real-time progress updates.
    Streams progress updates as Server-Sent Events.
    """

    user_id = _get_user_id_from_headers(request)

    async with AsyncSessionLocal() as local_db:
        task_service = TaskService(local_db)
        task = await task_service.task_repo.get_task_by_id(local_db, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this task")

    async def event_generator():
        """Generate SSE events for task progress."""
        # Send initial task status
        yield {
            "event": "status",
            "data": json.dumps(
                {
                    "task_id": task_id,
                    "status": task.get("status"),
                    "progress": task.get("progress", 0),
                    "message": task.get("progress_message", ""),
                }
            ),
        }

        # If task is already completed or error, close connection
        if task.get("status") in ["completed", "error"]:
            yield {"event": "close", "data": json.dumps({"status": task.get("status")})}
            return

        # Connect to Redis for real-time updates
        redis_client = redis.Redis(
            host=config.redis_host, port=config.redis_port, decode_responses=True
        )

        try:
            # Subscribe to progress updates
            async for progress_data in ProgressTracker.subscribe_to_progress(
                redis_client, task_id
            ):
                yield {"event": "progress", "data": json.dumps(progress_data)}

                # Close connection if task is done
                if progress_data.get("status") in ["completed", "error"]:
                    yield {
                        "event": "close",
                        "data": json.dumps({"status": progress_data.get("status")}),
                    }
                    break

        finally:
            await redis_client.close()

    return EventSourceResponse(event_generator())


@router.patch("/{task_id}")
async def update_task(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Update task details (title)."""
    try:
        data = await request.json()
        title = data.get("title")

        if not title:
            raise HTTPException(status_code=400, detail="Title is required")

        task_service = TaskService(db)

        task = await _require_task_owner(request, task_service, db, task_id)

        # Update source title
        await task_service.source_repo.update_source_title(db, task["source_id"], title)

        return {"message": "Task updated successfully", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")


@router.delete("/{task_id}")
async def delete_task(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Delete a task and all its associated clips."""
    try:
        user_id = _get_user_id_from_headers(request)
        task_service = TaskService(db)

        # Get task to verify ownership
        task = await task_service.task_repo.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["user_id"] != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this task"
            )

        # Delete clips and task
        await task_service.delete_task(task_id)

        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")


@router.delete("/{task_id}/clips/{clip_id}")
async def delete_clip(
    task_id: str, clip_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Delete a specific clip."""
    try:
        user_id = _get_user_id_from_headers(request)
        task_service = TaskService(db)

        # Verify task ownership
        task = await task_service.task_repo.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["user_id"] != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this clip"
            )

        # Delete the clip
        await task_service.clip_repo.delete_clip(db, clip_id)

        return {"message": "Clip deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting clip: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting clip: {str(e)}")


@router.patch("/{task_id}/clips/{clip_id}")
async def trim_clip(
    task_id: str, clip_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Trim clip boundaries and regenerate clip file."""
    try:
        payload = await request.json()
        start_offset = float(payload.get("start_offset", 0))
        end_offset = float(payload.get("end_offset", 0))

        if start_offset < 0 or end_offset < 0:
            raise HTTPException(status_code=400, detail="Offsets must be non-negative")

        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        updated_clip = await task_service.trim_clip(
            task_id, clip_id, start_offset, end_offset
        )
        return {"clip": updated_clip}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error trimming clip: {e}")
        raise HTTPException(status_code=500, detail=f"Error trimming clip: {str(e)}")


@router.post("/{task_id}/clips/{clip_id}/split")
async def split_clip(
    task_id: str, clip_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Split a clip into two clips."""
    try:
        payload = await request.json()
        split_time = float(payload.get("split_time", 0))
        if split_time <= 0:
            raise HTTPException(
                status_code=400, detail="split_time must be greater than zero"
            )

        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        result = await task_service.split_clip(task_id, clip_id, split_time)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error splitting clip: {e}")
        raise HTTPException(status_code=500, detail=f"Error splitting clip: {str(e)}")


@router.post("/{task_id}/clips/merge")
async def merge_clips(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Merge multiple clips into one clip."""
    try:
        payload = await request.json()
        clip_ids = payload.get("clip_ids") or []
        if not isinstance(clip_ids, list):
            raise HTTPException(status_code=400, detail="clip_ids must be an array")

        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        result = await task_service.merge_clips(task_id, clip_ids)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging clips: {e}")
        raise HTTPException(status_code=500, detail=f"Error merging clips: {str(e)}")


@router.patch("/{task_id}/clips/{clip_id}/captions")
async def update_clip_captions(
    task_id: str, clip_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Update clip caption text, timing style and highlighted words."""
    try:
        payload = await request.json()
        caption_text = str(payload.get("caption_text", "")).strip()
        position = str(payload.get("position", "bottom"))
        highlight_words = payload.get("highlight_words") or []
        if not isinstance(highlight_words, list):
            raise HTTPException(
                status_code=400, detail="highlight_words must be an array"
            )

        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        updated_clip = await task_service.update_clip_captions(
            task_id,
            clip_id,
            caption_text,
            position,
            [str(word) for word in highlight_words],
        )
        return {"clip": updated_clip}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating captions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error updating captions: {str(e)}"
        )


@router.post("/{task_id}/clips/{clip_id}/regenerate")
async def regenerate_clip(
    task_id: str, clip_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Regenerate a single clip after editing timing values."""
    try:
        payload = await request.json()
        start_offset = float(payload.get("start_offset", 0))
        end_offset = float(payload.get("end_offset", 0))

        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        updated_clip = await task_service.trim_clip(
            task_id, clip_id, start_offset, end_offset
        )
        return {"clip": updated_clip, "message": "Clip regenerated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating clip: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error regenerating clip: {str(e)}"
        )


@router.post("/{task_id}/settings")
async def apply_task_settings(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Update task-level styling settings and optionally apply to all existing clips."""
    try:
        payload = await request.json()
        font_family = _normalize_font_family(
            payload.get("font_family", "TikTokSans-Regular")
        )
        font_size = _normalize_font_size(payload.get("font_size", 24))
        font_color = _normalize_font_color(payload.get("font_color", "#FFFFFF"))
        caption_template = payload.get("caption_template", "default")
        include_broll = bool(payload.get("include_broll", False))
        apply_to_existing = bool(payload.get("apply_to_existing", False))
        enable_bypass = bool(payload.get("enable_bypass", False))
        enable_zoom = bool(payload.get("enable_zoom", False))
        enable_blur_bg = bool(payload.get("enable_blur_bg", False))
        target_language = payload.get("target_language")

        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        task_record = await task_service.task_repo.get_task_by_id(db, task_id)
        if not task_record:
            raise HTTPException(status_code=404, detail="Task not found")
        if not is_font_accessible(font_family, task_record["user_id"]):
            raise HTTPException(
                status_code=400, detail="Selected font is not available"
            )
        task = await task_service.update_task_settings(
            task_id,
            font_family,
            font_size,
            font_color,
            caption_template,
            include_broll,
            apply_to_existing,
            enable_bypass=enable_bypass,
            enable_zoom=enable_zoom,
            enable_blur_bg=enable_blur_bg,
            target_language=target_language,
        )
        return {"task": task, "message": "Task settings updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error updating task settings: {str(e)}"
        )


@router.get("/{task_id}/clips/{clip_id}/export")
async def export_clip(
    task_id: str,
    clip_id: str,
    request: Request,
    preset: str = "tiktok",
    db: AsyncSession = Depends(get_db),
):
    """Export clip with a social platform preset."""
    try:
        preset_name = preset.lower().strip()
        if preset_name not in EXPORT_PRESETS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid preset. Use one of: {', '.join(EXPORT_PRESETS.keys())}",
            )

        task_service = TaskService(db)
        await _require_task_owner(request, task_service, db, task_id)
        clip = await task_service.clip_repo.get_clip_by_id(db, clip_id)
        if not clip or clip.get("task_id") != task_id:
            raise HTTPException(status_code=404, detail="Clip not found")

        from pathlib import Path

        output_path = export_with_preset(
            Path(clip["file_path"]),
            Path(config.temp_dir) / "exports",
            preset_name,
        )

        download_name = f"{Path(clip['filename']).stem}_{preset_name}.mp4"
        return FileResponse(
            path=str(output_path), media_type="video/mp4", filename=download_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting clip: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting clip: {str(e)}")


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Cancel an active queued or processing task."""
    try:
        task_service = TaskService(db)
        task = await _require_task_owner(request, task_service, db, task_id)

        if task.get("status") in ["completed", "error", "cancelled"]:
            return {"message": f"Task already in terminal state: {task.get('status')}"}

        redis_client = redis.Redis(
            host=config.redis_host, port=config.redis_port, decode_responses=True
        )
        try:
            await redis_client.setex(f"task_cancel:{task_id}", 3600, "1")
        finally:
            await redis_client.close()

        await task_service.task_repo.update_task_status(
            db,
            task_id,
            "cancelled",
            progress=0,
            progress_message="Cancelled by user",
        )

        return {"message": "Task cancellation requested"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(e)}")


@router.get("/metrics/performance")
async def get_performance_metrics(db: AsyncSession = Depends(get_db)):
    """Get aggregate processing performance metrics by mode."""
    try:
        task_service = TaskService(db)
        return await task_service.get_performance_metrics()
    except Exception as e:
        logger.error(f"Error loading performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading metrics: {str(e)}")


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Resume a cancelled or errored task by enqueueing a new worker job."""
    try:
        task_service = TaskService(db)
        task = await _require_task_owner(request, task_service, db, task_id)

        if task.get("status") not in ["cancelled", "error", "queued"]:
            raise HTTPException(
                status_code=400,
                detail="Only cancelled/error/queued tasks can be resumed",
            )

        source_url = task.get("source_url")
        source_type = task.get("source_type")
        output_format = "vertical"
        add_subtitles = True
        enable_bypass = task.get("enable_bypass", False)
        enable_zoom = task.get("enable_zoom", False)
        enable_blur_bg = task.get("enable_blur_bg", False)
        target_language = task.get("target_language")

        redis_client = redis.Redis(
            host=config.redis_host, port=config.redis_port, decode_responses=True
        )
        try:
            source_payload = await redis_client.get(f"task_source:{task_id}")
            if source_payload:
                parsed = json.loads(source_payload)
                if not source_url:
                    source_url = parsed.get("url")
                if not source_type:
                    source_type = parsed.get("source_type")
                of = parsed.get("output_format", output_format)
                if of in ("vertical", "original"):
                    output_format = of
                asub = parsed.get("add_subtitles", add_subtitles)
                if isinstance(asub, bool):
                    add_subtitles = asub
                
                enable_bypass = parsed.get("enable_bypass", task.get("enable_bypass", False))
                enable_zoom = parsed.get("enable_zoom", task.get("enable_zoom", False))
                enable_blur_bg = parsed.get("enable_blur_bg", task.get("enable_blur_bg", False))
                target_language = parsed.get("target_language", task.get("target_language"))
        finally:
            await redis_client.close()

        if not source_url or not source_type:
            raise HTTPException(status_code=400, detail="Task source URL is missing")

        redis_client = redis.Redis(
            host=config.redis_host, port=config.redis_port, decode_responses=True
        )
        try:
            await redis_client.delete(f"task_cancel:{task_id}")
        finally:
            await redis_client.close()

        await task_service.task_repo.update_task_status(
            db,
            task_id,
            "queued",
            progress=0,
            progress_message="Re-queued by user",
        )

        processing_mode = task.get("processing_mode") or config.default_processing_mode

        job_id = await JobQueue.enqueue_processing_job(
            "process_video_task",
            processing_mode,
            task_id,
            source_url,
            source_type,
            task["user_id"],
            task.get("font_family") or "TikTokSans-Regular",
            task.get("font_size") or 24,
            task.get("font_color") or "#FFFFFF",
            task.get("caption_template") or "default",
            processing_mode,
            output_format,
            add_subtitles,
            enable_bypass,
            enable_zoom,
            enable_blur_bg,
            target_language,
        )

        return {"message": "Task resumed", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming task: {e}")
        raise HTTPException(status_code=500, detail=f"Error resuming task: {str(e)}")


@router.get("/dead-letter/list")
async def list_dead_letter_tasks():
    """List tasks that exhausted retries and landed in dead-letter store."""
    redis_client = redis.Redis(
        host=config.redis_host, port=config.redis_port, decode_responses=True
    )
    try:
        ids_result = redis_client.smembers("tasks:dead_letter")
        ids = await ids_result if inspect.isawaitable(ids_result) else ids_result
        items = []
        safe_ids = list(ids or [])
        for task_id in sorted(safe_ids):
            payload = await redis_client.get(f"dead_letter:{task_id}")
            if payload:
                try:
                    items.append(json.loads(payload))
                except json.JSONDecodeError:
                    items.append({"task_id": task_id, "raw": payload})

        return {"total": len(items), "tasks": items}
    finally:
        await redis_client.close()
