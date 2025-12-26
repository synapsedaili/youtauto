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
    
    IDEA_FILE = DATA_DIR / "idea.txt"
    SIDEA_FILE = DATA_DIR / "sidea.txt"
    
    # 🔑 API anahtarları (GitHub Secrets'ten gelecek)
    HF_TOKEN = os.environ.get("HF_TOKEN", "")
    YOUTUBE_CREDENTIALS = os.environ.get("YOUTUBE_CREDENTIALS", "")
    
    # ⏱️ Zamanlama
    DAILY_RUN_TIME = "16:00"  # TR saati
    
    # 📏 Karakter limitleri
    SHORTS_CHAR_LIMIT = 1000
    PODCAST_CHAR_LIMIT = 15000  
    
    # 🎥 Video ayarları
    SHORTS_DURATION = 60  # saniye
    PODCAST_DURATION = 900  # saniye (15 dakika)
    
    # 🏷️ YouTube etiketleri
    SHORTS_TAGS = ["ColdWar", "History", "Shorts", "SynapseDaily", "RetroFuturism"]
    PODCAST_TAGS = ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast", "SynapseDaily"]
    
    @classmethod
    def ensure_directories(cls):
        """Gerekli klasörleri oluştur."""
        for dir_path in [cls.MODELS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR]:
            dir_path.mkdir(exist_ok=True, parents=True)
