# src/config.py
import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    
    IDEA_FILE = DATA_DIR / "idea.txt"
    SIDEA_FILE = DATA_DIR / "sidea.txt"
    
    HF_TOKEN = os.environ.get("HF_TOKEN", "")
    YOUTUBE_TOKEN_BASE64 = os.environ.get("YOUTUBE_TOKEN_BASE64", "")
    
    SHORTS_DURATION = 60  # saniye
    PODCAST_DURATION = 900  # saniye (15 dakika)
    
    SHORTS_TAGS = ["ColdWar", "History", "Shorts", "SynapseDaily", "RetroFuturism"]
    PODCAST_TAGS = ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast", "SynapseDaily"]
    
    @classmethod
    def ensure_directories(cls):
        for dir_path in [cls.MODELS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR]:
            dir_path.mkdir(exist_ok=True, parents=True)
