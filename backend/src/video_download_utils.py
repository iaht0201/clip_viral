"""
Utility functions for multi-platform video operations.
Optimized for high-quality downloads and better error handling for YouTube, Bilibili, Douyin, and others.
"""

import re
import hashlib
from urllib.parse import urlparse, parse_qs
import yt_dlp
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import time
import subprocess

from .config import Config

logger = logging.getLogger(__name__)
config = Config()


class VideoDownloader:
    """Enhanced multi-platform video downloader with optimized settings."""

    def __init__(self):
        self.temp_dir = Path(config.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_optimal_download_options(self, video_id: str, url: str = "") -> Dict[str, Any]:
        """Get optimal yt-dlp options for high-quality downloads across platforms."""
        referer = "https://www.youtube.com/"
        if url and "bilibili.com" in url.lower():
            referer = "https://www.bilibili.com/"
        elif url and "douyin.com" in url.lower():
            referer = "https://www.douyin.com/"

        return {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": f"{self.temp_dir}/%(id)s.%(ext)s",
            "merge_output_format": "mkv",
            "quiet": False,
            "no_warnings": False,
            "noplaylist": True,
            "overwrites": True,
            # Optimized for speed and reliability
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
            "concurrent_fragment_downloads": 5,
            "http_chunk_size": 10485760,
            # Enhanced headers to avoid 403 errors and region blocks
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Referer": referer,
            },
            # Common bypass for YouTube "Sign in to confirm you're not a bot"
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios", "web"],
                    "skip": ["dash", "hls"]
                }
            },
            "nocheckcertificate": True,
            "prefer_insecure": False,
            "age_limit": None,
        }


