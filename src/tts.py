# src/tts.py
import asyncio
import edge_tts
from src.utils import get_current_index

async def generate_voice_with_edge_tts(text: str, output_path: str):
    """AI zaten CTA eklememişse CTA ekle, eklemişse dokunma."""
    
    # AI'nın eklediği teknik terimleri temizle
    clean_text = text.replace("Opening shot", "").replace("Title:", "").replace("Chapter:", "")
    clean_text = clean_text.replace("Rules:", "").replace("Instructions:", "")
    clean_text = clean_text.strip()
    
    # CTA'ları kontrol et
    has_podcast_invite = False
    has_subscribe_cta = False
    
    text_lower = clean_text.lower()
    
    # Orta davet kontrolü
    if "for the full story" in text_lower and "podcast" in text_lower:
        has_podcast_invite = True
    
    # Son CTA kontrolü
    if "like," in text_lower and "comment" in text_lower and "subscribe" in text_lower:
        has_subscribe_cta = True
    
    # Orta davet yoksa ekle
    if not has_podcast_invite and len(clean_text) > 300:
        middle_point = len(clean_text) // 2
        split_pos = clean_text.rfind(".", 0, middle_point)
        if split_pos == -1:
            split_pos = middle_point
        else:
            split_pos += 1
        
        clean_text = clean_text[:split_pos] + "\n\nFor the full story, listen to today's podcast!\n\n" + clean_text[split_pos:]
    
   
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
