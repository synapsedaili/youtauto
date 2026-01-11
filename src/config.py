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
  
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
  
    SHORTS_TAGS = ["ColdWar", "History", "Shorts", "SynapseDaily", "RetroFuturism"]
    PODCAST_TAGS = ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast", "SynapseDaily"]
    
    @classmethod
    def ensure_directories(cls):
      for dir_path in [cls.MODELS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR]:
          dir_path.mkdir(exist_ok=True, parents=True)
          (cls.DATA_DIR / "images" / "pod").mkdir(exist_ok=True, parents=True)
          (cls.DATA_DIR / "images" / "sor").mkdir(exist_ok=True, parents=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
