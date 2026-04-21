"""
AI-related functions for transcript analysis with enhanced precision and virality scoring.
VERSION 2.1 - Tối ưu 100% (Stage 1-4)
"""

import os
from pathlib import Path
import re
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional
import asyncio
import logging
import json
from pydantic import BaseModel, Field

from .config import Config
from .video_utils import parse_timestamp_to_seconds as mmss_to_seconds

config = Config()

# Use Groq Direct SDK for maximum stability
from groq import Groq

logger = logging.getLogger(__name__)

# --- Models ---

class ViralityScore(BaseModel):
    hook_score: int = 0         # 0-25
    engagement_score: int = 0   # 0-25
    value_score: int = 0        # 0-25
    shareability_score: int = 0 # 0-25
    total_score: int = 0        # 0-100
    hook_type: str = "attention"
    rank: str = "C"             # S, A, B, C

class TranscriptSegment(BaseModel):
    start_time: float 
    end_time: float 
    text: str
    relevance_score: float = 0.0
    reasoning: str = ""
    virality: Optional[ViralityScore] = None

class TranscriptAnalysis(BaseModel):
    most_relevant_segments: List[TranscriptSegment] = []
    summary: str = ""
    key_topics: List[str] = []
    broll_opportunities: Optional[List[Any]] = None

# === HELPER: CALCULATE RANK ===
def calculate_viral_rank(total_score: int) -> str:
    if total_score >= 85: return "S"     # Viral cực mạnh
    if total_score >= 70: return "A"     # Tiềm năng cao
    if total_score >= 50: return "B"     # Khá
    return "C"                           # Trung bình

# === POST-PROCESSING MẠNH (Stage 4) ===
def advanced_post_processing(segments: List[TranscriptSegment], min_gap: int = 15) -> List[TranscriptSegment]:
    """Overlap removal + Diversity + Duration Guard"""
    if not segments:
        return []

    # Sort by total score (High to Low)
    segments.sort(key=lambda x: x.virality.total_score if x.virality else (x.relevance_score * 100), reverse=True)

    selected = []
    used_ranges = []

    for seg in segments:
        start_sec = float(seg.start_time)
        end_sec = float(seg.end_time)
        duration = end_sec - start_sec

        # Guard: Segment phải đủ dài để viral (10s - 50s)
        if duration < 10 or duration > 50:
            continue

        # Check overlap (chống trùng lặp thời gian)
        overlap = False
        for used_start, used_end in used_ranges:
            # Nếu đoạn này nằm đè lên đoạn đã chọn (+ gap an toàn)
            if max(start_sec, used_start) < min(end_sec, used_end) + min_gap:
                overlap = True
                break

        if not overlap:
            # Fix rank based on python logic for consistency
            if seg.virality:
                seg.virality.rank = calculate_viral_rank(seg.virality.total_score)
            
            selected.append(seg)
            used_ranges.append((start_sec, end_sec))

        if len(selected) >= 10: 
            break

    # Trả về danh sách sắp xếp theo thời gian để dễ theo dõi
    selected.sort(key=lambda x: x.start_time)
    return selected

# === NEW: Translate Text (Async) ===
async def translate_text(text: str, target_lang: str) -> str:
    """Translate segment text using Groq LLM (v2.1)"""
    if not text or not target_lang or target_lang.lower() == "original":
        return text

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return text

    client = Groq(api_key=api_key)
    prompt = f"Bạn là chuyên gia dịch thuật. Hãy dịch đoạn văn bản sau sang ngôn ngữ '{target_lang}'. Chỉ trả về bản dịch, không thêm chú thích.\n\nTEXT: {text}"

    try:
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant", # Dùng model nhanh cho translation
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = completion.choices[0].message.content
        logger.info(f"AI raw response: {content}")
        translated = content.strip()
        return translated if translated else text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

# === NEW: Smart Script for Dubbing ===
async def get_smart_script_for_dubbing(transcript: str, title: str) -> List[Dict[str, Any]]:
    """Generate a localized, engaging script for dubbing (v2.1)"""
    if not transcript:
        return []

    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    prompt = f"""Bạn là Reviewer chuyên nghiệp. Hãy viết lại transcript sau thành kịch bản lồng tiếng (dubbing) hấp dẫn, tự nhiên, mang phong cách TikTok Việt Nam.
TIÊU ĐỀ: {title}
TRANSCRIPT GỐC: {transcript}

Mục tiêu: Giữ nguyên ý nghĩa nhưng làm cho văn phong cuốn hút hơn, bớt từ thừa, nhấn đúng trọng tâm.
Chia thành các câu ngắn để dễ lồng tiếng.

TRẢ VỀ JSON:
{{
  "segments": [
    {{
      "start_time": float,
      "end_time": float,
      "text": "nội dung lồng tiếng mới"
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
        data = json.loads(completion.choices[0].message.content)
        return data.get("segments", [])
    except Exception as e:
        logger.error(f"Dubbing script error: {e}")
        return []

# --- Main AI Analysis Function ---

async def get_most_relevant_parts_by_transcript(
    transcript: str, include_broll: bool = False
) -> TranscriptAnalysis:
    """Advanced Multi-Stage Analysis v2.1 using Stable Groq SDK"""
    if not transcript or len(transcript.strip()) < 300:
        logger.warning("Transcript quá ngắn để phân tích viral.")
        return TranscriptAnalysis()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("Missing GROQ_API_KEY")
        return TranscriptAnalysis()

    client = Groq(api_key=api_key)
    logger.info(f"🚀 Phân tích Viral 2.1 cho transcript ({len(transcript)} chars)")

    # === PROMPT THẦN THÁNH v2.1 ===
    prompt = f"""Bạn là Viral Content Strategist hàng đầu thế giới năm 2026.
