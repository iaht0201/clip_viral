
import asyncio
import os
import sys
import json
from pathlib import Path

# Set project root
current_dir = Path(__file__).parent
backend_src = current_dir / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

from src.services.task_service import TaskService
from src.database import AsyncSessionLocal

async def analyze_local_video():
    video_path = "/mnt/sdb3/model/SaveTik.io_7620063040993529122_hd.mp4"
    
    async with AsyncSessionLocal() as db:
        service = TaskService(db)
        print(f"Analyzing: {video_path}...")
        try:
            result = await service.analyze_video_for_dubbing(video_path)
            print("\n--- RESULTS ---")
            print(f"Title: {result['title']}")
            print(f"Segments Count: {len(result['segments'])}")
            
            # Show segments
            for i, seg in enumerate(result['segments']):
                print(f"\n[Segment {i+1}] {seg['start_time']} - {seg['end_time']}")
                print(f"Orig: {seg['original_text']}")
                print(f"Dub: {seg['localized_narration']}")
                
            # Save for inspection
            with open("/tmp/dubbing_analysis_result.json", "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("\nDetailed results saved to /tmp/dubbing_analysis_result.json")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_local_video())
