# src/utils/config.py
"""
Configuration Management
======================

Central configuration for the entire pipeline
"""

import os
from pathlib import Path

class Config:
    # Base directories
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    
    # Subdirectories
    SCRIPTS_DIR = DATA_DIR / "scripts"
    PROMPTS_DIR = DATA_DIR / "prompts"
    AUDIO_DIR = DATA_DIR / "audio"
    VIDEO_DIR = DATA_DIR / "video"
    IMAGES_DIR = DATA_DIR / "images"
    
    # Files
    SIDEA_FILE = BASE_DIR / "sidea.txt"
    
    # API Keys (from environment)
    LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")
    HF_TOKEN = os.getenv("HF_TOKEN")
    KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
    KAGGLE_KEY = os.getenv("KAGGLE_KEY")
    YOUTUBE_TOKEN_ENCODED = os.getenv("YOUTUBE_TOKEN_ENCODED")
    
    # Production settings
    TOTAL_VIDEO_CLIPS = 120
    CLIP_DURATION = 5  # seconds
    TARGET_VIDEO_DURATION = 600  # 10 minutes
    CHAPTERS_COUNT = 13
    WORDS_PER_CHAPTER = 300
    
    # Safety settings
    MAX_KAGGLE_HOURS_PER_DAY = 5  # Stay under 30 hours/week
    COOLDOWN_AFTER_CLIPS = 10  # Add break after every 10 clips
    COOLDOWN_DURATION = 60  # seconds
    
    @classmethod
    def ensure_directories(cls):
        """Create all necessary directories."""
        for dir_path in [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.TEMP_DIR,
            cls.OUTPUT_DIR,
            cls.SCRIPTS_DIR,
            cls.PROMPTS_DIR,
            cls.AUDIO_DIR,
            cls.VIDEO_DIR,
            cls.IMAGES_DIR
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