Nhiệm vụ: Trích xuất các đoạn Clip Viral đỉnh cao từ transcript.

=== RUBRIC CHẤM ĐIỂM (0-25 mỗi tiêu chí) ===
1. HOOK (0-25): Sức mạnh 3s đầu (Shock, tò mò, lời hứa hình ảnh).
2. ENGAGEMENT (0-25): Cảm xúc mạnh (hài hước, tranh cãi, kịch tính).
3. VALUE (0-25): Kiến thức mới, mẹo hay, aha moment.
4. SHAREABILITY (0-25): Sự đồng cảm, thôi thúc gửi cho bạn bè.
=> TỔNG ĐIỂM: 0 - 100.

=== QUY TẮC BẮT BUỘC ===
- THỜI LƯỢNG: Mỗi segment phải dài từ 15 đến 35 GIÂY (Không được cắt quá ngắn dưới 10s).
- NỘI DUNG: Phải là một câu chuyện hoặc ý kiến trọn vẹn, standalone có nghĩa.
- SỐ LƯỢNG: Tìm ít nhất 5-8 đoạn tốt nhất.
- NGÔN NGỮ: TRẢ VỀ TEXT CHÍNH XÁC TỪ TRANSCRIPT (VERBATIM).

=== TRẢ VỀ JSON THEO CẤU TRÚC ===
{{
  "summary": "Tóm tắt chiến lược viral của video",
  "key_topics": ["chủ đề 1", "chủ đề 2"],
  "most_relevant_segments": [
    {{
      "start_time": float,
      "end_time": float,
      "text": "văn bản gốc",
      "relevance_score": float (0-1),
      "reasoning": "Tại sao đoạn này viral?",
      "virality": {{
        "hook_score": int,
        "engagement_score": int,
        "value_score": int,
        "shareability_score": int,
        "total_score": int,
        "hook_type": "Curiosity/Shock/Question/Action",
        "rank": "S/A/B/C"
      }}
    }}
  ]
}}

TRANSCRIPT:
{transcript}
"""

    try:
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3 # Giữ AI ổn định, tránh sáng tạo quá mức vào text gốc
        )
        content = completion.choices[0].message.content
        logger.info(f"AI raw response: {content}")
        # Log transcript size
        logger.info(f"🚀 Phân tích Viral 2.1 - Transcript: {len(transcript)} ký tự")

        data = json.loads(content)

        segments = []
        for i, s in enumerate(data.get("most_relevant_segments", [])):
            try:
                v = s.get("virality", {})
                score = ViralityScore(
                    hook_score=v.get("hook_score", 0),
                    engagement_score=v.get("engagement_score", 0),
                    value_score=v.get("value_score", 0),
                    shareability_score=v.get("shareability_score", 0),
                    total_score=v.get("total_score", 0),
                    hook_type=v.get("hook_type", "attention"),
                    rank=v.get("rank", "C")
                )
                
                seg = TranscriptSegment(
                    start_time=float(s["start_time"]),
                    end_time=float(s["end_time"]),
                    text=s["text"],
                    relevance_score=float(s.get("relevance_score", 0.5)),
                    reasoning=s.get("reasoning", ""),
                    virality=score
                )
                segments.append(seg)
            except Exception as e:
                logger.warning(f"Malformed segment {i}: {e}")
                continue

        logger.info(f"AI parsed {len(segments)} potential segments. Starting post-processing...")
        # Stage 4: Hậu xử lý (Lọc Overlap + Guard thời lượng)
        final_segments = advanced_post_processing(segments)

        result = TranscriptAnalysis(
            most_relevant_segments=final_segments,
            summary=data.get("summary", ""),
            key_topics=data.get("key_topics", []),
            broll_opportunities=data.get("broll_opportunities") if include_broll else None
        )

        logger.info(f"✅ Đã phân tích xong! Chọn được {len(final_segments)} clips chất lượng cao.")
        return result

    except Exception as e:
        logger.error(f"AI Analysis Error: {e}")
        return TranscriptAnalysis()
