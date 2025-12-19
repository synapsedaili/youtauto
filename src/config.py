# src/config.py
import os

class Config:
    IDEA_FILE = "data/idea.txt"
    SIDEA_FILE = "data/sidea.txt"
    MODELS_DIR = "models"
    OUTPUT_DIR = "output"
    
    # TTS
    TTS_MODEL_PODCAST = "tts_models/en/ljspeech/vits"
    TTS_MODEL_SHORTS = "tts_models/en/ljspeech/fast_tacotron2"
    
    # Video
    SHORTS_DURATION = 60    # seconds
    PODCAST_DURATION = 900  # seconds (15 minutes)
    
    # YouTube
    SHORTS_TAGS = ["shorts", "ColdWar", "History", "SynapseDaily", "RetroFuturism"]
    PODCAST_TAGS = ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast", "SynapseDaily"]