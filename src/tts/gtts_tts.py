# src/tts/gtts_tts.py
import os
import logging
from pathlib import Path
from gtts import gTTS
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def generate_tts(text: str, output_path: str, mode: str = "shorts"):
    """
    gTTS (Google Text-to-Speech) ile ses üret.
    mode: 'shorts' veya 'podcast'
    """
    logger.info(f"🎙️ gTTS ile ses üretimine başlandı ({mode})...")
    
    # Karakter sınırı kontrolü
    max_chars = Config.SHORTS_CHAR_LIMIT if mode == "shorts" else Config.PODCAST_CHAR_LIMIT
    
    if len(text) > max_chars:
        text = text[:max_chars]
    
    try:
        # gTTS ile ses üret
        tts = gTTS(text=text, lang="en", slow=False, lang_check=False)
        tts.save(output_path)
        
        logger.info(f"✅ Ses dosyası oluşturuldu: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"gTTS hatası: {str(e)}")
        raise
