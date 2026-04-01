import sys
import logging
import asyncio
from pathlib import Path
from src.video_utils import get_video_transcript

logging.basicConfig(level=logging.DEBUG)

def main():
    print("Script started")
    try:
        transcript = get_video_transcript(Path("/app/uploads/vwM0Fg424bU.mp4"), "nano")
        print("Success:", transcript[:100])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
