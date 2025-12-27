# src/utils.py
import os
import re
import json
import base64
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(log_file=None):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    return logging.getLogger("SynapseDaily")

def get_todays_idea():
    from src.config import Config
    with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
        ideas = [line.strip() for line in f if line.strip()]
    current_index = 0
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                current_index = int(f.read().strip()) - 1
        except:
            pass
    selected = ideas[current_index % len(ideas)]
    with open(Config.SIDEA_FILE, "w") as f:
        f.write(str((current_index + 1) % len(ideas) + 1))
    return selected

def split_script_into_chunks(script: str, max_chars=120) -> list:
    words = script.split()
    chunks = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = current + " " + word if current else word
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks

def decode_youtube_credentials():
    from src.config import Config
    if not Config.YOUTUBE_CREDENTIALS:
        raise ValueError("YOUTUBE_CREDENTIALS eksik")
    data = base64.b64decode(Config.YOUTUBE_CREDENTIALS).decode()
    path = Config.TEMP_DIR / "client_secret.json"
    with open(path, "w") as f:
        json.dump(json.loads(data), f)
    return str(path)
