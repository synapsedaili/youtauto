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
    PODCAST_CHAR_LIMIT = 225000  # 15 kat artırıldı
    
    # 🎥 Video ayarları
    SHORTS_DURATION = 60  # saniye
    PODCAST_DURATION = 900  # saniye (15 dakika)
