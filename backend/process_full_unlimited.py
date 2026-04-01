
import os
import sys
import asyncio
from pathlib import Path
import logging
import edge_tts
from groq import Groq

# Add src to sys.path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from src.video_utils import get_video_transcript
    from moviepy import VideoFileClip, AudioFileClip, concatenate_audioclips, CompositeAudioClip, afx
    print("Imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)

async def main():
    video_path = Path("temp/yt_full_source.mp4")
    if not video_path.exists():
        print(f"Video not found at {video_path}")
        return

    # Step 1: Transcribe
    print("Step 1: Transcribing (Caching timing for segments)...")
    try:
        # We need more than just the string. 
        # But get_video_transcript caches raw json if we look at the src.
        # I'll just use the transcript string and ask AI to follow the FLOW.
        transcript = get_video_transcript(video_path)
        print("Transcription complete.")
    except Exception as e:
        print(f"Transcription failed: {e}")
        return

    # Step 2: AI Rewriting (Unlimited Full Coverage Mode)
    print("Step 2: AI Rewriting (Unlimited Full Coverage Mode)...")
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Split transcript into 5 large chunks (each ~2 mins) to stay within TPM
        words = transcript.split()
        chunk_size = len(words) // 5
        chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]

        # Step 2.1: Identify Video Nature
        print("  AI Analyzing video theme and style...")
        # Use first 500 words for context analysis
        context_sample = " ".join(words[:500])
        try:
            analysis_prompt = f"""
            Hãy phân tích đoạn transcript sau và xác định:
            1. CHỦ ĐỀ CHÍNH (ví dụ: Công nghệ, Nấu ăn, Du lịch, Tin tức, Movie review, v.v.)
            2. PHONG CÁCH DẪN (ví dụ: Hào hứng, Chuyên nghiệp, Trầm lắng, Hài hước)
            3. ĐỊNH DẠNG (ví dụ: Review sản phẩm, Kể chuyện, Phóng sự, Bình luận)
            
            TRANSCRIPT:
            {context_sample}
            
            Hãy trả về một câu tóm tắt định hướng biên kịch (ví dụ: "Đây là video review laptop, phong cách công nghệ chuyên nghiệp").
            """
            analysis_completion = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            video_context = analysis_completion.choices[0].message.content.strip()
            print(f"  Detected Context: {video_context}")
        except Exception as e:
            print(f"  Context detection failed: {e}")
            video_context = "Video nội dung tổng hợp, phong cách hào hứng, lôi cuốn."

        script_parts = []
        for i, chunk in enumerate(chunks[:5]):
            print(f"  Rewriting Part {i+1}...")
            prompt = f"""
            Bối cảnh video: {video_context}
            
            Dựa trên transcript phần {i+1} dưới đây, hãy viết một kịch bản thuyết minh (narration) tiếng Việt chi tiết.
            Yêu cầu:
            1. PHONG CÁCH: Phải phù hợp tuyệt đối với bối cảnh video (Nếu là Review thì cần nhận xét, nếu là Tin tức thì cần khách quan, nếu là Kể chuyện thì cần dẫn dắt).
            2. ĐỘ DÀI: Khoảng 300-350 từ để phủ kín phần này (2 phút).
            3. LIÊN KẾT: Đảm bảo nội dung nối tiếp phần trước một cách mượt mà.
            4. NGÔN NGỮ: Tiếng Việt tự nhiên, dùng từ ngữ phù hợp với chủ đề (thuật ngữ công nghệ nếu là đồ điện tử, từ gợi hình gợi cảm nếu là đồ ăn).
            
            TRANSCRIPT:
            {chunk}
            """
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
            script_parts.append(completion.choices[0].message.content.strip())
            await asyncio.sleep(8) # Avoid TPM/RPM
            
        full_script = "\n\n".join(script_parts)
        print(f"FULL Script generated ({len(full_script)} chars).")
    except Exception as e:
        print(f"Rewriting failed: {e}")
        full_script = "Nội dung thuyết minh tự động cho video..."

    # Step 3: Edge-TTS
    print("Step 3: Generating FULL Audio...")
    tts_path = video_path.parent / "full_den_voice.wav"
    try:
        communicate = edge_tts.Communicate(full_script, "vi-VN-NamMinhNeural")
        await communicate.save(str(tts_path))
        print(f"Full TTS generated.")
    except Exception as e:
        print(f"Edge-TTS failed: {e}")
        return

    # Step 4: Fast Mixing (FFmpeg Direct)
    print("Step 4: Mixing and Finalizing Video (Fast Muxing)...")
    output_path = video_path.parent / "final_yt_full_unlimited.mp4"
    
    # Use ffmpeg for speed and stability on long files
    cmd = (
        f"ffmpeg -v error -i {video_path} -i {tts_path} "
        f"-filter_complex \"[0:a]volume=0.2[bg]; [1:a]adelay=0|0[den]; [bg][den]amix=inputs=2:duration=longest:dropout_transition=3\" "
        f"-c:v copy -c:a aac -b:a 192k {output_path} -y"
    )
    
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()
    
    if output_path.exists():
        print(f"SUCCESS! Final video at: {output_path}")
    else:
        print("Mixing failed.")

if __name__ == "__main__":
    asyncio.run(main())
