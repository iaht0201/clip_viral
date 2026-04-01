import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./supoclip.db")

# Create async engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific options
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
    )
else:
    # PostgreSQL-specific options
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class for all models
class Base(DeclarativeBase):
    pass


# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Initialize database
async def init_db():
    from . import models  # Ensure all models are registered with Base.metadata
    async with engine.begin() as conn:
        # Optimization for SQLite: Enable WAL mode for better concurrency
        if DATABASE_URL.startswith("sqlite"):
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
            await conn.execute(text("PRAGMA cache_size=-64000"))  # 64MB cache
            await conn.execute(text("PRAGMA foreign_keys=ON"))

        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        migrations_dir = Path(__file__).parent / "migrations" / "sql"
        if migrations_dir.exists():
            files = sorted([p for p in migrations_dir.glob("*.sql") if p.is_file()])
            for migration_file in files:
                version = migration_file.name
                already_applied = await conn.execute(
                    text(
                        "SELECT 1 FROM schema_migrations WHERE version = :version LIMIT 1"
                    ),
                    {"version": version},
                )
                if already_applied.scalar() is not None:
                    continue

                sql = migration_file.read_text()
                # asyncpg doesn't support multiple statements in one execute(),
                # so split on semicolons and run each statement individually
                for statement in sql.split(";"):
                    statement = statement.strip()
                    if statement:
                        try:
                            await conn.execute(text(statement))
                        except Exception as e:
                            # If it's a "duplicate column" or "table already exists" error, we can ignore it
                            err_msg = str(e).lower()
                            if "already exists" in err_msg or "duplicate column" in err_msg:
                                logger.debug(f"Skipping already applied migration statement: {statement}")
                            else:
                                logger.error(f"Migration error in {version}: {e}")
                                raise
                await conn.execute(
                    text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                    {"version": version},
                )


# Close database connections
async def close_db():
    await engine.dispose()
