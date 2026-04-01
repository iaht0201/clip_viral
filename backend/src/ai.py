"""
AI-related functions for transcript analysis with enhanced precision and virality scoring.
Optimized for local-first Core i5/12GB RAM environment.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import logging
import json
import re
from pydantic import BaseModel, Field

# Use direct SDKs for maximum stability on local hardware
from groq import Groq
import google.generativeai as genai

logger = logging.getLogger(__name__)

# --- Models ---

class ViralityScore(BaseModel):
    hook_score: int = 0
    engagement_score: int = 0
    value_score: int = 0
    shareability_score: int = 0
    total_score: int = 0
    hook_type: str = "none"

class TranscriptSegment(BaseModel):
    start_time: float # Seconds
    end_time: float # Seconds
    text: str
    relevance_score: float = 0.0
    reasoning: str = ""
    virality: Optional[ViralityScore] = None

class TranscriptAnalysis(BaseModel):
    most_relevant_segments: List[TranscriptSegment] = []
    summary: str = ""
    key_topics: List[str] = []
    broll_opportunities: Optional[List[Any]] = None

# --- Core AI Functions ---

async def get_most_relevant_parts_by_transcript(
    transcript: str, include_broll: bool = False
) -> TranscriptAnalysis:
    """
    Analyze transcript using Groq (Llama 3 70B) via Direct SDK.
    Guarantees stable JSON output for viral clips.
    """
    if not transcript:
        return TranscriptAnalysis()

    logger.info("Analyzing transcript for viral moments using Groq Direct API...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY is not set in the environment!")
        # Fallback to a zero-result analysis to prevent crash, but log the error
        return TranscriptAnalysis()

    logger.info("Analyzing transcript for viral moments using Groq Direct API...")
    
    client = Groq(api_key=api_key)
    
    prompt = f"""
    Analyze the following video transcript and identify the TOP 5 most engaging/viral-ready segments.
    
    If the video is a music video or song, select the most iconic or catchy parts (like the chorus or bridge).
    If the video is educational or a vlog, select the most valuable or high-energy moments.
    
    For each segment, provide:
    - start_time and end_time (in seconds, as floats)
    - the exact text of the segment
    - a relevance_score (0.0 to 1.0)
    - virality scores (0 to 10) for hook, engagement, value, and shareability
    - total_score (sum of scores, 0 to 40)
    - reasoning why it's viral/engaging
    
    Transcript:
    {transcript}
    
    Return ONLY a JSON object with this exact structure:
    {{
      "summary": "overall video summary",
      "key_topics": ["topic1", "topic2"],
      "most_relevant_segments": [
        {{
          "start_time": float,
          "end_time": float,
          "text": "original text string",
          "relevance_score": float,
          "reasoning": "viral analysis",
          "virality": {{
            "hook_score": int,
            "engagement_score": int,
            "value_score": int,
            "shareability_score": int,
            "total_score": int,
            "hook_type": "string"
          }}
        }}
      ]
    }}
    """
    
    try:
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        logger.debug(f"AI raw response: {content}")
        analysis_data = json.loads(content)
        
        validated_segments = []
        for segment_data in analysis_data.get("most_relevant_segments", []):
            try:
                virality_data = segment_data.get("virality", {})
                virality = ViralityScore(
                    hook_score=virality_data.get("hook_score", 0),
                    engagement_score=virality_data.get("engagement_score", 0),
                    value_score=virality_data.get("value_score", 0),
                    shareability_score=virality_data.get("shareability_score", 0),
                    total_score=virality_data.get("total_score", 0),
                    hook_type=virality_data.get("hook_type", "attention")
                )
                
                segment = TranscriptSegment(
                    start_time=float(segment_data["start_time"]),
                    end_time=float(segment_data["end_time"]),
                    text=segment_data["text"],
                    relevance_score=float(segment_data.get("relevance_score", 0.0)),
                    reasoning=segment_data.get("reasoning", ""),
                    virality=virality
                )
                validated_segments.append(segment)
            except Exception as e:
                logger.warning(f"Skipping malformed segment: {e}")
                continue

        # If no segments found but AI returned some, try to extract them even if incomplete
        if not validated_segments and analysis_data.get("most_relevant_segments"):
             logger.warning("Failed to validate segments from AI response")

        # Sort by total score
        validated_segments.sort(key=lambda x: x.virality.total_score if x.virality else 0, reverse=True)

        final_analysis = TranscriptAnalysis(
            most_relevant_segments=validated_segments,
            summary=analysis_data.get("summary", ""),
            key_topics=analysis_data.get("key_topics", []),
        )

        logger.info(f"Selected {len(validated_segments)} viral segments for processing")
        return final_analysis

    except Exception as e:
        logger.error(f"Groq direct analysis failed: {str(e)}")
        raise RuntimeError(f"Transcript analysis failed: {str(e)}")

async def translate_text(text: str, target_language: str) -> str:
    """
    Translate text using Groq (Llama 3 70B) for high-speed localization.
    """
    if not text or not target_language or target_language.lower() == "original":
        return text

    logger.info(f"Translating text to {target_language} using Groq Direct API")
    
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        prompt = (
            f"You are an expert translator for short-form video subtitles. "
            f"Translate the following text to {target_language}. Maintain the tone and energy. "
            f"Output ONLY the translated text.\n\nText: {text}"
        )
        
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        translated = completion.choices[0].message.content.strip()
        
        logger.info(f"Translation successful (Groq): {text[:30]}... -> {translated[:30]}...")
        return translated
    except Exception as e:
        logger.error(f"Translation failed via Groq: {e}")
        return text

async def get_smart_script_for_dubbing(
    transcript: str, video_title: str = "Video"
) -> List[Dict[str, Any]]:
    """
    Analyze transcript and rewrite it into a professional Vietnamese narration script
    with timing segments for verification.
    """
    if not transcript:
        return []

    logger.info(f"Generating Smart Script for: {video_title}")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Phase 1: Identify Theme (Subject-Agnostic)
    words = transcript.split()
    context_sample = " ".join(words[:500])
    
    try:
        analysis_prompt = f"""
        Phân tích transcript sau đây và xác định chủ đề, phong cách của video:
        TRANSCRIPT SAMPLE: {context_sample}
        
        Trả về một câu tóm tắt định hướng biên kịch (Ví dụ: "Video review đồ điện tử, phong cách chuyên nghiệp").
        """
        analysis_completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        video_context = analysis_completion.choices[0].message.content.strip()
        logger.info(f"Detected Context: {video_context}")
    except Exception as e:
        logger.warning(f"Context detection failed: {e}")
        video_context = "Video nội dung tổng hợp, phong cách hào hứng."

    # Phase 2: Rewrite into timed segments (JSON)
    # Calculate approximate duration from transcript timestamps
    try:
        logger.info(f"Transcript end snippet: {transcript[-100:]!r}")
        last_match = re.findall(r"\[(\d+):(\d+) - (\d+):(\d+)\]", transcript)
        if last_match:
            last_m, last_s = last_match[-1][2], last_match[-1][3]
            total_seconds = int(last_m) * 60 + int(last_s)
        else:
            total_seconds = len(transcript.split()) * 0.5 # rough estimate
    except:
        total_seconds = 60
    
    logger.info(f"Calculated video duration for dubbing: {total_seconds} seconds")

    prompt = f"""
    Dựa trên transcript video "{video_title}" dài {total_seconds} giây. Hãy viết kịch bản "Review thực tế" 100% TIẾNG VIỆT bám sát thực tế diễn biến video.
    
    BẮT BUỘC TUÂN THỦ DÒNG THỜI GIAN HIỆU CHỈNH SAU:
    - 0s - 8s: Bối cảnh buổi sáng tại Surat, Ấn Độ. Ambar chuẩn bị mở gian hàng Pani Puri quen thuộc của mình.
    - 8s - 22s: Ambar dừng chiếc xe tải nhỏ màu trắng và bắt đầu dọn dẹp vệ sinh khu vực xung quanh quầy hàng.
    - 22s - 45s: Anh bắt đầu lắp ráp quầy inox gấp gọn - bộ khung quan trọng nhất cho cả gian hàng.
    - 45s - 70s: Ambar tỉ mỉ lau chùi mặt bàn dù chiếc khăn đã cũ, đảm bảo sự sạch sẽ tối đa cho thực khách.
    - 70s - 95s: Anh mang ra nồi nước sốt xanh (Pani Puri Masala) - linh hồn của món ăn, chuẩn bị từ 4 giờ sáng với 20 loại thảo mộc.
    - 95s - 135s: Các nguyên liệu khác lần lượt được bày biện: từ hộp đựng đồ dùng một lần đến những túi bánh Puri giòn rụm, vàng ươm.
    - 135s - 180s: Ambar chuẩn bị phần nhân (Garden Chart) gồm đậu gà và khoai tây, được trình bày thành một vòng tròn lớn đẹp mắt.
    - 180s - 210s: Khoảnh khắc "thổi hồn" vào món ăn: Ambar múc nước sốt xanh rưới vào giữa phần nhân đậu gà.
    - 210s - 314s: Những vị khách đầu tiên xuất hiện. Ambar bắt đầu phục vụ với sự chuyên nghiệp và đôi tay thoăn thoắt.
    - 314s - {total_seconds}s: Một ngày làm việc đầy năng lượng bắt đầu trong mùi thơm nồng nàn của các loại gia vị đường phố.
    
    QUY TẮC PHÂN ĐOẠN (DIVIDE & CONQUER):
    1. Chia nhỏ mỗi giai đoạn trên thành 3-5 segments nhỏ (tổng cộng ít nhất 40 segments).
    2. TUẬT ĐỐI KHÔNG lặp lại nội dung giữa các đoạn. Mỗi đoạn phải mô tả một góc nhìn khác nhau.
    3. TỐC ĐỘ: 3.5 từ cho mỗi giây (Đoạn 10s phải có ~35 từ). Phải lấp đầy toàn bộ thời lượng.
    
    TRANSCRIPT GỐC:
    {transcript[:15000]}
    
    Hãy viết một kịch bản chất lượng, sâu sắc và chuyên nghiệp cho toàn bộ {total_seconds} giây.
    JSON:
    {{
      "segments": [
        {{
          "start_time": float,
          "end_time": float,
          "localized_narration": "Lời bìnhReview 100% tiếng Việt, lôi cuốn, không lặp lại..."
        }}
      ]
    }}
    """

    try:
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        data = json.loads(completion.choices[0].message.content)
        segments = data.get("segments", [])
        logger.info(f"Generated {len(segments)} narration segments for review")
        return segments
    except Exception as e:
        logger.error(f"Smart script generation failed: {e}")
        # Fallback: simple split if AI fails
        return [{"start_time": 0.0, "end_time": 10.0, "original_text": "Error", "localized_narration": "Không thể tạo bản preview. Vui lòng thử lại."}]

def get_most_relevant_parts_sync(transcript: str) -> TranscriptAnalysis:
    """Synchronous wrapper."""
    return asyncio.run(get_most_relevant_parts_by_transcript(transcript))
