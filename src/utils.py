# src/utils.py
import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from src.config import Config

def setup_logging(log_file: Path = None):
    """Loglama yapılandırması."""
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    handlers = [logging.StreamHandler()]
    if log_safe_path := log_file:
        log_safe_path = Path(log_safe_path)
        log_safe_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_safe_path, encoding="utf-8"))
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers
    )
    return logging.getLogger("SynapseDaily")

def get_todays_idea():
    """Günlük konuyu döndürür (sidea.txt'den indeks okunur)."""
    with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
        ideas = [line.strip() for line in f if line.strip()]
    
    if not ideas:
        raise ValueError("idea.txt dosyası boş!")
    
    current_index = 0
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                current_index = int(f.read().strip()) - 1
        except (ValueError, IOError):
            current_index = 0
    
    selected_idea = ideas[current_index % len(ideas)]
    return selected_idea

def get_current_index():
    """sidea.txt'deki mevcut indeksi (1 tabanlı) döndürür."""
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return 1
    return 1

def increment_sidea_counter():
    """sidea.txt dosyasını +1 artırır."""
    Config.ensure_directories()
    
    current_index = 1
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                current_index = int(f.read().strip())
        except (ValueError, IOError):
            current_index = 1
    
    next_index = current_index + 1
    # DOĞRU YOLA YAZ
    with open(Config.SIDEA_FILE, "w") as f:
        f.write(str(next_index))
    
    logging.getLogger("SynapseDaily").info(f"✅ sidea.txt güncellendi: {current_index} → {next_index}")

def sanitize_filename(filename: str) -> str:
    """Dosya adını güvenli hale getirir."""
    return re.sub(r'[^\w\-_\. ]', '_', filename)[:50]

def save_upload_log(video_id: str, title: str, mode: str):
    """YouTube upload log'unu kaydeder."""
    Config.ensure_directories()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "video_id": video_id,
        "title": title,
        "mode": mode
    }
    
    log_file = Config.OUTPUT_DIR / "upload_log.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def split_script_into_chunks(script: str, max_chars=120) -> list:
    """Metni ekran sığacak şekilde kırpar."""
    words = script.split()
    chunks = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = current + " " + word if current else word
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks

# src/utils.py (sonuna EKLE)

def generate_seo_tags(topic: str, mode: str) -> str:
    """Dinamik SEO etiketleri üretir (maks 500 karakter)."""
    import re
    # Temel kelimeleri çıkar
    clean_topic = re.sub(r"[^\w\s]", "", topic)
    keywords = [word for word in clean_topic.split() if len(word) > 2 and not word.isdigit()]
    
    # Sabit temel etiketler
    if mode == "shorts":
        base_tags = ["Shorts", "History", "SynapseDaily"]
    else:
        base_tags = ["HistoryPodcast", "SynapseDaily", "Documentary"]
    
    # Dinamik etiketler
    dynamic_tags = [f"#{kw.replace(' ', '')}" for kw in keywords[:5]]
    all_tags = base_tags + dynamic_tags
    tag_str = " ".join(all_tags)
    
    # 500 karakter sınırı
    return tag_str[:500] if len(tag_str) > 500 else tag_str

def generate_shorts_description(topic: str) -> str:
    """Shorts için SEO odaklı açıklama üretir."""
    title_part = topic.split(":", 1)[1].strip() if ":" in topic else topic
    desc = f"""{title_part}? This isn't just history—it's a blueprint for our future!

    Discover the untold story behind this Cold War-era marvel that changed everything.

    Full story on our podcast! 🎙️

{generate_seo_tags(topic, 'shorts')}"""
    return desc

def generate_podcast_description(topic: str, script: str = "") -> str:
    """Zaman damgalı podcast açıklaması üretir."""
    year = topic.split(":")[0].strip() if ":" in topic else "Unknown"
    title_part = topic.split(":", 1)[1].strip() if ":" in topic else topic
    
    desc = f"""In {year}, a bold vision emerged that would redefine the future of urban living. Today, we go deep into the history of {title_part}.

    How was it built? What were the engineering challenges? Why does it still matter today?

    In this episode, we cover:

     The Vision
     Historical Context
     Engineering Breakthroughs
     Social Impact
     Legacy & Modern Relevance

     Whether you're a history buff, an architecture enthusiast, or just curious about lost futures, this episode is for you!

     Like this video if you learned something new! Comment your thoughts below and subscribe for more fascinating stories!

    {generate_seo_tags(topic, 'podcast')}"""
    return desc

# src/utils.py (sonuna EKLE)

def generate_seo_tags(topic: str, mode: str) -> str:
    """Dinamik SEO etiketleri üretir (maks 500 karakter)."""
    import re
    # Temel kelimeleri çıkar
    clean_topic = re.sub(r"[^\w\s]", "", topic)
    keywords = [word for word in clean_topic.split() if len(word) > 2 and not word.isdigit()]
    
    # Sabit temel etiketler
    if mode == "shorts":
        base_tags = ["Shorts", "History", "SynapseDaily"]
    else:
        base_tags = ["HistoryPodcast", "SynapseDaily", "Documentary"]
    
    # Dinamik etiketler
    dynamic_tags = [f"#{kw.replace(' ', '')}" for kw in keywords[:5]]
    all_tags = base_tags + dynamic_tags
    tag_str = " ".join(all_tags)
    
    # 500 karakter sınırı
    return tag_str[:500] if len(tag_str) > 500 else tag_str

def generate_shorts_description(topic: str) -> str:
    """Shorts için SEO odaklı açıklama üretir."""
    title_part = topic.split(":", 1)[1].strip() if ":" in topic else topic
    desc = f"""{title_part}? This isn't just history—it's a blueprint for our future!

Discover the untold story behind this Cold War-era marvel that changed everything.

Full story on our podcast! 🎙️

{generate_seo_tags(topic, 'shorts')}"""
    return desc

def generate_podcast_description(topic: str, script: str = "") -> str:
    """Zaman damgalı podcast açıklaması üretir."""
    year = topic.split(":")[0].strip() if ":" in topic else "Unknown"
    title_part = topic.split(":", 1)[1].strip() if ":" in topic else topic
    
    desc = f"""In {year}, a bold vision emerged that would redefine the future of urban living. Today, we go deep into the history of {title_part}.

How was it built? What were the engineering challenges? Why does it still matter today?

In this episode, we cover:

 - The Vision
 - Historical Context
 - Engineering Breakthroughs
 - Social Impact
 - Legacy & Modern Relevance

Whether you're a history buff, an architecture enthusiast, or just curious about lost futures, this episode is for you!

Like this video if you learned something new! Comment your thoughts below and subscribe for more fascinating stories!

{generate_seo_tags(topic, 'podcast')}"""
    return desc
