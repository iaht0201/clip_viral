import pytest
from src.video_download_utils import get_video_id, VideoDownloader

def test_get_video_id_youtube():
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/shorts/dQw4w9WgXcQ"
    ]
    for url in urls:
        assert get_video_id(url) == "dQw4w9WgXcQ"

def test_get_video_id_bilibili():
    url = "https://www.bilibili.com/video/BV1uL4y1n7Lp"
    assert get_video_id(url) == "BV1uL4y1n7Lp"

def test_get_video_id_douyin():
    url = "https://www.douyin.com/video/7345678901234567890"
    assert get_video_id(url) == "7345678901234567890"

def test_invalid_url():
    # Valid HTTP but not supported platform should return a hash (11 chars)
    result = get_video_id("https://google.com")
    assert result is not None
    assert len(result) == 11
    
    # Actually invalid string
    assert get_video_id("not-a-url") == "not-a-url" # Heuristic for short strings
    assert get_video_id("") is None
