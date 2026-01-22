# src/tts.py
import asyncio
import edge_tts
from src.utils import get_current_index

async def generate_voice_with_edge_tts(text: str, output_path: str):

    clean_text = text.replace("Opening shot", "").replace("Title:", "").replace("Chapter:", "")
    clean_text = clean_text.replace("Rules:", "").replace("Instructions:", "")
    clean_text = clean_text.strip()
    
    current_index = get_current_index()
    voice = "en-US-GuyNeural" if current_index % 2 == 1 else "en-GB-SoniaNeural"
    
    communicate = edge_tts.Communicate(
        clean_text, 
        voice,
        rate="-5%",      
        volume="+0%",    
        pitch="+0Hz"     
    )
    
    await communicate.save(output_path)
