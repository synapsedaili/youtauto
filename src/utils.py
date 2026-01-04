# src/utils.py
import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path

def setup_logging(log_file: Path = None):
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    return logging.getLogger("SynapseDaily")

# src/utils.py
import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path

def setup_logging(log_file: Path = None):
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    return logging.getLogger("SynapseDaily")

def get_todays_idea():
    """Günlük konuyu döndürür (sidea.txt güncellenmez burada)."""
    from src.config import Config
    
    with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
        ideas = [line.strip() for line in f if line.strip()]
    
    if not ideas:
        raise ValueError("idea.txt dosyası boş!")
    
    current_index = 0
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                current_index = int(f.read().strip()) - 1
        except:
            current_index = 0
    
    selected_idea = ideas[current_index % len(ideas)]
    return selected_idea

def increment_sidea_counter():
    """sidea.txt dosyasını +1 artırır (sadece ikisi de başarılıysa çağrılır)."""
    from src.config import Config
    
    Config.ensure_directories()
    
    current_index = 0
    if Config.SIDEA 

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '_', filename)[:50]

def save_upload_log(video_id: str, title: str, mode: str):
    from src.config import Config
    Config.ensure_directories()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "video_id": video_id,
        "title": title,
        "mode": mode
    }
    
    log_file = Config.OUTPUT_DIR / "upload_log.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
