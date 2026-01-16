# src/tts.py
import asyncio  
import re
import logging
from pathlib import Path
from typing import Optional
import edge_tts
from src.config import Config
from src.utils import setup_logging, get_current_index

logger = setup_logging()

# İstisna listesi - bunlar temizlenmemeli
PROTECTED_PHRASES = [
    "background radiation",
    "background check",
    "background noise",
    "sound barrier",
    "sound wave",
    "sound level",
    "voiceover artist",
    "voiceover narration",
    "cold war effects",
    "long-term effects",
    "music theory",
    "opening statement",
    "seconds later",
    "opening ceremony"
  "starts with a shocking historical fact"
]

def clean_text_for_tts(text: str) -> str:
    """
    Seslendirme için metni kontekst koruyarak temizler.
    
    Args:
        text (str): Temizlenecek metin
    
    Returns:
        str: Temizlenmiş metin
    
    Temizlenenler:
    - Parantez içindeki teknik talimatlar
    - Köşeli parantez içindeki üretim notları
    - Sayı+harf kombinasyonları (015n, 23x gibi)
    - İzole edilmiş teknik ifadeler
    
    Korunanlar:
    - Tarihsel terimler (background radiation vb.)
    - Gerçek içerik cümleleri
    """
    if not text or not isinstance(text, str):
        logger.warning("⚠️ Temizlenecek metin boş veya geçersiz")
        return ""
    
    # Adım 1: İstisnaları geçici markerlarla koru
    protected_map = {}
    for phrase in PROTECTED_PHRASES:
        if phrase.lower() in text.lower():
            marker = f"__PROTECTED_{hash(phrase)}__"
            protected_map[marker] = phrase
            # Case-insensitive değiştirme
            text = re.sub(re.escape(phrase), marker, text, flags=re.IGNORECASE)
    
    # Adım 2: Parantez içindeki teknik talimatları temizle
    text = re.sub(r'\([^)]*?(opening|background|sound|effect|music|voiceover|seconds|fade in|cut to)[^)]*?\)', '', text, flags=re.IGNORECASE)
    
    # Adım 3: Köşeli parantez içindeki üretim notlarını temizle
    text = re.sub(r'\[[^\]]*?(opening|background|sound|effect|music|voiceover|seconds|fade in|cut to)[^\]]*?\]', '', text, flags=re.IGNORECASE)
    
    # Adım 4: Satır başı ve sonundaki izole teknik ifadeler
    text = re.sub(r'^(opening|background|sound|effect|music|voiceover|seconds|fade in|cut to)\b.*?[\n\.\!]', '', text, flags=re.IGNORECASE|re.MULTILINE)
    text = re.sub(r'\b(opening|background|sound|effect|music|voiceover|seconds|fade in|cut to).*?$', '', text, flags=re.IGNORECASE|re.MULTILINE)
    
    # Adım 5: Sayı+harf kombinasyonlarını temizle (015n, 23x gibi)
    text = re.sub(r'\b\d+[a-zA-Z]+\b', '', text)
    
    # Adım 6: İstisnaları geri yerleştir
    for marker, phrase in protected_map.items():
        text = text.replace(marker, phrase)
    
    # Adım 7: Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Adım 8: Minimum içerik kontrolü
    if len(text) < 200:
        logger.warning("⚠️ Temizlenen metin çok kısa. Fallback kullanılıyor.")
        fallback = (
            "This Cold War story changed everything. "
            "For the full story, listen to today's podcast! "
            "Like, comment, and subscribe for more fascinating stories!"
        )
        text = fallback
    
    logger.info(f"🧹 Temizlenmiş metin uzunluğu: {len(text)} karakter")
    return text

async def generate_voice_with_edge_tts(text: str, output_path: str, is_shorts: bool = False):
    try:
        logger.info("🎙️ Seslendirme başlatılıyor...")
        clean_text = clean_text_for_tts(text)
        
        # Kısa metinler için otomatik CTA
        if len(clean_text) < 400:
            clean_text += (
                "\n\nFor the full story, listen to today's podcast! "
                "Like, comment, and subscribe for more Cold War mysteries!"
            )
        
        # ⚡ SES PARAMETRELERİ
        if is_shorts:
            # Shorts'ta HER ZAMAN bu ses ve NORMAL hız
            voice = "en-US-GuyNeural" 
            rate = "+0%"            
            pitch = "+0Hz"
            volume = "+0%"
        else:
            # Podcast'te dinamik ses seçimi + YAVAŞLATILMIŞ
            current_index = get_current_index()
            voice = "en-GB-SoniaNeural" if current_index % 2 == 0 else "en-US-GuyNeural"
            rate = "-5%"    # %5 yavaşlat (daha anlatımsal)
            pitch = "+0Hz"
            volume = "+0%"
        
        logger.info(f"⚡ Ses parametreleri: voice={voice}, rate={rate}, pitch={pitch}, volume={volume}")
        
        # Seslendirme
        communicate = edge_tts.Communicate(
            clean_text,
            voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        await communicate.save(output_path)
        
        # Dosya kontrolü
        output_path = Path(output_path)
        if not output_path.exists() or output_path.stat().st_size < 1000:
            raise Exception("Ses dosyası oluşturma başarısız")
        
        logger.info(f"✅ Seslendirme tamamlandı: {output_path} ({output_path.stat().st_size//1024} KB)")
        
    except Exception as e:
        logger.exception(f"❌ Seslendirme hatası: {str(e)}")
        # Basit fallback metni
        fallback_text = (
            "Error generating voice. "
            "For the full story, listen to today's podcast. "
            "Like, comment, and subscribe for more Cold War mysteries!"
        )
        try:
            communicate = edge_tts.Communicate(
                fallback_text,
                "en-US-GuyNeural",  
                rate="-50%",
                pitch="+0Hz",
                volume="+3%"
            )
            await communicate.save(output_path)
            logger.info("✅ Basit fallback seslendirme başarılı")
        except Exception as fallback_e:
            logger.error(f"❌ Basit fallback de başarısız: {str(fallback_e)}")
            # Boş dosya oluştur (video üretimini durdurma)
            with open(output_path, 'wb') as f:
                f.write(b'')
            logger.warning("⚠️ Boş ses dosyası oluşturuldu. Video üretimine devam edilecek.")
