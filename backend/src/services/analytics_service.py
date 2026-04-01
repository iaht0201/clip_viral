import duckdb
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from ..config import Config

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for logging viral scores and content trends to DuckDB."""
    
    def __init__(self):
        self.config = Config()
        self.db_path = Path(self.config.temp_dir) / "analytics.duckdb"
        self._init_db()

    def _init_db(self):
        """Initialize the DuckDB table schema."""
        try:
            conn = duckdb.connect(str(self.db_path))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS viral_scores (
                    task_id VARCHAR,
                    clip_id VARCHAR,
                    timestamp TIMESTAMP,
                    source_type VARCHAR,
                    virality_score DOUBLE,
                    hook_score DOUBLE,
                    engagement_score DOUBLE,
                    value_score DOUBLE,
                    shareability_score DOUBLE,
                    hook_type VARCHAR,
                    text TEXT
                )
            """)
            conn.close()
            logger.info(f"DuckDB analytics initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDB: {e}")

    async def log_clip_scores(self, task_id: str, source_type: str, clips: List[Dict[str, Any]]):
        """Log virality scores for a batch of clips."""
        try:
            conn = duckdb.connect(str(self.db_path))
            now = datetime.utcnow()
            
            for clip in clips:
                conn.execute("""
                    INSERT INTO viral_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    clip.get("id", "unknown"),
                    now,
                    source_type,
                    clip.get("virality_score", 0),
                    clip.get("hook_score", 0),
                    clip.get("engagement_score", 0),
                    clip.get("value_score", 0),
                    clip.get("shareability_score", 0),
                    clip.get("hook_type", "none"),
                    clip.get("text", "")
                ))
            
            conn.close()
            logger.info(f"Logged {len(clips)} clips to DuckDB for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to log to DuckDB: {e}")

    async def get_trends(self) -> Dict[str, Any]:
        """Fetch basic trends from DuckDB."""
        try:
            conn = duckdb.connect(str(self.db_path))
            # Average scores over time
            df = conn.execute("""
                SELECT 
                    date_trunc('day', timestamp) as day,
                    avg(virality_score) as avg_virality,
                    count(*) as clip_count
                FROM viral_scores
                GROUP BY 1
                ORDER BY 1 DESC
                LIMIT 30
            """).df()
            conn.close()
            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Failed to fetch trends: {e}")
            return {}
