# src/tts.py
import asyncio
import edge_tts
from src.utils import get_current_index

async def generate_voice_with_edge_tts(text: str, output_path: str):
     
    # 1. ✅ TEMİZLEME: Prompt terimlerini ve AI'nın eklediği başlıkları kaldır
    clean_text = text.replace("Start with SHOCKING HOOK (first 3 seconds)", "")
    clean_text = clean_text.replace("Include 2 curiosity questions", "")
    clean_text = clean_text.replace("End with CTA:", "").replace("Mid-video:", "")
    clean_text = clean_text.replace("Total characters:", "").replace("SCRIPT:", "")
    
    # 2. ✅ BAŞLIK VE TEKNİK TERİMLERİ TEMİZLE
    clean_text = clean_text.replace("Welcome to Synapse Daily", "")
    clean_text = clean_text.replace("Imagine it's", "")
    clean_text = clean_text.replace("Opening shot", "")
    clean_text = clean_text.replace("Based on", "")
    clean_text = clean_text.replace("Today we'll talk about", "")
    clean_text = clean_text.replace("In this video", "")
    clean_text = clean_text.replace("Title:", "")
    clean_text = clean_text.replace("Chapter:", "")
    clean_text = clean_text.replace("Part:", "")
    clean_text = clean_text.replace("Section:", "")
    clean_text = clean_text.replace("Rules:", "")
    clean_text = clean_text.replace("Instructions:", "")
    
    # 3. ✅ AI TARAFINDAN EKLENEN CTA'LARI TEMİZLE
    lines = clean_text.split("\n")
    filtered_lines = []
    for line in lines:
        line_lower = line.lower().strip()
        
        # AI'nın eklediği CTA'ları sil
        if "like," in line_lower and "comment" in line_lower and "subscribe" in line_lower:
            continue
        if "like this video" in line_lower:
            continue
        if "comment your thoughts" in line_lower:
            continue
        if "subscribe for more" in line_lower:
            continue
        if "for the full story" in line_lower and "podcast" in line_lower:
            continue
        
        filtered_lines.append(line)
    
    clean_text = "\n".join(filtered_lines).strip()
    
    # 4. ✅ BOŞ SATIRLARI TEMİZLE
    clean_text = "\n".join([line.strip() for line in clean_text.split("\n") if line.strip()])
    
    # 5. ✅ CTA'LARI YENİDEN EKLE (ama sadece bir kez ve doğru sırayla)
    has_podcast_invite = False
    has_subscribe_cta = False
    
    for line in clean_text.split("\n"):
        line_lower = line.lower()
        if "for the full story" in line_lower and "podcast" in line_lower:
            has_podcast_invite = True
        if "like, comment, and subscribe" in line_lower or "subscribe for more" in line_lower:
            has_subscribe_cta = True
    
    # Orta davet ekle (AI eklemezse)
    if not has_podcast_invite and len(clean_text) > 300:
        middle_point = len(clean_text) // 2
        # Orta noktada cümle bitimi bul
        split_pos = clean_text.rfind(".", 0, middle_point)
        if split_pos == -1:
            split_pos = middle_point
        else:
            split_pos += 1
        
        clean_text = clean_text[:split_pos] + "\n\nFor the full story, listen to today's podcast!\n\n" + clean_text[split_pos:]
    
    # Son CTA ekle (AI eklemezse)
    if not has_subscribe_cta:
        clean_text += "\n\nLike, comment, and subscribe for more Cold War mysteries!"
    
    # 6. ✅ SES AYARLARI: GitHub'da daha yavaş çalışması için
    current_index = get_current_index()
    voice = "en-US-GuyNeural" if current_index % 2 == 1 else "en-GB-SoniaNeural"
    
    # Edge TTS ayarları
    communicate = edge_tts.Communicate(
        clean_text, 
        voice,
        rate="-5%",      # %5 daha yavaş (GitHub'da hızlı çalışmasın diye)
        volume="+0%",    # Normal ses seviyesi
        pitch="+0Hz"     # Normal ton
    )
    
    # 7. ✅ SES DOSYASINI OLUŞTUR
    await communicate.save(output_path)
