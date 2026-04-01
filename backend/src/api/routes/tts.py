from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import logging
from ...services.tts_service import TTSService
from ...config import Config

logger = logging.getLogger(__name__)
config = Config()
router = APIRouter(prefix="/tts", tags=["tts"])

@router.get("/generate")
async def generate_tts(
    text: str = Query(..., description="Text to convert to speech"),
    language: str = Query("English", description="Target language (English, Japanese, Vietnamese)"),
):
    """Generate TTS audio file and return it."""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        temp_dir = Path(config.temp_dir) / "tts"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        output_path = temp_dir / filename
        
        success = await TTSService.generate_speech(text, language, output_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="TTS generation failed")
            
        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in TTS route: {e}")
        raise HTTPException(status_code=500, detail=str(e))
