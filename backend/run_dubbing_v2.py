
import os
import time
if "DATABASE_URL" not in os.environ or "prisma" in os.environ.get("DATABASE_URL", ""):
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./supoclip.db"

import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

# Add src to path
current_dir = os.getcwd()
sys.path.insert(0, os.path.join(current_dir, "src"))

# Mock
sys.modules["src.services.analytics_service"] = MagicMock()
sys.modules["src.services.webhook_service"] = MagicMock()
sys.modules["duckdb"] = MagicMock()

from src.services.task_service import TaskService
from src.database import AsyncSessionLocal, Base, engine

async def process_full_dubbing_v2():
    # Sync DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    video_path = "/mnt/sdb3/model/SaveTik.io_7620063040993529122_hd.mp4"
    preview_v2_path = os.path.join(current_dir, "dubbing_preview_v2.json")
    
    with open(preview_v2_path, "r") as f:
        preview_data = json.load(f)
    
    segments = preview_data["segments"]
    # Join into a single large block for edge-tts (as the current TaskService._process_full_dubbing does)
    # Actually, TaskService._process_full_dubbing joins segments with \n\n
    narration_script = json.dumps(segments)
    
    async with AsyncSessionLocal() as db:
        service = TaskService(db)
        service.analytics = MagicMock()
        service.webhooks = MagicMock()
        
        task_id = "task_v2_" + str(int(time.time()))
        print(f"TASK ID: {task_id}")
        
        try:
            async def progress(p, msg): print(f"[{p}%] {msg}")
            
            # Start dubbing
            result = await service._process_full_dubbing(
                task_id=task_id,
                url=video_path,
                source_type="local",
                narration_script=narration_script,
                progress_callback=progress
            )
            
            print("\n--- DUBBING V2 COMPLETE ---")
            output_filename = f"final_dubbed_{task_id}.mp4"
            output_path = os.path.join(current_dir, "temp", "clips", output_filename)
            print(f"Final Video path: {output_path}")
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(process_full_dubbing_v2())
