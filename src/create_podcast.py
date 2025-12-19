# src/create_podcast.py
import os
import tempfile
from pathlib import Path
from src.config import Config
from src.script_generator import generate_script
from src.tts.coqui_tts import generate_tts
from src.video_generator import create_video
from src.youtube_uploader import upload_video

def get_todays_idea():
    with open(Config.IDEA_FILE) as f:
        ideas = [l.strip() for l in f if l.strip()]
    with open(Config.SIDEA_FILE) as f:
        idx = int(f.read().strip()) - 1
    return ideas[idx % len(ideas)]

def main():
    idea = get_todays_idea()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Script
        script = generate_script(idea, mode="podcast")
        
        # TTS
        audio_path = temp_path / "podcast.wav"
        generate_tts(script, str(audio_path), mode="podcast")
        
        # Video
        video_path = temp_path / "podcast.mp4"
        create_video(str(audio_path), script, str(video_path), Config.PODCAST_DURATION)
        
        # Upload
        desc = f"{script[:500]}...\n\n#ColdWarTech #UnbuiltCities #RetroFuturism"
        video_id = upload_video(str(video_path), idea, desc, "private", is_shorts=False)
        
        print(f"✅ Podcast yüklendi: {video_id}")

if __name__ == "__main__":
    main()