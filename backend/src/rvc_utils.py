import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache for RVC models to avoid reloading
_rvc_instance = None
_current_model = None

try:
    from rvc_python.infer import RVCInference
    RVC_AVAILABLE = True
except ImportError:
    RVC_AVAILABLE = False
    logger.warning("rvc-python NOT found. Voice conversion will be skipped. Install with 'pip install rvc-python'.")

def apply_voice_conversion(input_path: Path, output_path: Path, persona: str = "den") -> bool:
    """
    Apply RVC voice conversion to an existing audio file.
    Supports specific personas like 'den' mapped to local .pth models.
    """
    if not RVC_AVAILABLE:
        logger.error("RVC Voice Conversion requested but rvc-python is not installed.")
        return False

    global _rvc_instance, _current_model

    # Persona mapping
    persona_map = {
        "den": {
            "model": "/mnt/sdb3/model/Den/Den.pth",
            "index": "/mnt/sdb3/model/Den/added_IVF686_Flat_nprobe_1_Den_v2.index"
        }
    }

    if persona not in persona_map:
        logger.warning(f"Persona '{persona}' not found in RVC map. Skipping conversion.")
        return False

    config = persona_map[persona]
    model_path = config["model"]
    index_path = config.get("index")

    if not os.path.exists(model_path):
        logger.error(f"RVC model file not found: {model_path}")
        return False

    try:
        # Initialize or reload RVC instance if model changed
        if _rvc_instance is None or _current_model != model_path:
            logger.info(f"Loading RVC model: {model_path}...")
            _rvc_instance = RVCInference(device="cpu") # Force CPU for local stability
            _rvc_instance.set_model(model_path, index_path)
            _current_model = model_path

        logger.info(f"Applying RVC conversion ({persona}) to {input_path}...")
        _rvc_instance.infer(str(input_path), str(output_path))
        
        if output_path.exists():
            logger.info(f"RVC conversion successful: {output_path}")
            return True
        return False

    except Exception as e:
        logger.error(f"RVC conversion error: {e}")
        return False
