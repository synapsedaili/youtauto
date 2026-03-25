# run_pipeline.py
import os
import sys
import asyncio
import tempfile
import logging
from pathlib import Path

# Src modüllerini import et
from src.config import Config
from src.utils import setup_logging, get_current_index, increment_sidea_counter
from src.tts import generate_voice_with_edge_tts
from src.video_generator import create_shorts_video, create_podcast_video
from src.upload_video import upload_to_youtube, add_video_to_playlist

logger = setup_logging()

def get_manual_script(mode: str) -> str:
    """Manuel eklenen script dosyasını okur."""
    script_path = Config.DATA_DIR / "scripts" / ("pod.txt" if mode == "podcast" else "sor.txt")
    
    if not script_path.exists():
        logger.error(f"❌ Script dosyası bulunamadı: {script_path}")
        raise FileNotFoundError(f"Script dosyası bulunamadı: {script_path}")
    
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read().strip()
    
    logger.info(f"📝 {mode.upper()} script dosyası okundu: {len(script)} karakter")
    return script

def run_shorts_pipeline():
    """Shorts pipeline'ını çalıştırır ve YouTube'a yükler."""
    logger = setup_logging(Config.OUTPUT_DIR / "shorts.log")
    logger.info("📱 SHORTS PIPELINE BAŞLIYOR...")

    try:
        # Manuel script'i al
        script = get_manual_script("shorts")
        logger.info(f"📝 Shorts script uzunluğu: {len(script)} karakter")
        
        # Mevcut sidea index'ini al (değiştirme)
        current_index = get_current_index()
        logger.info(f"📊 Shorts için sidea index: {current_index}")
        
        # Ses dosyasını oluştur
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "shorts_audio.mp3"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Videoyu oluştur
            video_path = temp_path / "shorts_video.mp4"
            logger.info("🎥 Video render ediliyor...")
            create_shorts_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle (private olarak)
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(
                str(video_path), 
                f"Shorts #{current_index}",  # Başlık (elle düzenlenecek)
                "Description will be added manually",  # Açıklama (elle düzenlenecek)
                "private",  # Private olarak yükle
                "shorts"
            )
            
            # Oynatma listesine ekle
            add_video_to_playlist(video_id, "PLj-SRcntMu9NhOfPCTJ0gOJcZfKmhaJ80")
            
            logger.info(f"🎉 SHORTS TAMAMLANDI! YouTube ID: {video_id}")
            logger.info(f"📊 Shorts tamamlandı, sidea değişmedi: {current_index}")

    except Exception as e:
        logger.exception(f"❌ Shorts pipeline hatası: {str(e)}")
        raise

def run_podcast_pipeline():
    """Podcast pipeline'ını çalıştırır ve YouTube'a yükler."""
    logger = setup_logging(Config.OUTPUT_DIR / "podcast.log")
    logger.info("🎙️ PODCAST PIPELINE BAŞLIYOR...")

    try:
        # Manuel script'i al
        script = get_manual_script("podcast")
        logger.info(f"📝 Podcast script uzunluğu: {len(script)} karakter")
        
        # Mevcut sidea index'ini al
        current_index = get_current_index()
        logger.info(f"📊 Podcast için sidea index: {current_index}")
        
        # Ses dosyasını oluştur
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "podcast_audio.mp3"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Videoyu oluştur
            video_path = temp_path / "podcast_video.mp4"
            logger.info("🎥 Video render ediliyor...")
            create_podcast_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle (private olarak)
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(
                str(video_path), 
                f"Podcast #{current_index}",  # Başlık (elle düzenlenecek)
                "Description will be added manually",  # Açıklama (elle düzenlenecek)
                "private",  # Private olarak yükle
                "podcast"
            )
            
            # Oynatma listesine ekle
            add_video_to_playlist(video_id, "PLj-SRcntMu9Ng8Snbrm2kkAppJlNHeoq9")
            
            logger.info(f"🎉 PODCAST TAMAMLANDI! YouTube ID: {video_id}")
            
            # 👇 PODCAST TAMAMLANDIĞINDA SIDEA ARTIR
            next_index = increment_sidea_counter()
            logger.info(f"✅ sidea.txt güncellendi: {current_index} → {next_index}")

    except Exception as e:
        logger.exception(f"❌ Podcast pipeline hatası: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("❌ Kullanım: python run_pipeline.py --mode shorts|podcast")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "shorts":
        run_shorts_pipeline()
    elif mode == "podcast":
        run_podcast_pipeline()
    else:
        logger.error(f"❌ Geçersiz mod: {mode}")
        sys.exit(1)
