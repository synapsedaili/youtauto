# src/config.py
import os
from pathlib import Path

class Config:
    """Tüm konfigürasyon ayarları"""
    
    # 📁 Dosya yolları
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    
    # 📄 IDEA dosyaları
    IDEA_FILE = DATA_DIR / "idea.txt"
    SIDEA_FILE = DATA_DIR / "sidea.txt"
    
    # ✅ Klasörleri oluştur
    @classmethod
    def ensure_directories(cls):
        for dir_path in [cls.MODELS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR, cls.DATA_DIR]:
            dir_path.mkdir(exist_ok=True, parents=True)
        
        # IDEA dosyalarını oluştur (eğer yoksa)
        if not cls.IDEA_FILE.exists():
            default_ideas = """1960: Project Orion – The Nuclear Bomb-Powered Spaceship (USA)
1960: DARPA's First AI Research Program Begins (USA)
1960: Atlantropa Revisited – German Engineers' Med Drain Plan (Germany)
1961: Biosphere 2 Concept First Drafted (USA)
1961: Soviet Alfa-Class Submarine Design Initiated (USSR)
1961: General Atomics Trago – Nuclear Locomotive Proposal (USA)"""
            cls.IDEA_FILE.write_text(default_ideas, encoding="utf-8")
            print(f"✅ {cls.IDEA_FILE} oluşturuldu")
        
        if not cls.SIDEA_FILE.exists():
            cls.SIDEA_FILE.write_text("1", encoding="utf-8")
            print(f"✅ {cls.SIDEA_FILE} oluşturuldu")
    
    # 🔑 API anahtarları
    YOUTUBE_TOKEN_ENCODED = os.environ.get("YOUTUBE_TOKEN_ENCODED", "")
    HF_TOKEN = os.environ.get("HF_TOKEN", "dummy_token")
    
    # 📏 Karakter limitleri
    SHORTS_CHAR_LIMIT = 1000
    PODCAST_CHAR_LIMIT = 15000
    
    # 🎥 Video ayarları
    SHORTS_DURATION = 60  # saniye
    PODCAST_DURATION = 900  # saniye (15 dakika)
    
    # 🏷️ YouTube etiketleri
    SHORTS_TAGS = ["ColdWar", "History", "Shorts", "SynapseDaily"]
    PODCAST_TAGS = ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast"]
