# src/tts/gtts_tts.py
import os
import logging
from gtts import gTTS
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def generate_tts(text: str, output_path: str, mode: str = "shorts"):
    """
    gTTS ile ses üret.
    """
    logger.info(f"🎙️ gTTS ile ses üretimine başlandı ({mode})...")
    
    # gTTS başlat
    tts = gTTS(text=text, lang="en", slow=False)
    
    # Ses dosyası üret
    tts.save(output_path)
    
    logger.info(f"✅ Ses dosyası oluşturuldu: {output_path}")
    return output_path
