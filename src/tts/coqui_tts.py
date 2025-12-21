# src/tts/coqui_tts.py
import os
import logging
from pathlib import Path
from TTS.api import TTS
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def ensure_models_downloaded():
    """Coqui modellerini indir (eğer yoksa)."""
    Config.ensure_directories()
    
    # Shorts modeli
    shorts_model_path = Config.MODELS_DIR / "fast_tacotron2"
    if not shorts_model_path.exists():
        logger.info("📥 Coqui Fast Tacotron2 modeli indiriliyor (Shorts için)...")
        TTS(model_name=Config.SHORTS_TTS_MODEL, progress_bar=True, gpu=False)
    
    # Podcast modeli
    podcast_model_path = Config.MODELS_DIR / "vits"
    if not podcast_model_path.exists():
        logger.info("📥 Coqui VITS modeli indiriliyor (Podcast için)...")
        TTS(model_name=Config.PODCAST_TTS_MODEL, progress_bar=True, gpu=False)
    
    logger.info("✅ Coqui modelleri hazır.")

def generate_tts(text: str, output_path: str, mode: str = "shorts"):
    """
    Coqui TTS ile ses üret.
    mode: 'shorts' veya 'podcast'
    """
    ensure_models_downloaded()
    
    logger.info(f"🎙️ Coqui TTS ile ses üretimine başlandı ({mode})...")
    
    # Modeli seç
    model_name = Config.SHORTS_TTS_MODEL if mode == "shorts" else Config.PODCAST_TTS_MODEL
    
    # TTS başlat (CPU modu)
    tts = TTS(
        model_name=model_name,
        progress_bar=True,
        gpu=False  # GitHub Actions'ta GPU yok
    )
    
    # Ses dosyası üret
    tts.tts_to_file(
        text=text,
        file_path=output_path
    )
    
    logger.info(f"✅ Ses dosyası oluşturuldu: {output_path}")
    return output_path
