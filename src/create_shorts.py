# src/create_shorts.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
    return ideas[idx % len(ideas)], idx

def main():
    idea, idx = get_todays_idea()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Script
        script = generate_script(idea, mode="shorts")
        
        # TTS
        audio_path = temp_path / "shorts.wav"
        generate_tts(script, str(audio_path), mode="shorts")
        
        # Video
        video_path = temp_path / "shorts.mp4"
        create_video(str(audio_path), script, str(video_path), Config.SHORTS_DURATION)
        
        # Upload
        desc = f"{script[:500]}...\n\n#shorts #ColdWar #History"
        video_id = upload_video(str(video_path), idea, desc, "public", is_shorts=True)
        
        # sidea.txt'yi güncelle
        with open(Config.SIDEA_FILE, "w") as f:
            f.write(str((idx + 1) % len([l for l in open(Config.IDEA_FILE) if l.strip()]) + 1))
        
        print(f"✅ Shorts yüklendi: {video_id}")

if __name__ == "__main__":
    main()