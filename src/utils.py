# src/utils.py
import logging
from pathlib import Path
from src.config import Config

def setup_logging(log_file=None):
    """Logging ayarlarını yap."""
    logger = logging.getLogger("SynapseDaily")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (opsiyonel)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_current_index():
    """
    Yarı otomatik sistemde sabit index döner.
    Çünkü görseller ve scriptler elle yönetiliyor.
    """
    return 1  # 👈 SABİT

def increment_sidea_counter():
    """
    Yarı otomatik sistemde sidea artırma YOK.
    Kullanıcı dosyaları elle yönetir.
    """
    logger = logging.getLogger("SynapseDaily")
    logger.info("📊 Yarı otomatik sistem: sidea.txt yönet
