"""
Text-to-Speech utility using edge-tts.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
import edge_tts

logger = logging.getLogger(__name__)

import os
import sys
import logging
from pathlib import Path

# Force CPU mode for MeloTTS to avoid CUDA 13 missing library errors on i5
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TRITON_INTERPRET"] = "1" # For extra safety

# Ensure the Vietnamese-optimized Fork is at the top of the path (Priority #1)
melo_repo_path = "/mnt/sdb3/supoclip/supoclip/backend/melo_vietnamese_repo"
if melo_repo_path not in sys.path:
    sys.path.insert(0, melo_repo_path)

try:
    from melo.api import TTS
except ImportError as e:
    logger.error(f"MeloTTS-Vietnamese repo not found at {melo_repo_path}: {e}")
    # Last resort fallback, but we should fixed this
    from melo.api import TTS

logger = logging.getLogger(__name__)

# Global model cache to avoid reloading on every clip (saves RAM on i5)
_melo_model = None

def get_melo_model():
    global _melo_model
    if _melo_model is None:
        try:
            config_path = "/mnt/sdb3/supoclip/supoclip/backend/models/melo_vietnamese/pretrain/config.json"
            ckpt_path = "/mnt/sdb3/supoclip/supoclip/backend/models/melo_vietnamese/pretrain/G_463000.pth"
            
            logger.info(f"Loading local MeloTTS-Vietnamese model from {ckpt_path}...")
            # We use CPU by default for stability on i5, but it's very fast
            _melo_model = TTS(
                language="VI", 
                device="cpu",
                config_path=config_path,
                ckpt_path=ckpt_path
            )
            logger.info("MeloTTS-Vietnamese model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load MeloTTS model: {e}")
            return None
    return _melo_model

from .rvc_utils import apply_voice_conversion

async def generate_tts(text: str, target_language: str, output_path: Path, persona: Optional[str] = None, voice_id: Optional[str] = None) -> bool:
    """
    Generate professional-grade TTS using local MeloTTS-Vietnamese (nmcuong) or Edge-TTS.
    Optionally applies RVC voice conversion (e.g., 'den') to the synthesized output.
    """
    if not text:
        return False

    temp_audio_path = output_path.with_suffix(".temp.wav")
    final_audio_path = output_path
    
    # Decide if we need to use a temp file for conversion
    gen_path = temp_audio_path if persona else final_audio_path

    # Check if a specific voice_id is provided, if so, we might skip MeloTTS
    # unless it's specifically a melo voice (which we don't handle IDs for yet).
    success = False

    # 1. Try Local MeloTTS for Vietnamese if no specific Edge-TTS voice is requested
    if not voice_id and target_language.lower() == "vietnamese":
        model = get_melo_model()
        if model:
            logger.info(f"Generating professional MeloTTS for Vietnamese: {text[:40]}...")
            try:
                # Get the first available speaker
                speaker_ids = model.hps.data.spk2id
                speaker_id = list(speaker_ids.values())[0] if speaker_ids else 0
                
                # MeloTTS generate is blocking, but it's very fast for short segments
                model.tts_to_file(text, speaker_id, str(gen_path), speed=1.0)
                
                if gen_path.exists():
                    logger.info(f"MeloTTS audio saved: {gen_path}")
                    success = True
            except Exception as e:
                logger.error(f"MeloTTS generation error: {e}")
                logger.info("Falling back to Edge-TTS for Vietnamese...")

    # 2. Fallback to Edge-TTS if MeloTTS fails or for non-Vietnamese or if we have a voice_id
    if not success:
        voice = voice_id
        if not voice:
            voice_map = {
                "vietnamese": "vi-VN-NamMinhNeural",
                "english": "en-US-GuyNeural",
                "chinese": "zh-CN-YunxiNeural",
                "auto": "vi-VN-NamMinhNeural"
            }
            voice = voice_map.get(target_language.lower(), "vi-VN-NamMinhNeural")
            
        logger.info(f"Using Edge-TTS for {target_language} with voice {voice}: {text[:40]}...")
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(gen_path))
            
            if gen_path.exists():
                logger.info(f"Edge-TTS audio saved: {gen_path}")
                success = True
        except Exception as e:
            logger.error(f"Edge-TTS generation error: {e}")
            return False

    # 3. Apply RVC Voice Conversion if persona provided
    if success and persona:
        logger.info(f"Triggering voice conversion to persona: {persona}")
        try:
            rvc_success = apply_voice_conversion(gen_path, final_audio_path, persona)
            
            if rvc_success:
                logger.info(f"Successfully applied persona '{persona}' to TTS output.")
                # Clean up temp file
                if temp_audio_path.exists():
                    temp_audio_path.unlink()
                return True
            else:
                logger.error(f"Voice conversion failed for persona '{persona}'. Initial synthesis kept.")
                # If RVC fails, we still keep the original gen audio as final (rename if it was temp)
                if not final_audio_path.exists() and gen_path.exists():
                    gen_path.rename(final_audio_path)
                elif temp_audio_path.exists() and temp_audio_path != final_audio_path:
                    # Clean up temp if it's not the final one
                    temp_audio_path.unlink()
                return True # Still return True as base audio is valid
        except Exception as e:
            logger.error(f"Persona application failed: {e}")
            # Ensure we still have the original audio
            if not final_audio_path.exists() and gen_path.exists():
                gen_path.rename(final_audio_path)
            return True # Baseline TTS is still OK
            
    return success
