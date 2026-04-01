
import sys
import os
import asyncio
import json
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# Mock
from unittest.mock import MagicMock
sys.modules["src.services.analytics_service"] = MagicMock()
sys.modules["src.services.webhook_service"] = MagicMock()
sys.modules["duckdb"] = MagicMock()

# Path
current_dir = os.getcwd()
sys.path.insert(0, os.path.join(current_dir, "src"))

async def analyze_local_video():
    from src.services.task_service import TaskService
    from src.services.video_service import VideoService
    
    video_path = "/mnt/sdb3/model/SaveTik.io_7620063040993529122_hd.mp4"
    if not os.path.exists(video_path):
        print(f"ERROR: {video_path} NOT FOUND")
        return

    service = TaskService(None)
    service.video_service = VideoService()
    
    try:
        result = await service.analyze_video_for_dubbing(video_path)
        print(f"\n--- RESULTS: {len(result['segments'])} segments ---")
        save_path = os.path.join(current_dir, "dubbing_preview_v2.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved to {save_path}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_local_video())
