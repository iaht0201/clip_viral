import sys
import logging
from src.config import Config
from src.video_utils import get_video_transcript
from pathlib import Path

logging.basicConfig(level=logging.INFO)
print("Config loaded")
try:
    transcript = get_video_transcript(Path("uploads/vwM0Fg424bU.mp4"), "nano")
    print(transcript[:100])
except Exception as e:
    print("Error:", e)
