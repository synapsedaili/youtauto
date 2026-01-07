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
    
    SHORTS_CHAR_LIMIT = 1000
    PODCAST_CHAR_LIMIT = 30000
    
    SHORTS_DURATION = 60
    PODCAST_DURATION = 900
    
    @classmethod
    def ensure_directories(cls):
        for d in [cls.MODELS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR]:
            d.mkdir(exist_ok=True, parents=True)
