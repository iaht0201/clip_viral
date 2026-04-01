import aiohttp
import logging
from pathlib import Path
from ..config import Config

logger = logging.getLogger(__name__)
config = Config()

class TTSService:
    """Service to handle local TTS generation using MeloTTS-Vietnamese."""
    
    def __init__(self, base_url: str = "http://localhost:8880"):
        self.base_url = base_url.rstrip("/")

    async def generate_voiceover(
        self, text: str, output_path: Path, speaker: str = "vov"
    ) -> bool:
        """
        Calls local MeloTTS endpoint to generate .wav file.
        BA Constraint: Max 500 characters per request.
        """
        if not text:
            return False
            
        # Clean text and enforce BA limit
        clean_text = text[:500].strip()
        logger.info(f"Generating TTS for {len(clean_text)} chars using MeloTTS at {self.base_url}")

        payload = {
            "text": clean_text,
            "speaker": speaker,
            "speed": 1.0
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/convert", json=payload, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(output_path, "wb") as f:
                            f.write(content)
                        logger.info(f"TTS generated successfully: {output_path}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"TTS API Error ({response.status}): {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Failed to connect to Local TTS Server: {e}")
            return False

    @staticmethod
    def get_fallback_service():
        """Returns a fallback service if MeloTTS is down (e.g. Edge-TTS)."""
        # We can implement Edge-TTS fallback here later if needed
        pass
