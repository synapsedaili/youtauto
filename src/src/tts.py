# src/tts.py
import asyncio
import edge_tts
from src.utils import get_current_index

async def generate_voice_with_edge_tts(text: str, output_path: str):
    """Seslendirme öncesi temizlik yapar."""
    # ⚠️ Hook/voice etiketlerini KESİNLİKLE temizle
    clean_text = text.replace("[HOOK]", "").replace("[VOICE ON]", "").replace("[VOICE OFF]", "")
    clean_text = clean_text.strip()
    
    current_index = get_current_index()
    voice = "en-US-GuyNeural" if current_index % 2 == 1 else "en-GB-SoniaNeural"
    
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(output_path)
