# src/utils.py
import os
import re
import json
import base64
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(log_file: Path = None):
    """Loglama ayarlarını yap."""
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
    """data/idea.txt ve data/sidea.txt'den günlük konuyu al."""
    from src.config import Config
    
    # Konuları oku
    with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
        ideas = [line.strip() for line in f if line.strip()]
    
    if not ideas:
        raise ValueError("idea.txt dosyası boş!")
    
    # Son indeksi oku
    current_index = 0
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                current_index = int(f.read().strip()) - 1
        except:
            current_index = 0
    
    # Güncel konuyu seç
    selected_idea = ideas[current_index % len(ideas)]
    next_index = (current_index + 1) % len(ideas)
    
    # sidea.txt'yi güncelle
    with open(Config.SIDEA_FILE, "w") as f:
        f.write(str(next_index + 1))
    
    return selected_idea

def sanitize_filename(filename: str) -> str:
    """Dosya adını güvenli hale getir."""
    return re.sub(r'[^\w\-_\. ]', '_', filename)[:50]

def save_upload_log(video_id: str, title: str, mode: str):
    """YouTube upload log'unu kaydet."""
    from src.config import Config
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "video_id": video_id,
        "title": title,
        "mode": mode
    }
    
    log_file = Config.OUTPUT_DIR / "upload_log.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def decode_youtube_credentials():
    """GitHub Secrets'ten base64 decode et."""
    from src.config import Config
    
    if not Config.YOUTUBE_CREDENTIALS:
        raise ValueError("YOUTUBE_CREDENTIALS secret'i ayarlanmamış!")
    
    try:
        json_data = base64.b64decode(Config.YOUTUBE_CREDENTIALS).decode("utf-8")
        credentials = json.loads(json_data)
        
        client_secret_path = Config.TEMP_DIR / "client_secret.json"
        with open(client_secret_path, "w") as f:
            json.dump(credentials, f)
        
        return str(client_secret_path)
    except Exception as e:
        raise ValueError(f"Kullanıcı bilgileri decode edilemedi: {str(e)}")

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
