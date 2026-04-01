
import os
import sys
import asyncio
from pathlib import Path
import logging
import json

# Add src to sys.path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print("Starting FULL 27m process...")
try:
    from src.video_utils import get_video_transcript
    from src.tts import generate_tts
    from groq import Groq
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, afx
    import edge_tts
    print("Imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    audio_path = Path("temp/full_audio_only.m4a")
    video_path = Path("temp/BV1xZXGB2ESn.mp4")
    if not audio_path.exists():
        print(f"Audio not found at {audio_path}")
        return

    # Step 1: Transcribe (Full 27 mins from audio file)
    print(f"Step 1: Transcribing FULL audio (27 mins)...")
    try:
        # get_video_transcript can also take audio files
        transcript = get_video_transcript(audio_path)
        print("Transcription complete.")
    except Exception as e:
        print(f"Transcription failed: {e}")
        return
    
    # Step 2: AI Analyzing video theme and style
    print("Step 2: AI Analyzing video theme and style...")
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Use a portion of transcript for context
        context_sample = transcript[:2000]
        analysis_prompt = f"""
        Phân tích transcript sau và xác định: Chủ đề, Phong cách (Hào hứng/Trang trọng/...) và Định dạng video.
        Transcript: {context_sample}
        Trả về 1 câu định hướng: "Đây là video [chủ đề], phong cách [phong cách]."
        """
        analysis_completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        video_context = analysis_completion.choices[0].message.content.strip()
        print(f"  Detected Context: {video_context}")

        # Split into chunks of 5000 chars
        chunks = [transcript[i:i+5000] for i in range(0, 30000, 5000)]
        
        script_parts = []
        for i, chunk in enumerate(chunks):
            if not chunk or len(chunk) < 300: continue
            
            print(f"  Rewriting chunk {i+1}...")
            prompt = f"""
            Bối cảnh video: {video_context}
            Dựa trên transcript phần {i+1} dưới đây, hãy viết một kịch bản thuyết minh (narration) tiếng Việt.
            Yêu cầu: Phù hợp với bối cảnh, dẫn dắt lôi cuốn, không bị lặp nội dung. Độ dài ~200 từ.
            Transcript: {chunk}
            """
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
            script_parts.append(completion.choices[0].message.content.strip())
            await asyncio.sleep(10)
            
        script = "\n\n".join(script_parts)
        print(f"Full script generated ({len(script)} chars).")
    except Exception as e:
        print(f"Rewriting failed: {e}")
        script = "Hành trình review ẩm thực Hà Nam 4 ngày trọn vẹn..."

    # Step 4: Generate Edge-TTS
    print("Step 3: Generating FULL Edge-TTS Audio...")
    tts_path = video_path.parent / "full_edge_narration.wav"
    try:
        communicate = edge_tts.Communicate(script, "vi-VN-NamMinhNeural")
        await communicate.save(str(tts_path))
        print(f"Edge-TTS generated.")
    except Exception as e:
        print(f"Edge-TTS failed: {e}")
        return

    # Step 5: Mixing and Rendering
    print("Step 4: Mixing and Rendering (This takes ~30-45 mins)...")
    try:
        video = VideoFileClip(str(video_path))
        
        # Audio
        bg_audio = video.audio.with_effects([afx.MultiplyVolume(0.15)])
        den_audio = AudioFileClip(str(tts_path))
        
        # If narration is shorter (likely), we just let the bg audio continue.
        # Position narration at start
        final_audio = CompositeAudioClip([bg_audio, den_audio.with_start(0)])
        
        final_video = video.with_audio(final_audio)
        
        output_path = video_path.parent / "final_full_review_27m.mp4"
        
        # Render
        # bitrate reduced slightly for faster render on i5
        final_video.write_videofile(
            str(output_path), 
            codec="libx264", 
            audio_codec="aac", 
            threads=4, 
            bitrate="4000k",
            preset="ultrafast", # Priority on completion
            fps=video.fps or 30
        )
        print(f"FINAL SUCCESS! Video at: {output_path}")
    except Exception as e:
        print(f"Process failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
