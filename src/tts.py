# src/tts.py
import asyncio
import edge_tts
from src.utils import get_current_index

async def generate_voice_with_edge_tts(text: str, output_path: str):
    """Seslendirme öncesi temizlik yapar."""
    clean_text = text.replace("[HOOK]", "").replace("[VOICE ON]", "").replace("[VOICE OFF]", "").strip()
    voice = "en-US-GuyNeural" if get_current_index() % 2 == 1 else "en-GB-SoniaNeural"
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(output_path)
