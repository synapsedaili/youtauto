# src/config.py
import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    
    # ✅ Karakter limitleri güncellendi
    SHORTS_CHAR_LIMIT = 1000  # Shorts için 1000 karakter
    PODCAST_CHAR_LIMIT = 45000  # Podcast için 45.000 karakter
    
    # API anahtarları
    HF_TOKEN = os.environ.get("HF_TOKEN", "")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    TOGETHERAI_API_KEY = os.environ.get("TOGETHERAI_API_KEY", "")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
    YOUTUBE_TOKEN_ENCODED = os.environ.get("YOUTUBE_TOKEN_ENCODED", "")
    
    SHORTS_TAGS = ["ColdWar", "History", "Shorts", "SynapseDaily", "RetroFuturism"]
    PODCAST_TAGS = ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast", "SynapseDaily"]
    
    @classmethod
    def ensure_directories(cls):
        for dir_path in [cls.MODELS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR]:
            dir_path.mkdir(exist_ok=True, parents=True)
