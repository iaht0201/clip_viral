import time
print("Importing config...")
from src.config import Config
print("Importing video_download_utils...")
try:
    from src.video_download_utils import *
except Exception as e:
    print(f"Error importing video_download_utils: {e}")
print("Importing video_utils...")
try:
    from src.video_utils import *
except Exception as e:
    print(f"Error importing video_utils: {e}")
print("Importing ai...")
try:
    from src.ai import *
except Exception as e:
    print(f"Error importing ai: {e}")
print("Finished imports.")
