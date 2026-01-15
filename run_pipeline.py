# run_pipeline.py
import argparse
import asyncio
from pathlib import Path
import logging
from src.config import Config
from src.utils import (
    setup_logging,
    get_todays_idea,
    generate_shorts_description,
    generate_podcast_description,
    increment_sidea_counter,
    send_error_notification
)
from src.script_generator import generate_shorts_script, generate_podcast_script
from src.video_generator import create_shorts_video, create_podcast_video
from src.upload_video import upload_to_youtube, add_video_to_playlist
from src.tts import generate_voice_with_edge_tts
import tempfile

logger = setup_logging()

def parse_arguments():
    """Komut satırı argümanlarını parse eder."""
    parser = argparse.ArgumentParser(description='YouTube Shorts ve Podcast Pipeline')
    parser.add_argument('--mode', choices=['shorts', 'podcast'], required=True,
                        help='Çalıştırılacak mod: shorts veya podcast')
    return parser.parse_args()

def run_shorts_pipeline():
    """Shorts pipeline'ını çalıştırır ve YouTube'a yükler."""
    logger = setup_logging(Config.OUTPUT_DIR / "shorts.log")
    logger.info("📱 SHORTS PIPELINE BAŞLIYOR...")

    try:
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

    except Exception as e:
        logger.exception(f"❌ Shorts pipeline hatası: {str(e)}")
        # Hata durumunda bildirim gönder (isteğe bağlı)
        try:
            send_error_notification(f"Shorts pipeline failed: {str(e)}")
        except:
            pass
        raise

def run_podcast_pipeline():
    """Podcast pipeline'ını çalıştırır ve YouTube'a yükler."""
    logger = setup_logging(Config.OUTPUT_DIR / "podcast.log")
    logger.info("🎙️ PODCAST PIPELINE BAŞLIYOR...")

    try:
        # Konuyu al
        topic = get_todays_idea()
        logger.info(f"🎯 Konu: {topic}")
        
        # Script'i üret
        script = generate_podcast_script(topic)
        logger.info(f"📝 Üretilen script:\n{script[:200]}...")  # İlk 200 karakteri logla
        
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

    except Exception as e:
        logger.exception(f"❌ Podcast pipeline hatası: {str(e)}")
        # Hata durumunda bildirim gönder (isteğe bağlı)
        try:
            send_error_notification(f"Podcast pipeline failed: {str(e)}")
        except:
            pass
        raise

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.mode == "shorts":
        run_shorts_pipeline()
    elif args.mode == "podcast":
        run_podcast_pipeline()
