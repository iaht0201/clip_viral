"""
Source repository - handles all database operations for video sources.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any  # Dict/Any kept for return type hints
import logging

logger = logging.getLogger(__name__)


class SourceRepository:
    """Repository for source-related database operations."""

    @staticmethod
    async def create_source(
        db: AsyncSession, source_type: str, title: str, url: Optional[str] = None
    ) -> str:
        """Create a new source record and return its ID."""
        from ..models import Source
        
        source = Source(
            type=source_type,
            title=title,
            url=url
        )
        
        try:
            db.add(source)
            await db.commit()
            await db.refresh(source)
            source_id = source.id
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating source: {e}")
            # Fallback for simpler creation if needed, though Source model usually requires all of these
            source = Source(
                type=source_type,
                title=title
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
            source_id = source.id

        logger.info(f"Created source {source_id}: {title} ({source_type})")
        return str(source_id)

    @staticmethod
    async def get_source_by_id(
        db: AsyncSession, source_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get source by ID."""
        result = await db.execute(
            text("SELECT * FROM sources WHERE id = :source_id"),
            {"source_id": source_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": row.id,
            "type": row.type,
            "title": row.title,
            "url": getattr(row, "url", None),
            "created_at": row.created_at,
        }

    @staticmethod
    async def update_source_title(db: AsyncSession, source_id: str, title: str) -> None:
        """Update the title of a source."""
        await db.execute(
            text("UPDATE sources SET title = :title WHERE id = :source_id"),
            {"title": title, "source_id": source_id},
        )
        await db.commit()
        logger.info(f"Updated source {source_id} title to: {title}")
