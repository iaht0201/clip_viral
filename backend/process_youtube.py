
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

print("Starting YouTube Localization...")
try:
    from src.video_utils import get_video_transcript
    from groq import Groq
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, afx
    import edge_tts
    print("Imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)

async def main():
    video_path = Path("temp/yt_source.mp4")
    if not video_path.exists():
        print(f"Video not found at {video_path}")
        return

    # Step 1: Transcribe
    print("Step 1: Transcribing...")
    try:
        transcript = get_video_transcript(video_path)
        print("Transcription complete.")
    except Exception as e:
        print(f"Transcription failed: {e}")
        return
    
    # Step 2: AI Analyzing topic and rewriting LONG script for full duration
    print("Step 2: AI Analyzing topic and rewriting LONG script...")
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Use a portion for initial analysis or let the 70b model handle it
        analysis_chunk = transcript[:2000]
        
        prompt = f"""
        Nhiệm vụ:
        1. Phân tích transcript sau để xác định chủ đề và phong cách video (Review công nghệ, Tin tức, Kể chuyện, Nấu ăn, v.v.).
        2. Viết một kịch bản thuyết minh (narration) tiếng Việt DÀI và CHI TIẾT bao phủ toàn bộ nội dung video (khoảng 5-10 phút).
        
        Yêu cầu chi tiết:
        - PHONG CÁCH: Điều chỉnh linh hoạt theo chủ đề đã xác định (Hào hứng cho Vlog, Chuyên nghiệp cho Review công nghệ, Nghiêm túc cho Tin tức).
        - ĐỘ DÀI: Khoảng 1500-2000 từ để đảm bảo giọng đọc phủ kín thời lượng video.
        - NGÔN NGỮ: Tiếng Việt tự nhiên, không dịch cứng nhắc. 
        - NỘI DUNG: Dẫn dắt lôi cuốn, mô tả cụ thể các sự kiện/hành động đang diễn ra dựa trên transcript.
        
        TRANSCRIPT GỐC:
        {transcript}
        """
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            # Using 3.3-70b for maximum quality and detail
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        script = completion.choices[0].message.content.strip()
        print(f"LONG script generated ({len(script)} chars). Full coverage mode.")
    except Exception as e:
        print(f"Rewriting failed: {e}")
        script = "Nội dung thuyết minh tự động chi tiết cho video..."

    # Step 3: Edge-TTS
    print("Step 3: Generating Edge-TTS (Nam Minh)...")
    tts_path = video_path.parent / "yt_den_voice.wav"
    try:
        communicate = edge_tts.Communicate(script, "vi-VN-NamMinhNeural")
        await communicate.save(str(tts_path))
        print(f"TTS generated.")
    except Exception as e:
        print(f"Edge-TTS failed: {e}")
        return

    # Step 4: Mixing and Rendering
    print("Step 4: Mixing and Rendering...")
    try:
        video = VideoFileClip(str(video_path))
        
        # Audio Ducking
        bg_audio = video.audio.with_effects([afx.MultiplyVolume(0.15)])
        den_audio = AudioFileClip(str(tts_path))
        
        # Composite audio
        final_audio = CompositeAudioClip([bg_audio, den_audio.with_start(0)])
        
        final_video = video.with_audio(final_audio)
        
        output_path = video_path.parent / "final_yt_review.mp4"
        
        # Fast render
        final_video.write_videofile(
            str(output_path), 
            codec="libx264", 
            audio_codec="aac", 
            threads=4, 
            preset="ultrafast",
            fps=video.fps or 30
        )
        print(f"SUCCESS! Final YouTube review at: {output_path}")
    except Exception as e:
        print(f"Rendering failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
