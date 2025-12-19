# src/tts/coqui_tts.py
import os
import logging
from TTS.api import TTS
from src.config import Config

logger = logging.getLogger(__name__)

def ensure_models():
    """Modelleri indir (cache'li)."""
    os.makedirs(Config.MODELS_DIR, exist_ok=True)

def generate_tts(text: str, output_path: str, mode: str = "podcast"):
    """Coqui TTS ile ses üret."""
    ensure_models()
    
    model_name = Config.TTS_MODEL_PODCAST if mode == "podcast" else Config.TTS_MODEL_SHORTS
    
    logger.info(f"🎙️ Coqui TTS başlatılıyor: {model_name}")
    tts = TTS(model_name=model_name, progress_bar=True, gpu=False)
    
    tts.tts_to_file(text=text, file_path=output_path)
    logger.info(f"✅ Ses dosyası: {output_path}")
    return output_path