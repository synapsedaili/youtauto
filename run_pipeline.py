# run_pipeline.py
import argparse
import asyncio
from pathlib import Path
import tempfile
from src.config import Config
from src.utils import (
    setup_logging,
    get_todays_idea,
    increment_sidea_counter,
    generate_shorts_description,
    generate_podcast_description
)
from src.script_generator import generate_shorts_script, generate_podcast_script
from src.video_generator import create_shorts_video, create_podcast_video
from src.tts import generate_voice_with_edge_tts
from src.upload_video import upload_to_youtube, add_video_to_playlist

Config.ensure_directories()
logger = setup_logging()
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
        
        # Ses ve video oluştur
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "shorts_audio.mp3"
            video_path = temp_path / "shorts_video.mp4"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            logger.info("🎥 Video render ediliyor...")
            create_shorts_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle
            description = generate_shorts_description(topic)
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "shorts")
            
            # Oynatma listesine ekle
            add_video_to_playlist(video_id, "PLj-SRcntMu9NhOfPCTJ0gOJcZfKmhaJ80")
            
            logger.info(f"🎉 SHORTS TAMAMLANDI! YouTube ID: {video_id}")
            
            # Sidea.txt'yi GÜNCELLE (sadece bir kez)
            increment_sidea_counter()

    except Exception as e:
        logger.exception(f"❌ Shorts pipeline hatası: {str(e)}")
        raise

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
        
        # Script'i üret (13 bölüm, 4 istekte)
        script = generate_podcast_script(topic)
        logger.info(f"📝 Üretilen script uzunluğu: {len(script)} karakter")
        
        # Ses ve video oluştur
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "podcast_audio.mp3"
            video_path = temp_path / "podcast_video.mp4"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            logger.info("🎥 Video render ediliyor...")
            create_podcast_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle
            description = generate_podcast_description(topic, script)
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "podcast")
            
            # Oynatma listesine ekle
            add_video_to_playlist(video_id, "PLj-SRcntMu9Ng8Snbrm2kkAppJlNHeoq9")
            
            logger.info(f"🎉 PODCAST TAMAMLANDI! YouTube ID: {video_id}")
            
            # Sidea.txt'yi GÜNCELLE (sadece bir kez)
            increment_sidea_counter()

    except Exception as e:
        logger.exception(f"❌ Podcast pipeline hatası: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "shorts"
    
    if mode == "shorts":
        run_shorts_pipeline()
    elif mode == "podcast":
        run_podcast_pipeline()
    else:
        print(f"❌ Geçersiz mod: {mode}. 'shorts' veya 'podcast' kullanın.")
        sys.exit(1)
