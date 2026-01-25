# run_pipeline.py
import argparse
import asyncio
from pathlib import Path
import logging
import sys
import os
from src.config import Config
from src.utils import (
    setup_logging,
    get_todays_idea,
    generate_shorts_description,
    generate_podcast_description,
    increment_sidea_counter
)
from src.script_generator import generate_shorts_script, generate_podcast_script
from src.video_generator import create_shorts_video, create_podcast_video
from src.upload_video import upload_to_youtube, add_video_to_playlist
from src.tts import generate_voice_with_edge_tts
import tempfile

# Python versiyon kontrolü
if sys.version_info < (3, 11):
    logging.warning("⚠️ Python 3.10 kullanıyorsunuz. 2026-10-04 tarihinden sonra destek sona erecek. Python 3.11+ kullanmanız önerilir.")

logger = setup_logging()

def ensure_directories():
    """Gerekli tüm dizinleri oluşturur."""
    Config.ensure_directories()
    # Ekstra dizin kontrolü
    for dir_path in [Config.TEMP_DIR, Config.OUTPUT_DIR, Config.DATA_DIR / "images" / "pod", Config.DATA_DIR / "images" / "sor"]:
        dir_path.mkdir(exist_ok=True, parents=True)
        if not dir_path.exists():
            logger.warning(f"⚠️ Dizin oluşturulamadı: {dir_path}")

def parse_arguments():
    """Komut satırı argümanlarını parse eder."""
    parser = argparse.ArgumentParser(description='YouTube Shorts ve Podcast Pipeline')
    parser.add_argument('--mode', choices=['shorts', 'podcast'], required=True,
                        help='Çalıştırılacak mod: shorts veya podcast')
    return parser.parse_args()

def send_error_notification(message: str):
    """Hata bildirimini loglar."""
    logger.error(f"🚨 HATA BİLDİRİMİ: {message}")

def run_shorts_pipeline():
    """Shorts pipeline'ını çalıştırır ve YouTube'a yükler."""
    logger = setup_logging(Config.OUTPUT_DIR / "shorts.log")
    logger.info("📱 SHORTS PIPELINE BAŞLIYOR...")

    try:
        # Dizinleri tekrar kontrol et
        ensure_directories()
        
        # Konuyu al
        topic = get_todays_idea()
        logger.info(f"🎯 Konu: {topic}")
        
        # Script'i üret
        script = generate_shorts_script(topic)
        logger.info(f"📝 Üretilen script:\n{script[:200]}...")  # İlk 200 karakteri logla
        
        # Eksik çağrıları kontrol et ve ekle
        if "For the full story" not in script and len(script) > 300:
            middle_point = len(script) // 2
            script = script[:middle_point] + "\n\nFor the full story, listen to today's podcast!" + script[middle_point:]
            logger.info("✅ Orta daveti otomatik eklendi")
        
        if "Like, comment, and subscribe" not in script:
            script += "\n\nLike, comment, and subscribe for more Cold War mysteries!"
            logger.info("✅ Son CTA otomatik eklendi")
        
        # Geçici dizin oluştur
        temp_dir_path = Config.TEMP_DIR / f"shorts_{os.getpid()}"
        temp_dir_path.mkdir(exist_ok=True, parents=True)
        
        try:
            audio_path = temp_dir_path / "shorts_audio.mp3"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Videoyu oluştur
            video_path = temp_dir_path / "shorts_video.mp4"
            logger.info("🎥 Video render ediliyor...")
            create_shorts_video(str(audio_path), script, str(video_path))
            
            # Açıklamayı oluştur
            description = generate_shorts_description(topic)
            
            # YouTube'a yükle
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "shorts")
            
            # Oynatma listesine ekle
            add_video_to_playlist(video_id, "PLj-SRcntMu9NhOfPCTJ0gOJcZfKmhaJ80")
            
            logger.info(f"🎉 SHORTS TAMAMLANDI! YouTube ID: {video_id}")
            
            # sidea.txt'yi güncelle
            increment_sidea_counter()

        finally:
            # Temizlik yap
            try:
                import shutil
                shutil.rmtree(temp_dir_path)
                logger.info(f"✅ Geçici dizin temizlendi: {temp_dir_path}")
            except Exception as e:
                logger.warning(f"⚠️ Geçici dizin temizlenemedi: {str(e)}")

    except Exception as e:
        error_msg = f"Shorts pipeline failed: {str(e)}"
        logger.exception(f"❌ Shorts pipeline hatası: {error_msg}")
        send_error_notification(error_msg)
        raise

def run_podcast_pipeline():
    """Podcast pipeline'ını çalıştırır ve YouTube'a yükler."""
    logger = setup_logging(Config.OUTPUT_DIR / "podcast.log")
    logger.info("🎙️ PODCAST PIPELINE BAŞLIYOR...")

    try:
        # Dizinleri tekrar kontrol et
        ensure_directories()
        
        # Konuyu al
        topic = get_todays_idea()
        logger.info(f"🎯 Konu: {topic}")
        
        # Script'i üret
        script = generate_podcast_script(topic)
        logger.info(f"📝 Üretilen script:\n{script[:200]}...")  # İlk 200 karakteri logla
        
        # Geçici dizin oluştur
        temp_dir_path = Config.TEMP_DIR / f"podcast_{os.getpid()}"
        temp_dir_path.mkdir(exist_ok=True, parents=True)
        
        try:
            audio_path = temp_dir_path / "podcast_audio.mp3"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Videoyu oluştur
            video_path = temp_dir_path / "podcast_video.mp4"
            logger.info("🎥 Video render ediliyor...")
            create_podcast_video(str(audio_path), script, str(video_path))
            
            # Açıklamayı oluştur
            description = generate_podcast_description(topic, script)
            
            # YouTube'a yükle
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "podcast")
            
            # Oynatma listesine ekle
            add_video_to_playlist(video_id, "PLj-SRcntMu9Ng8Snbrm2kkAppJlNHeoq9")
            
            logger.info(f"🎉 PODCAST TAMAMLANDI! YouTube ID: {video_id}")
            
            # sidea.txt'yi güncelle
            increment_sidea_counter()

        finally:
            # Temizlik yap
            try:
                import shutil
                shutil.rmtree(temp_dir_path)
                logger.info(f"✅ Geçici dizin temizlendi: {temp_dir_path}")
            except Exception as e:
                logger.warning(f"⚠️ Geçici dizin temizlenemedi: {str(e)}")

    except Exception as e:
        error_msg = f"Podcast pipeline failed: {str(e)}"
        logger.exception(f"❌ Podcast pipeline hatası: {error_msg}")
        send_error_notification(error_msg)
        raise

if __name__ == "__main__":
    # ÖNCE DİZİNLERİ OLUŞTUR
    ensure_directories()
    
    args = parse_arguments()
    
    if args.mode == "shorts":
        run_shorts_pipeline()
    elif args.mode == "podcast":
        run_podcast_pipeline()
