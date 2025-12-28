# src/tts/gtts_tts.py
import os
import logging
from gtts import gTTS
from pydub import AudioSegment
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def split_text(text: str, max_chars: int = 4500) -> list:
    """Metni gTTS limitine göre parçalara böl."""
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= max_chars:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def generate_tts(text: str, output_path: str, mode: str = "shorts"):
    """
    gTTS ile ses üret (uzun metinler için parçalı).
    """
    logger.info(f"🎙️ gTTS ile ses üretimine başlandı ({mode})...")
    
    # Podcast için metni böl
    if mode == "podcast":
        chunks = split_text(text)
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"🔊 Chunk {i+1}/{len(chunks)} seslendiriliyor...")
            tts = gTTS(text=chunk, lang="en", slow=False)
            
            # Geçici dosya
            temp_path = f"/tmp/temp_chunk_{i}.mp3"
            tts.save(temp_path)
            
            # Pydub ile yükle
            audio_segments.append(AudioSegment.from_mp3(temp_path))
        
        # Tüm parçaları birleştir
        combined = sum(audio_segments)
        combined.export(output_path, format="mp3")
        
    else:
        # Shorts için normal seslendirme
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(output_path)
    
    logger.info(f"✅ Ses dosyası oluşturuldu: {output_path}")
    return output_path
