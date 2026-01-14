# src/tts.py
import asyncio
import edge_tts
from src.utils import get_current_index

async def generate_voice_with_edge_tts(text: str, output_path: str):
    """Seslendirme öncesi temizlik yapar."""
    # 👇 PROMPT TALİMATLARINI TEMİZLE
    clean_text = text.replace("Start with SHOCKING HOOK (first 3 seconds)", "")
    clean_text = clean_text.replace("Include 2 curiosity questions", "")
    clean_text = clean_text.replace("###", "")
    clean_text = clean_text.replace("[HOOK]", "").replace("[VOICE ON]", "").replace("[VOICE OFF]", "")
    clean_text = clean_text.strip()
    
    # 👇 ORTASINA VE SONUNA ÇAĞRI EKLE (AI eklemezse bile)
    if "For the full story" not in clean_text and len(clean_text) > 300:
        middle_point = len(clean_text) // 2
        clean_text = clean_text[:middle_point] + "\n\nFor the full story, listen to today's podcast!" + clean_text[middle_point:]
    
    if "Like, comment, and subscribe" not in clean_text:
        clean_text += "\n\nLike, comment, and subscribe for more Cold War mysteries!"
    
    current_index = get_current_index()
    voice = "en-US-GuyNeural" if current_index % 2 == 1 else "en-GB-SoniaNeural"
    
    # 👇 SES HIZI VE DURAKLAMALAR
    communicate = edge_tts.Communicate(
        clean_text, 
        voice,
        rate="+0%",     # Normal hız (rap değil!)
        volume="+0%", 
        pitch="+0Hz"
    )
    
    # 👇 NOKTALAMA İŞARETLERİNDE DURAKLAMA EKLE
    communicate.proxy = None
    await communicate.save(output_path)
