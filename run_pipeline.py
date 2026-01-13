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

def run_shorts_pipeline():
    logger = setup_logging(Config.OUTPUT_DIR / "shorts.log")
    logger.info("📱 SHORTS PIPELINE BAŞLIYOR...")

    try:
        topic = get_todays_idea()
        logger.info(f"🎯 Konu: {topic}")
        script = generate_shorts_script(topic)
    if "For the full story" not in script:
        script = script.replace(".", ".\n\nFor the full story, listen to today's podcast!", 1)
    
    if "Like, comment, and subscribe" not in script:
        script += "\n\nLike, comment, and subscribe for more mysteries!"

        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "shorts_audio.mp3"
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))

            video_path = temp_path / "shorts_video.mp4"
            create_shorts_video(str(audio_path), script, str(video_path))

            description = generate_shorts_description(topic)
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "shorts")
            
            # 👇 SHORTS OYNATMA LİSTESİNE EKLE
            add_video_to_playlist(video_id, "PLj-SRcntMu9NhOfPCTJ0gOJcZfKmhaJ80")
            
            logger.info(f"🎉 SHORTS TAMAMLANDI! YouTube ID: {video_id}")

            

    except Exception as e:
        logger.exception(f"❌ Shorts pipeline hatası: {str(e)}")
        raise

def run_podcast_pipeline():
    logger = setup_logging(Config.OUTPUT_DIR / "podcast.log")
    logger.info("🎙️ PODCAST PIPELINE BAŞLIYOR...")

    try:
        topic = get_todays_idea()
        logger.info(f"🎯 Konu: {topic}")
        script = generate_podcast_script(topic)

        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "podcast_audio.mp3"
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))

            video_path = temp_path / "podcast_video.mp4"
            create_podcast_video(str(audio_path), script, str(video_path))

            description = generate_podcast_description(topic, script)
            video_id = upload_to_youtube(str(video_path), topic, description, "private", "podcast")
            
            # 👇 PODCAST OYNATMA LİSTESİNE EKLE
            add_video_to_playlist(video_id, "PLj-SRcntMu9Ng8Snbrm2kkAppJlNHeoq9")
            
            logger.info(f"🎉 PODCAST TAMAMLANDI! YouTube ID: {video_id}")
            increment_sidea_counter()

    except Exception as e:
        logger.exception(f"❌ Podcast pipeline hatası: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["shorts", "podcast"], required=True)
    args = parser.parse_args()

    if args.mode == "shorts":
        run_shorts_pipeline()
    else:
        run_podcast_pipeline()
