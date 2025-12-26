# src/utils.py
import os
import re
import json
import base64
import logging
from pathlib import Path
from datetime import datetime
from src.config import Config

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

def clean_unicode(text: str) -> str:
    """Özel karakterleri temizle (UnicodeEncodeError önlemek için)."""
    # En dash (–) ve em dash (—) gibi karakterleri çıkar
    text = text.replace('\u2013', '-').replace('\u2014', '--')
    # Diğer özel karakterleri temizle
    return ''.join(char for char in text if ord(char) < 128 or char in 'çğıöşüÇĞİÖŞÜ')

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
            logging.info("🔄 sidea.txt oluşturuldu (ilk değer: 1)")
        
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
        
        logging.info(f"🎯 Seçilen konu: {selected_idea} (İndeks: {current_index + 1}/{len(ideas)})")
        return selected_idea
        
    except Exception as e:
        logging.error(f"❌ Konu seçimi hatası: {str(e)}")
        # Fallback konu
        fallback_idea = "1960: Project Orion – The Nuclear Bomb-Powered Spaceship (USA)"
        logging.warning(f"🔄 Fallback konu kullanılıyor: {fallback_idea}")
        return fallback_idea

def download_font():
    """Arial fontunu indir."""
    font_path = "/tmp/arial.ttf"
    if not os.path.exists(font_path):
        os.makedirs("/tmp", exist_ok=True)
        try:
            import urllib.request
            urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf", font_path)
            logging.info("✅ Font indirildi")
        except Exception as e:
            logging.error(f"❌ Font indirme hatası: {str(e)}")
    return font_path

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
