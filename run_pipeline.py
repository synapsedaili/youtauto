# run_pipeline.py
import argparse
import logging
from src.config import Config
from src.utils import setup_logging, get_todays_idea
from src.script_generator import generate_script
from src.tts.gtts_tts import generate_tts
from src.video_generator import create_shorts_video, create_podcast_video
from src.upload_video import upload_to_youtube
from pathlib import Path
import tempfile
import os

def run_shorts_pipeline():
    """Shorts pipeline'ını çalıştır (minimum hata yönetimi)"""
    Config.ensure_directories()
    logger = setup_logging(Config.OUTPUT_DIR / "shorts.log")
    logger.info("📱 SHORTS PIPELINE BAŞLIYOR...")
    
    try:
        # 1. Konu seç
        topic = get_todays_idea()
        
        # 2. Script üret
        script = generate_script(topic, mode="shorts")
        
        # 3. Geçici dizin oluştur
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            
            # 4. Ses üret
            audio_path = temp_path / "shorts_audio.wav"
            generate_tts(script, str(audio_path), mode="shorts")
            
            # 5. Video üret
            video_path = temp_path / "shorts_video.mp4"
            create_shorts_video(str(audio_path), script, str(video_path))
            
            # 6. YouTube'a yükle
            description = f"{script[:300]}...\n\n#shorts #ColdWar #History #SynapseDaily"
            video_id = upload_to_youtube(
                str(video_path),
                topic,
                description,
                "public",
                "shorts"
            )
            
            logger.info(f"🎉 SHORTS TAMAMLANDI! YouTube ID: {video_id}")
            return True
            
    except Exception as e:
        logger.critical(f"❌ KESİNLİKLE HATA: {str(e)}")
        logger.critical("💡 ÇÖZÜM: GitHub Secrets'te YOUTUBE_TOKEN_ENCODED secret'ini kontrol edin")
        raise

def run_podcast_pipeline():
    """Podcast pipeline'ını çalıştır"""
    Config.ensure_directories()
    logger = setup_logging(Config.OUTPUT_DIR / "podcast.log")
    logger.info("🎙️ PODCAST PIPELINE BAŞLIYOR...")
    
    try:
        topic = get_todays_idea()
        script = generate_script(topic, mode="podcast")
        
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            
            audio_path = temp_path / "podcast_audio.wav"
            generate_tts(script, str(audio_path), mode="podcast")
            
            video_path = temp_path / "podcast_video.mp4"
            create_podcast_video(str(audio_path), script, str(video_path))
            
            description = f"{script[:500]}...\n\n📚 SOURCES: CIA FOIA, NASA Archives\n#ColdWarTech #UnbuiltCities"
            video_id = upload_to_youtube(
                str(video_path),
                topic,
                description,
                "public",
                "podcast"
            )
            
            logger.info(f"🎉 PODCAST TAMAMLANDI! YouTube ID: {video_id}")
            return True
            
    except Exception as e:
        logger.critical(f"❌ KESİNLİKLE HATA: {str(e)}")
        logger.critical("💡 ÇÖZÜM: GitHub Secrets'te YOUTUBE_TOKEN_ENCODED secret'ini kontrol edin")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["shorts", "podcast", "both"], default="shorts")
    args = parser.parse_args()
    
    if args.mode == "shorts":
        run_shorts_pipeline()
    elif args.mode == "podcast":
        run_podcast_pipeline()
    else:
        run_shorts_pipeline()
        run_podcast_pipeline()
