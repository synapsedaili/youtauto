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
