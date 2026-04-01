
import os
import sys
import asyncio
import logging
from pathlib import Path
import json

# Add src to path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.video_download_utils import download_video, get_video_title
from src.video_utils import get_video_transcript
from src.ai import translate_text, get_most_relevant_parts_by_transcript
from src.tts import generate_tts
from src.config import Config
from src.rvc_utils import apply_voice_conversion

# We need MoviePy v2 based on the codebase
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, vfx, afx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def rewrite_to_smart_script(transcript: str) -> str:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # 3.1: Analysis
    print("  Analyzing video theme...")
    analysis_prompt = f"Phân tích transcript sau: xác định chủ đề và phong cách. Transcript: {transcript[:1000]}. Trả về nội dung định hướng ngắn: 'Đây là video [chủ đề], phong cách [phong cách].'"
    try:
        analysis_completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        video_context = analysis_completion.choices[0].message.content.strip()
        print(f"  Detected: {video_context}")
    except:
        video_context = "Video nội dung tổng hợp, phong cách hào hứng."

    # 3.2: Rewrite
    prompt = f"""
    Bối cảnh video: {video_context}
    Dựa trên transcript video dưới đây, hãy viết lại thành một script thuyết minh video hấp dẫn, năng động, hào hứng.
    Quy tắc:
    1. PHONG CÁCH: Điều chỉnh linh hoạt theo bối cảnh (Ví dụ: Review công nghệ thì chuyên nghiệp, review đồ ăn thì hấp dẫn vị giác, tin tức thì súc tích).
    2. CẤU TRÚC: Hook mạnh ở đầu, dẫn dắt lôi cuốn, kết luận gọn gàng.
    3. ĐỘ DÀI: Súc tích (khoảng 150-250 từ).
    4. NGÔN NGỮ: Tiếng Việt tự nhiên, phù hợp với đối tượng khán giả xem loại video này.
    5. Chỉ trả về nội dung script, không thêm bất kỳ ghi chú nào khác.

    TRANSCRIPT:
    {transcript}
    """
    
    try:
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are a professional Vietnamese scriptwriter for viral videos."}, 
                      {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Rewriting failed: {e}")
        return transcript # Fallback

async def process_workflow(url: str):
    print(f"STARTING WORKFLOW for {url}")
    config = Config()
    
    # 1. Download or Use Local
    if os.path.exists(url) and os.path.isfile(url):
        print(f"Using local file: {url}")
        logger.info(f"Step 1: Using local video {url}")
        video_path = Path(url)
    else:
        print(f"Downloading URL: {url}")
        logger.info(f"Step 1: Downloading {url}")
        video_path = download_video(url)
        if not video_path:
            logger.error("Download failed")
            return
    
    print(f"Video path: {video_path}")

    # 2. Transcription
    logger.info(f"Step 2: Transcribing video {video_path}")
    transcript_cache = video_path.with_suffix(".transcript_cache.json")
    if transcript_cache.exists():
        with open(transcript_cache, "r") as f:
            transcript_data = json.load(f)
            transcript = transcript_data.get("text", "")
    else:
        transcript = get_video_transcript(video_path)

    # 3. Rewrite Style
    logger.info("Step 3: Rewriting to Smart Script style")
    review_script = await rewrite_to_smart_script(transcript)
    logger.info(f"REWRITTEN SCRIPT:\n{review_script}")

    # 4. Generate TTS with Den Voice (MeloTTS + RVC)
    logger.info("Step 4: Generating Den Voice (Melo + RVC)")
    tts_output = video_path.parent / f"den_review_{video_path.stem}.wav"
    # generate_tts already handles persona="den" applying RVC
    await generate_tts(review_script, "vietnamese", tts_output, persona="den")
    
    if not tts_output.exists():
         logger.error("TTS generation failed")
         return

    # 5. Assembly (Mix + Ducking)
    logger.info("Step 5: Blending audio and rendering video")
    video = VideoFileClip(str(video_path))
    
    # Ducking original audio (others voice down)
    bg_audio = video.audio.with_effects([afx.MultiplyVolume(0.15)])
    
    # Den voice (up)
    den_audio = AudioFileClip(str(tts_output))
    
    # If Den voice is longer than video, speed up video or slow down Den voice (pitch change though)
    # Let's adjust video speed to match Den voice if Den voice is longer
    if den_audio.duration > video.duration:
        speed_factor = video.duration / den_audio.duration
        # To avoid extreme slowness, we cap it or just extend video?
        # Better: loop end of video or just speed up 1.1x?
        # For simplicity, we just match duration
        den_audio = den_audio.subclipped(0, video.duration)
        logger.warning(f"Den voice ({den_audio.duration}s) longer than video ({video.duration}s). Clipping Den voice.")
    
    # Position Den voice at the start
    final_audio = CompositeAudioClip([bg_audio, den_audio.with_start(0)])
    final_video = video.with_audio(final_audio)
    
    # Output file
    final_output = video_path.parent / f"den_review_final_{video_path.stem}.mp4"
    
    # Use quality settings from VideoProcessor
    logger.info(f"Rendering final video to: {final_output}")
    await asyncio.to_thread(
        final_video.write_videofile,
        str(final_output),
        codec="libx264",
        audio_codec="aac",
        threads=2, # RAM safety
        preset="fast",
        fps=video.fps or 30
    )
    
    logger.info(f"WORKFLOW COMPLETE! Result: {final_output}")
    print(f"DONE: {final_output}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.bilibili.com/video/BV1xZXGB2ESn/"
    asyncio.run(process_workflow(url))
