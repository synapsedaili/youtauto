# src/config.py
import os
from pathlib import Path

class Config:
    # 📁 Dosya yolları
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    
    # 🔑 API anahtarları
    HF_TOKEN = os.environ.get("HF_TOKEN", "dummy_token")  # Fallback token
    
    # ⚙️ Ses ayarları
    DEFAULT_PODCAST_VOICE = "male"  # Erkek ses (daha lgun)
    
    # 📏 Karakter limitleri
    SHORTS_CHAR_LIMIT = 1000
    PODCAST_CHAR_LIMIT = 15000
    
    # 🎥 Video ayarları
    SHORTS_DURATION = 60  # saniye
    PODCAST_DURATION = 900  # saniye (15 dakika)
    
    # 🔄 Hata yönetimi
    MAX_RETRIES = 3
    API_TIMEOUT = 180  # saniye
    
    @classmethod
    def ensure_directories(cls):
        """Gerekli klasörleri oluştur"""
        for dir_path in [cls.MODELS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR]:
            dir_path.mkdir(exist_ok=True, parents=True)
