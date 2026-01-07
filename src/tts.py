# src/tts.py
import asyncio
import edge_tts
from src.utils import get_current_index

async def generate_voice_with_edge_tts(text: str, output_path: str):
    """Edge TTS ile ses üretir. Tek sayı → erkek, Çift sayı → kadın."""
    current_index = get_current_index()
    
    if current_index % 2 == 1:
        voice = "en-US-GuyNeural"
    else:
        voice = "en-GB-SoniaNeural"
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
