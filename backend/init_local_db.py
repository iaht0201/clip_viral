import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from src.database import Base
from src.models import User, Task, Source, GeneratedClip, ProcessingCache, WaitlistEntry

# Use the local SQLite DB path
DATABASE_URL = "sqlite+aiosqlite:///./supoclip.db"

async def init_db():
    print(f"Initializing database at {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")
    
    await engine.dispose()

if __name__ == "__main__":
    # Ensure we are in the backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(init_db())