def _get_local_video_dimensions(path: Path) -> tuple[int, int]:
    """Return local video width/height using ffprobe."""
    try:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            str(path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if not output or "x" not in output:
            return (0, 0)
        width_str, height_str = output.split("x", 1)
        return (int(width_str), int(height_str))
    except Exception:
        return (0, 0)


def get_youtube_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID specifically."""
    if not isinstance(url, str) or not url.strip():
        return None

    url = url.strip()
    patterns = [
        r"(?:youtube\.com/(?:.*v=|v/|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"youtube\.com/v/([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            if len(video_id) == 11:
                return video_id

    # Check if it's already an ID (simple heuristic)
    if 8 <= len(url) <= 15 and "." not in url and "/" not in url:
        return url

    # Default if no patterns match
    return None

    try:
        parsed_url = urlparse(url)
        if "youtube.com" in parsed_url.netloc.lower():
            query = parse_qs(parsed_url.query)
            video_ids = query.get("v")
            if video_ids and len(video_ids[0]) == 11:
                return video_ids[0]
    except Exception:
        pass

    return None


def get_video_id(url: str) -> Optional[str]:
    """
    Generic video ID extractor supporting YouTube, Bilibili, Douyin, and others.
    """
    if not isinstance(url, str) or not url.strip():
        return None

    # YouTube check
    yt_id = get_youtube_video_id(url)
    if yt_id:
        return yt_id

    # Bilibili: /video/BV... or /video/av...
    bili_match = re.search(r"bilibili\.com/video/([A-Za-z0-9]+)", url, re.IGNORECASE)
    if bili_match:
        return bili_match.group(1)

    # Douyin: /video/123456789 or /note/123456789
    douyin_match = re.search(r"douyin\.com/(?:video|note)/(\d+)", url, re.IGNORECASE)
    if douyin_match:
        return douyin_match.group(1)

    # Fallback to hashed URL for other valid links
    if url.startswith(("http://", "https://")):
        return hashlib.md5(url.encode()).hexdigest()[:11]

    return None


def validate_video_url(url: str) -> bool:
    """Validate if URL is supported for scraping."""
    return get_video_id(url) is not None


def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive video information without downloading.
    Works for any platform supported by yt-dlp.
    """
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extractaudio": False,
            "skip_download": True,
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Referer": "https://www.youtube.com/" if "youtube.com" in url or "youtu.be" in url else "https://www.bilibili.com/",
            },
            "nocheckcertificate": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None

            return {
                "id": info.get("id"),
                "title": info.get("title", "Video"),
                "description": info.get("description", ""),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "upload_date": info.get("upload_date"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "thumbnail": info.get("thumbnail"),
                "format_id": info.get("format_id"),
                "resolution": info.get("resolution"),
                "fps": info.get("fps"),
                "filesize": info.get("filesize"),
                "extractor": info.get("extractor"),
            }

    except Exception as e:
        logger.error(f"Error extracting video info: {e}")
        return None


def get_video_title(url: str) -> Optional[str]:
    """Get the title of a video from a URL or local path."""
    if Path(url).exists():
        return Path(url).name
    video_info = get_video_info(url)
    return video_info.get("title") if video_info else None


def download_video(url: str, max_retries: int = 3) -> Optional[Path]:
    """
    Download video from any supported platform (YouTube, Bilibili, Douyin, etc.).
    Returns the path to the downloaded file, or None if download fails.
    """
    downloader = VideoDownloader()
    video_id = get_video_id(url)
    if not video_id:
        logger.error(f"Could not extract video ID or generate hash from: {url}")
        return None

    downloader = VideoDownloader()

    # SMART CACHE: Check if file already exists in temp
    for ext in [".mp4", ".mkv", ".webm"]:
        existing_file = downloader.temp_dir / f"{video_id}{ext}"
        if existing_file.exists() and existing_file.stat().st_size > 1024 * 1024:
            logger.info(f"Using cached video from temp: {existing_file}")
            return existing_file

    # Extract metadata first
    video_info = get_video_info(url)
    if not video_info:
        logger.error(f"Could not retrieve video information for: {url}")
        return None

    logger.info(f"Video: '{video_info.get('title')}' ({video_info.get('duration')}s) via {video_info.get('extractor')}")

    # Retry download with exponential backoff
    for attempt in range(max_retries):
        try:
            logger.info(f"Download attempt {attempt + 1}/{max_retries}")
            ydl_opts = downloader.get_optimal_download_options(video_id, url)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

                # Find the downloaded file
                downloaded_files = [
                    file_path
                    for file_path in Path(config.temp_dir).glob(f"{video_id}.*")
                    if file_path.is_file()
                    and file_path.suffix.lower() in [".mp4", ".mkv", ".webm"]
                ]
                if downloaded_files:
                    ranked_files = []
                    for candidate in downloaded_files:
                        width, height = _get_local_video_dimensions(candidate)
                        ranked_files.append((height, width, candidate.stat().st_size, candidate))
                    
                    ranked_files.sort(reverse=True)
                    best_file = ranked_files[0][3]
                    
                    logger.info(f"Download successful: {best_file.name} ({best_file.stat().st_size // 1024 // 1024}MB)")
                    return best_file

        except Exception as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
            else:
                logger.error(f"All download attempts failed for: {url}")

    return None


def get_video_duration(url: str) -> Optional[int]:
    """Get video duration in seconds without downloading."""
    video_info = get_video_info(url)
    return video_info.get("duration") if video_info else None


def cleanup_downloaded_files(video_id: str):
    """Clean up downloaded files for a specific video ID."""
    temp_dir = Path(config.temp_dir)
    for file_path in temp_dir.glob(f"{video_id}.*"):
        try:
            if file_path.is_file():
                file_path.unlink()
        except Exception:
            pass


# Backward compatibility aliases
def extract_video_id(url: str) -> Optional[str]:
    return get_video_id(url)

def download_youtube_video(url: str, max_retries: int = 3) -> Optional[Path]:
    return download_video(url, max_retries)

def get_youtube_video_title(url: str) -> Optional[str]:
    return get_video_title(url)
