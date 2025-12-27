# src/config.py
import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    
    IDEA_FILE = DATA_DIR / "idea.txt"
    SIDEA_FILE = DATA_DIR / "sidea.txt"
    
    HF_TOKEN = os.environ.get("HF_TOKEN", "")
    YOUTUBE_CREDENTIALS = os.environ.get("YOUTUBE_CREDENTIALS", "")
    
    SHORTS_DURATION = 60      # 1 dakika
    PODCAST_DURATION = 900    # 15 dakika
    
    SHORTS_CHAR_LIMIT = 1000
    PODCAST_CHAR_LIMIT = 15000
    
    SHORTS_TAGS = ["ColdWar", "History", "Shorts", "SynapseDaily"]
    PODCAST_TAGS = ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast"]
    
    @classmethod
    def ensure_directories(cls):
        for d in [cls.TEMP_DIR, cls.OUTPUT_DIR]:
            d.mkdir(exist_ok=True, parents=True)
