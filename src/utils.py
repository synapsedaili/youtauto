# src/utils.py
import logging
from datetime import datetime
from pathlib import Path
from src.config import Config

def setup_logging(log_file=None):
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    handlers = [logging.StreamHandler()]
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)
    return logging.getLogger("SynapseDaily")

def get_todays_idea():
    with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
        ideas = [line.strip() for line in f if line.strip()]
    if not ideas:
        raise ValueError("idea.txt boş!")
    idx = 0
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                idx = int(f.read().strip()) - 1
        except:
            idx = 0
    return ideas[idx % len(ideas)]

def get_current_index():
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 1
    return 1

def increment_sidea_counter():
    current = get_current_index()
    with open(Config.SIDEA_FILE, "w") as f:
        f.write(str(current + 1))
    logging.getLogger("SynapseDaily").info(f"✅ sidea.txt: {current} → {current + 1}")
