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
    try:
        # IDEA dosyasını oku
        if not Config.IDEA_FILE.exists():
            raise FileNotFoundError(f"idea.txt dosyası bulunamadı: {Config.IDEA_FILE}")
        
        with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
            ideas = [line.strip() for line in f if line.strip()]
        
        if not ideas:
            raise ValueError("idea.txt dosyası boş!")
        
        # SIDEA dosyasını oku veya oluştur
        if not Config.SIDEA_FILE.exists():
            Config.SIDEA_FILE.write_text("1", encoding="utf-8")
            logger.info("🔄 sidea.txt oluşturuldu (ilk değer: 1)")
        
        with open(Config.SIDEA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                current_index = 0
            else:
                try:
                    current_index = int(content) - 1
                except ValueError:
                    current_index = 0
        
        # Güncel konuyu seç
        selected_idea = ideas[current_index % len(ideas)]
        next_index = (current_index + 1) % len(ideas)
        
        # SIDEA dosyasını güncelle
        with open(Config.SIDEA_FILE, "w", encoding="utf-8") as f:
            f.write(str(next_index + 1))
        
        logger.info(f"🎯 Seçilen konu: {selected_idea} (İndeks: {current_index + 1}/{len(ideas)})")
        return selected_idea
        
    except Exception as e:
        logger.error(f"❌ Konu seçimi hatası: {str(e)}")
        # Fallback konu
        fallback_idea = "1960: Project Orion – The Nuclear Bomb-Powered Spaceship (USA)"
        logger.warning(f"🔄 Fallback konu kullanılıyor: {fallback_idea}")
        return fallback_idea

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
