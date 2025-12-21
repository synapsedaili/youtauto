# src/tts/piper_tts.py
import os
import logging
import subprocess
import sys
from pathlib import Path
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

# Piper model URL'leri
PIPER_MODELS = {
    "shorts": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx.json",
        "name": "en_US-lessac-low.onnx"
    },
    "podcast": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "name": "en_US-lessac-medium.onnx"
    }
}

def download_model(mode: str = "shorts"):
    """Piper modelini indir."""
    Config.ensure_directories()
    model_info = PIPER_MODELS[mode]
    model_path = Config.MODELS_DIR / model_info["name"]
    config_path = model_path.with_suffix(".onnx.json")
    
    if not model_path.exists():
        logger.info(f"📥 {mode.upper()} için Piper modeli indiriliyor...")
        # Modeli indir
        subprocess.run([
            "wget", "-O", str(model_path), model_info["url"]
        ], check=True)
        
        # Config dosyasını indir
        subprocess.run([
            "wget", "-O", str(config_path), model_info["config_url"]
        ], check=True)
    
    logger.info(f"✅ {mode.upper()} modeli hazır: {model_path}")
    return str(model_path)

def generate_tts(text: str, output_path: str, mode: str = "shorts"):
    """
    Piper TTS ile ses üret.
    """
    model_path = download_model(mode)
    logger.info(f"🎙️ Piper TTS ile ses üretimine başlandı ({mode})...")
    
    # Piper komutunu çalıştır
    cmd = [
        sys.executable, "-m", "piper",
        "--model", model_path,
        "--output", output_path
    ]
    
    # Metni Piper'a aktar
    try:
        result = subprocess.run(
            cmd,
            input=text,
            text=True,
            capture_output=True,
            check=True
        )
        logger.info(f"✅ Ses dosyası oluşturuldu: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Piper TTS hatası:\nStdout: {e.stdout}\nStderr: {e.stderr}")
        raise
