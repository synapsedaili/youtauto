# run_pipeline.py
import argparse
import logging
import asyncio
from src.config import Config
from src.utils import setup_logging, get_todays_idea
from src.script_generator import generate_script
from src.video_generator import create_shorts_video, create_podcast_video, generate_voice_with_edge_tts
from src.upload_video import upload_to_youtube
from pathlib import Path
import tempfile

def run_shorts_pipeline():
    logger = setup_logging(Config.OUTPUT_DIR / "shorts.log")
    logger.info("📱 SHORTS PIPELINE BAŞLIYOR...")
    
    try:
        topic = get_todays_idea()
        logger.info(f"🎯 Konu: {topic}")
        
        script = generate_script(topic, mode="shorts")
        
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            
            # Ses üret (Edge TTS)
            audio_path = temp_path / "shorts_audio.mp3"
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Video üret
            video_path = temp_path / "shorts_video.mp4"
            create_shorts_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle
            description = f"{script[:300]}...\n\n#shorts #ColdWar #History #SynapseDaily"
            video_id = upload_to_youtube(
                str(video_path),
                topic,
                description,
                "public",
                "shorts"
            )
            
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
        
        script = generate_script(topic, mode="podcast")
        
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            
            # Ses üret (Edge TTS)
            audio_path = temp_path / "podcast_audio.mp3"
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Video üret
            video_path = temp_path / "podcast_video.mp4"
            create_podcast_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle
            description = (
                f"{script[:500]}...\n\n"
                "📚 SOURCES: CIA FOIA, NASA Archives, Internet Archive\n"
                "👉 Join our Patreon for extended cuts and blueprints!\n\n"
                "#ColdWarTech #UnbuiltCities #RetroFuturism #HistoryPodcast"
            )
            video_id = upload_to_youtube(
                str(video_path),
                topic,
                description,
                "private",
                "podcast"
            )
            
            logger.info(f"🎉 PODCAST TAMAMLANDI! YouTube ID: {video_id}")
    
    except Exception as e:
        logger.exception(f"❌ Podcast pipeline hatası: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synapse Daily Pipeline")
    parser.add_argument("--mode", choices=["shorts", "podcast"], required=True, help="Çalıştırılacak mod")
    args = parser.parse_args()
    
    Config.ensure_directories()
    
    if args.mode == "shorts":
        run_shorts_pipeline()
    else:
        run_podcast_pipeline()
