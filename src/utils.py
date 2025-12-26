# src/utils.py
import os
import re
import json
import base64
import logging
from pathlib import Path
from datetime import datetime
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def get_todays_idea():
    """data/idea.txt ve data/sidea.txt'den günlük konuyu al."""
    try:
        # IDEA dosyasını oku
        if not Config.IDEA_FILE.exists():
            raise FileNotFoundError(f"idea.txt dosyası bulunamadı: {Config.IDEA_FILE}")
        
        with open(Config.IDEA_FILE, "r", encoding="utf-8") as f:
            ideas = [line.strip() for line in f if line.strip()]
        
        if not ideas:
            raise ValueError("idea.txt dosyası boş!")
        
        # SIDEA dosyasını oku veya oluştur
        if not Config.SIDEA_FILE.exists():
            Config.SIDEA_FILE.write_text("1", encoding="utf-8")
            logger.info("🔄 sidea.txt oluşturuldu (ilk değer: 1)")
        
        with open(Config.SIDEA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                current_index = 0
            else:
                try:
                    current_index = int(content) - 1
                except ValueError:
                    current_index = 0
        
        # Güncel konuyu seç
        selected_idea = ideas[current_index % len(ideas)]
        next_index = (current_index + 1) % len(ideas)
        
        # SIDEA dosyasını güncelle
        with open(Config.SIDEA_FILE, "w", encoding="utf-8") as f:
            f.write(str(next_index + 1))
        
        logger.info(f"🎯 Seçilen konu: {selected_idea} (İndeks: {current_index + 1}/{len(ideas)})")
        return selected_idea
        
    except Exception as e:
        logger.error(f"❌ Konu seçimi hatası: {str(e)}")
        # Fallback konu
        fallback_idea = "1960: Project Orion – The Nuclear Bomb-Powered Spaceship (USA)"
        logger.warning(f"🔄 Fallback konu kullanılıyor: {fallback_idea}")
        return fallback_idea
