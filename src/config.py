# src/config.py
from pathlib import Path

class Config:
    # Proje kök dizini
    ROOT_DIR = Path(__file__).parent.parent
    
    # Data dizini
    DATA_DIR = ROOT_DIR / "data"
    
    # Görsel klasörleri
    IMAGES_DIR = DATA_DIR / "images"
    POD_IMAGES_DIR = IMAGES_DIR / "pod"
    SOR_IMAGES_DIR = IMAGES_DIR / "sor"
    
    # Script klasörleri
    SCRIPTS_DIR = DATA_DIR / "scripts"
    POD_SCRIPT = SCRIPTS_DIR / "pod.txt"
    SOR_SCRIPT = SCRIPTS_DIR / "sor.txt"
    
    # SideA dosyası
    SIDEA_FILE = DATA_DIR / "sidea.txt"
    
    # Temp ve output dizinleri
    TEMP_DIR = ROOT_DIR / "temp"
    OUTPUT_DIR = ROOT_DIR / "output"
    
    # Video süre sınırları
    MAX_SHORTS_DURATION = 90   # Maksimum 90 saniye
    MAX_PODCAST_DURATION = 3600  # Maksimum 60 dakika
    
    @classmethod
    def ensure_directories(cls):
        """Gerekli dizinleri oluştur."""
        for dir_path in [cls.TEMP_DIR, cls.OUTPUT_DIR, cls.POD_IMAGES_DIR, cls.SOR_IMAGES_DIR, cls.SCRIPTS_DIR]:
            dir_path.mkdir(exist_ok=True, parents=True)
