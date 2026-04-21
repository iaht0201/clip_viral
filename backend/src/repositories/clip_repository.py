"""
Clip repository - handles all database operations for generated clips.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sa_text
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)


def safe_isoformat(dt):
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    try:
        return dt.isoformat()
    except AttributeError:
        return str(dt)


class ClipRepository:
    """Repository for clip-related database operations."""

    @staticmethod
    async def create_clip(
        db: AsyncSession,
        task_id: str,
        filename: str,
        file_path: str,
        start_time: str,
        end_time: str,
        duration: float,
        text: str,
        relevance_score: float,
        reasoning: str,
        clip_order: int,
        virality_score: int = 0,
        hook_score: int = 0,
        engagement_score: int = 0,
        value_score: int = 0,
        shareability_score: int = 0,
        hook_type: Optional[str] = None,
        rank: str = "C",
    ) -> str:
        """Create a new clip record and return its ID."""
        from ..models import GeneratedClip
        
        clip = GeneratedClip(
            task_id=task_id,
            filename=filename,
            file_path=file_path,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            text=text,
            relevance_score=relevance_score,
            reasoning=reasoning,
            clip_order=clip_order,
            virality_score=virality_score,
            hook_score=hook_score,
            engagement_score=engagement_score,
            value_score=value_score,
            shareability_score=shareability_score,
            hook_type=hook_type,
            rank=rank
        )
        
        try:
            db.add(clip)
            await db.commit()
            await db.refresh(clip)
            clip_id = clip.id
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating clip: {e}")
            # Fallback for simpler creation
            clip = GeneratedClip(
                task_id=task_id,
                filename=filename,
                file_path=file_path,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                relevance_score=relevance_score,
                clip_order=clip_order
            )
            db.add(clip)
            await db.commit()
            await db.refresh(clip)
            clip_id = clip.id
            
        logger.debug(f"Created clip {clip_id} for task {task_id}")
        return str(clip_id)

    @staticmethod
    async def get_clips_by_task(db: AsyncSession, task_id: str) -> List[Dict[str, Any]]:
        """Get all clips for a specific task, ordered by clip_order."""
        try:
            result = await db.execute(
                sa_text("""
                    SELECT id, filename, file_path, start_time, end_time, duration,
                           text, relevance_score, reasoning, clip_order, created_at,
                           virality_score, hook_score, engagement_score, value_score, shareability_score, hook_type, rank
                    FROM generated_clips
                    WHERE task_id = :task_id
                    ORDER BY clip_order ASC
                """),
                {"task_id": task_id},
            )
        except Exception:
            await db.rollback()
            result = await db.execute(
                sa_text("""
                    SELECT id, filename, file_path, start_time, end_time, duration,
                           text, relevance_score, reasoning, clip_order, created_at
                    FROM generated_clips
                    WHERE task_id = :task_id
                    ORDER BY clip_order ASC
                """),
                {"task_id": task_id},
            )

        clips = []
        for row in result.fetchall():
            clips.append(
                {
                    "id": row.id,
                    "filename": row.filename,
                    "file_path": row.file_path,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                    "duration": row.duration,
                    "text": row.text,
                    "relevance_score": row.relevance_score,
                    "reasoning": row.reasoning,
                    "clip_order": row.clip_order,
                    "created_at": safe_isoformat(row.created_at),
                    "video_url": f"/clips/{row.file_path.removeprefix('temp/').removeprefix('temp') if hasattr(row, 'file_path') else f'clips/{row.filename}'}",
                    "virality_score": row.virality_score or 0,
                    "hook_score": row.hook_score or 0,
                    "engagement_score": row.engagement_score or 0,
                    "value_score": row.value_score or 0,
                    "shareability_score": row.shareability_score or 0,
                    "hook_type": row.hook_type,
                    "rank": getattr(row, "rank", "C"),
                }
            )

        return clips

    @staticmethod
    async def get_clips_count(db: AsyncSession, task_id: str) -> int:
        """Get the count of clips for a task."""
        result = await db.execute(
            sa_text(
                "SELECT COUNT(*) as count FROM generated_clips WHERE task_id = :task_id"
            ),
            {"task_id": task_id},
        )
        return result.scalar()

    @staticmethod
    async def delete_clips_by_task(db: AsyncSession, task_id: str) -> int:
        """Delete all clips for a task. Returns count of deleted clips."""
        result = await db.execute(
            sa_text("DELETE FROM generated_clips WHERE task_id = :task_id"),
            {"task_id": task_id},
        )
        await db.commit()
        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} clips for task {task_id}")
        return deleted_count

    @staticmethod
    async def delete_clip(db: AsyncSession, clip_id: str) -> None:
        """Delete a single clip by ID."""
        await db.execute(
            sa_text("DELETE FROM generated_clips WHERE id = :clip_id"),
            {"clip_id": clip_id},
        )
        await db.commit()
        logger.info(f"Deleted clip {clip_id}")

    @staticmethod
    async def get_clip_by_id(
        db: AsyncSession, clip_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get one clip by ID."""
        try:
            result = await db.execute(
                sa_text(
                    """
                    SELECT id, task_id, filename, file_path, start_time, end_time, duration,
                           text, relevance_score, reasoning, clip_order,
                           virality_score, hook_score, engagement_score, value_score, shareability_score, hook_type, rank,
                           created_at
                    FROM generated_clips
                    WHERE id = :clip_id
                    """
                ),
                {"clip_id": clip_id},
            )
        except Exception:
            await db.rollback()
            result = await db.execute(
                sa_text(
                    """
                    SELECT id, task_id, filename, file_path, start_time, end_time, duration,
                           text, relevance_score, reasoning, clip_order, created_at
                    FROM generated_clips
                    WHERE id = :clip_id
                    """
                ),
                {"clip_id": clip_id},
            )
        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row.id,
            "task_id": row.task_id,
            "filename": row.filename,
            "file_path": row.file_path,
            "start_time": row.start_time,
            "end_time": row.end_time,
            "duration": row.duration,
            "text": row.text,
            "relevance_score": row.relevance_score,
            "reasoning": row.reasoning,
            "clip_order": row.clip_order,
            "virality_score": row.virality_score or 0,
            "hook_score": row.hook_score or 0,
            "engagement_score": row.engagement_score or 0,
            "value_score": row.value_score or 0,
            "shareability_score": row.shareability_score or 0,
            "hook_type": row.hook_type,
            "rank": getattr(row, "rank", "C"),
            "created_at": safe_isoformat(row.created_at),
            "video_url": f"/clips/{row.file_path.removeprefix('temp/').removeprefix('temp')}",
        }

    @staticmethod
    async def update_clip(
        db: AsyncSession,
        clip_id: str,
        filename: str,
        file_path: str,
        start_time: str,
        end_time: str,
        duration: float,
        text: str,
    ) -> None:
        """Update core clip metadata and file path."""
        await db.execute(
            sa_text(
                """
                UPDATE generated_clips
                SET filename = :filename,
                    file_path = :file_path,
                    start_time = :start_time,
                    end_time = :end_time,
                    duration = :duration,
                    text = :text,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :clip_id
                """
            ),
            {
                "clip_id": clip_id,
                "filename": filename,
                "file_path": file_path,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "text": text,
            },
        )
        await db.commit()

    @staticmethod
    async def reorder_task_clips(db: AsyncSession, task_id: str) -> None:
        """Normalize clip_order sequence after edits."""
        result = await db.execute(
            sa_text(
                "SELECT id FROM generated_clips WHERE task_id = :task_id ORDER BY clip_order ASC, created_at ASC"
            ),
            {"task_id": task_id},
        )
        clip_ids = [row.id for row in result.fetchall()]
        for idx, cid in enumerate(clip_ids, start=1):
            await db.execute(
                sa_text(
                    "UPDATE generated_clips SET clip_order = :clip_order, updated_at = CURRENT_TIMESTAMP WHERE id = :clip_id"
                ),
                {"clip_order": idx, "clip_id": cid},
            )
        await db.commit()
