import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import logging
import gc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv("/mnt/sdb3/supoclip/supoclip/.env")

from src.video_download_utils import download_video, get_video_id
from src.ai import get_most_relevant_parts_by_transcript, translate_text
from src.video_utils import create_clips_from_segments
import assemblyai as aai

async def run_hybrid_test_pipeline(video_url: str):
    logger.info(f"--- STARTING HYBRID TEST PIPELINE for {video_url} ---")
    
    # 1. Ingestion (Phase 1)
    video_id = get_video_id(video_url)
    temp_dir = Path("/mnt/sdb3/supoclip/supoclip/backend/temp") / video_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # SMART CACHE: Video Download
    video_path = download_video(video_url)
    if not video_path:
        logger.error("Failed to download video")
        return

    # 2. Transcription (Caching Stage)
    transcript_cache = temp_dir / "transcript.json"
    if transcript_cache.exists():
        logger.info(f"Using CACHED transcription from {transcript_cache}")
        with open(transcript_cache, 'r') as f:
            transcript_text = json.load(f)["text"]
    else:
        logger.info("Transcribing audio with AssemblyAI (Model: universal-3-pro)...")
        aai.settings.api_key = os.getenv("ASSEMBLY_AI_API_KEY")
        transcriber = aai.Transcriber()
        config_aai = aai.TranscriptionConfig(speech_models=["universal-3-pro"])
        
        transcript_result = transcriber.transcribe(str(video_path), config=config_aai)
        if transcript_result.status == aai.TranscriptStatus.error:
            logger.error(f"AssemblyAI Error: {transcript_result.error}")
            return
            
        transcript_text = transcript_result.text
        # Save cache
        with open(transcript_cache, 'w') as f:
            json.dump({"text": transcript_text}, f)
        logger.info(f"Transcription saved to cache: {transcript_cache}")

    # 3. AI Brain Analysis (Caching Stage)
    analysis_cache = temp_dir / "analysis.json"
    if analysis_cache.exists():
        logger.info(f"Using CACHED viral analysis from {analysis_cache}")
        with open(analysis_cache, 'r') as f:
            analysis_dict = json.load(f)
            # Reconstruct our analysis object logic manually for segments
            from munch import Munch
            analysis_data = Munch.fromDict(analysis_dict)
    else:
        logger.info("Analyzing transcript for viral moments using Groq...")
        analysis_data = await get_most_relevant_parts_by_transcript(transcript_text)
        
        # Save cache (need to serialize for json)
        # Assuming analysis_data has .most_relevant_segments
        cache_data = {
            "most_relevant_segments": [
                {
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "text": s.text,
                    "relevance_score": s.relevance_score,
                    "reasoning": s.reasoning,
                    "virality": {
                        "total_score": s.virality.total_score if s.virality else 0,
                        "hook_score": s.virality.hook_score if s.virality else 0,
                        "engagement_score": s.virality.engagement_score if s.virality else 0,
                        "value_score": s.virality.value_score if s.virality else 0,
                        "shareability_score": s.virality.shareability_score if s.virality else 0,
                        "hook_type": s.virality.hook_type if s.virality else "N/A"
                    }
                } for s in analysis_data.most_relevant_segments
            ]
        }
        with open(analysis_cache, 'w') as f:
            json.dump(cache_data, f)
        logger.info(f"Analysis saved to cache: {analysis_cache}")

    # 4. Rendering & Anti-Copyright (Phase 4 - Sequential)
    logger.info("Rendering clips sequentially with Anti-Copyright measures...")
    clips_dir = Path("/mnt/sdb3/supoclip/supoclip/backend/outputs") / video_id
    
    # Extract segments list correctly whether munch or dict
    if hasattr(analysis_data, "most_relevant_segments"):
        raw_segments = analysis_data.most_relevant_segments
    else:
        raw_segments = analysis_data.get("most_relevant_segments", [])

    segments = []
    for i, seg in enumerate(raw_segments[:2]):
        # Support both object and dict access
        seg_text = seg.text if hasattr(seg, "text") else seg.get("text", "")
        start_time = seg.start_time if hasattr(seg, "start_time") else seg.get("start_time", 0.0)
        end_time = seg.end_time if hasattr(seg, "end_time") else seg.get("end_time", 0.0)
        relevance = seg.relevance_score if hasattr(seg, "relevance_score") else seg.get("relevance_score", 0.0)
        reasoning = seg.reasoning if hasattr(seg, "reasoning") else seg.get("reasoning", "")
        
        vn_text = await translate_text(seg_text, "Vietnamese")
        segments.append({
            "start_time": start_time,
            "end_time": end_time,
            "text": seg_text,
            "translated_text": vn_text,
            "relevance_score": relevance,
            "reasoning": reasoning
        })

    clip_infos = await create_clips_from_segments(
        video_path=video_path,
        segments=segments,
        output_dir=clips_dir,
        add_subtitles=True,
        target_language="Vietnamese"
    )

    logger.info(f"--- TEST PIPELINE COMPLETE. {len(clip_infos)} CLIPS RENDERED ---")

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=L87PAAejHPs"
    asyncio.run(run_hybrid_test_pipeline(url))
