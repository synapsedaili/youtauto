# run_pipeline.py
import tempfile
import asyncio
from pathlib import Path
import logging
import os
import shutil
from argparse import ArgumentParser

from src.config import Config
from src.utils import (
    setup_logging,
    get_todays_idea,
    get_current_index,
    generate_shorts_description,
    generate_podcast_description
)
from src.script_generator import generate_shorts_script, generate_podcast_script
from src.video_generator import create_shorts_video, create_podcast_video
from src.tts import generate_voice_with_edge_tts
from src.upload_video import upload_to_youtube, add_video_to_playlist

# 👇 NEW: Handle missing notifications module
try:
    from src.notifications import send_error_notification
except ImportError:
    # Fallback function
    def send_error_notification(message: str):
        logger = logging.getLogger("SynapseDaily")
        logger.error(f"🚨 ERROR NOTIFICATION: {message}")

def ensure_directories():
    """Gerekli tüm dizinleri oluşturur."""
    Config.ensure_directories()

def run_complete_pipeline():
    """Complete pipeline: Scripts → Images → Videos → Upload"""
    ensure_directories()
    
    # 1. Generate scripts
    logger = setup_logging(Config.OUTPUT_DIR / "pipeline.log")
    logger.info("🔄 COMPLETE PIPELINE STARTED...")
    
    try:
        topic = get_todays_idea()
        logger.info(f"🎯 Topic: {topic}")
        
        # Generate both scripts
        logger.info("📝 Generating podcast script...")
        podcast_script = generate_podcast_script(topic)
        
        logger.info("📝 Generating shorts script...")
        shorts_script = generate_shorts_script(topic)
        
        # 2. Generate images from scripts (using FIREFOX)
        logger.info("🖼️ Generating images from scripts...")
        from src.firefox_image_generator import FirefoxImageGenerator
        img_generator = FirefoxImageGenerator()
        
        # Generate podcast images
        logger.info("🎨 Generating podcast images...")
        podcast_images = img_generator.generate_images_from_script(topic, podcast_script, "podcast")
        
        # Generate shorts images
        logger.info("🎨 Generating shorts images...")
        shorts_images = img_generator.generate_images_from_script(topic, shorts_script, "shorts")
        
        # 3. Create videos (images already in place)
        logger.info("🎬 Creating videos...")
        
        # Shorts video
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "shorts_audio.mp3"
            
            logger.info("🎙️ Generating shorts audio...")
            asyncio.run(generate_voice_with_edge_tts(shorts_script, str(audio_path)))
            
            video_path = temp_path / "shorts_video.mp4"
            logger.info("🎥 Creating shorts video...")
            create_shorts_video(str(audio_path), shorts_script, str(video_path))
            
            # Upload shorts
            logger.info("📤 Uploading shorts...")
            description = generate_shorts_description(topic)
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "shorts")
            add_video_to_playlist(video_id, "PLj-SRcntMu9NhOfPCTJ0gOJcZfKmhaJ80")
            
            logger.info(f"🎉 SHORTS COMPLETED! ID: {video_id}")
        
        # Podcast video
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "podcast_audio.mp3"
            
            logger.info("🎙️ Generating podcast audio...")
            asyncio.run(generate_voice_with_edge_tts(podcast_script, str(audio_path)))
            
            video_path = temp_path / "podcast_video.mp4"
            logger.info("🎥 Creating podcast video...")
            create_podcast_video(str(audio_path), podcast_script, str(video_path))
            
            # Upload podcast
            logger.info("📤 Uploading podcast...")
            description = generate_podcast_description(topic)
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "podcast")
            add_video_to_playlist(video_id, "PLj-SRcntMu9Ng8Snbrm2kkAppJlNHeoq9")
            
            logger.info(f"🎉 PODCAST COMPLETED! ID: {video_id}")
            
            # Update sidea counter
            current_index = get_current_index()
            next_index = current_index + 1
            with open(Config.SIDEA_FILE, "w") as f:
                f.write(str(next_index))
            logger.info(f"✅ sidea.txt updated: {current_index} → {next_index}")
        
        logger.info("✅ COMPLETE PIPELINE FINISHED SUCCESSFULLY!")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")
        send_error_notification(f"Pipeline failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")
        send_error_notification(f"Pipeline failed: {str(e)}")
        raise

def run_shorts_pipeline():
    """Only shorts pipeline."""
    # Existing shorts functionality
    pass

def run_podcast_pipeline():
    """Only podcast pipeline."""
    # Existing podcast functionality
    pass

if __name__ == "__main__":
    parser = ArgumentParser(description='Content Pipeline')
    parser.add_argument('--mode', choices=['complete', 'shorts', 'podcast'], default='complete')
    args = parser.parse_args()
    
    if args.mode == 'complete':
        run_complete_pipeline()
    elif args.mode == 'shorts':
        run_shorts_pipeline()
    elif args.mode == 'podcast':
        run_podcast_pipeline()
