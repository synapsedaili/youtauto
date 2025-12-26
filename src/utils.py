# src/utils.py
import logging
import os
from datetime import datetime
from src.config import Config

def setup_logging(log_file=None):
    """Loglama ayarları"""
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file or "pipeline.log") if log_file else logging.NullHandler()
        ]
    )
    return logging.getLogger("SynapseDaily")

def get_todays_idea():
    """Günlük konuyu seç"""
    Config.ensure_directories()
    
    # IDEA dosyasını oku
    with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
        ideas = [line.strip() for line in f if line.strip()]
    
    if not ideas:
        raise ValueError("idea.txt dosyası boş!")
    
    # SIDEA dosyasını oku
    current_index = 0
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                content = f.read().strip()
                current_index = int(content) - 1 if content else 0
        except:
            current_index = 0
    
    # Güncel konuyu seç
    selected_idea = ideas[current_index % len(ideas)]
    next_index = (current_index + 1) % len(ideas)
    
    # SIDEA dosyasını güncelle
    with open(Config.SIDEA_FILE, "w") as f:
        f.write(str(next_index + 1))
    
    print(f"🎯 Seçilen konu: {selected_idea} (İndeks: {current_index + 1}/{len(ideas)})")
    return selected_idea

def save_upload_log(video_id: str, title: str, mode: str):
    """Upload log'larını kaydet"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "video_id": video_id,
        "title": title,
        "mode": mode
    }
    
    log_file = Config.OUTPUT_DIR / "upload_log.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(log_entry) + "\n")
