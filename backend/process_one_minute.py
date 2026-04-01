
import os
import sys
import asyncio
from pathlib import Path
import logging

# Add src to sys.path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print("Importing modules...")
try:
    from src.video_utils import get_video_transcript
    from src.tts import generate_tts
    from groq import Groq
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, vfx, afx
    print("Imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    video_path = Path("temp/test_bilibili.mp4")
    if not video_path.exists():
        print(f"Video not found at {video_path}")
        return

    print(f"Step 2: Transcribing video {video_path}...")
    try:
        transcript = get_video_transcript(video_path)
        print("Transcription complete.")
    except Exception as e:
        print(f"Transcription failed: {e}")
        return
    
    print("Step 3: AI Analyzing topic and rewriting to appropriate style...")
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Step 3.1: Analysis
        analysis_prompt = f"Phân tích transcript sau: xác định chủ đề và phong cách video. Transcript: {transcript[:1000]}. Trả về nội dung định hướng ngắn: 'Đây là video [chủ đề], phong cách [phong cách].'"
        analysis_completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        video_context = analysis_completion.choices[0].message.content.strip()
        print(f"  Detected Context: {video_context}")

        # Step 3.2: Rewrite
        prompt = f"""
        Bối cảnh video: {video_context}
        Nhiệm vụ: Viết lại transcript dưới đây thành một script thuyết minh ngắn gọn (30-45 giây), hào hứng, phong cách Reviewer chuyên nghiệp và phù hợp với bối cảnh video. 
        Chỉ trả về text tiếng Việt.
        
        Transcript:
        {transcript}
        """
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        script = completion.choices[0].message.content.strip()
        print(f"Rewritten Script:\n{script}")
    except Exception as e:
        print(f"Rewriting failed: {e}")
        script = transcript # Fallback

    print("Step 4: Generating Edge-TTS Voice (Base)...")
    tts_path = video_path.parent / "edge_voice_base.wav"
    try:
        # We manually use Edge-TTS here instead of the default generate_tts behavior
        import edge_tts
        communicate = edge_tts.Communicate(script, "vi-VN-NamMinhNeural")
        await communicate.save(str(tts_path))
        print(f"Edge-TTS generated at {tts_path}")
    except Exception as e:
        print(f"Edge-TTS failed: {e}")
        return

    print("Step 5: Mixing audio and rendering...")
    try:
        video = VideoFileClip(str(video_path))
        
        # Original audio ducked to 15%
        bg_audio = video.audio.with_effects([afx.MultiplyVolume(0.15)])
        
        # Den voice at 100%
        den_audio = AudioFileClip(str(tts_path))
        
        # Sync: Clip Den if longer, or just overlay
        if den_audio.duration > video.duration:
             den_audio = den_audio.subclipped(0, video.duration)
        
        final_audio = CompositeAudioClip([bg_audio, den_audio])
        final_video = video.with_audio(final_audio)
        
        output_path = video_path.parent / "final_den_review_60s.mp4"
        
        # Multi-threading for speed on i5
        final_video.write_videofile(str(output_path), codec="libx264", audio_codec="aac", threads=2, fps=video.fps or 30)
        print(f"Success! Final video at: {output_path}")
    except Exception as e:
        print(f"Mixing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
