# src/video_generator.py
import os
from pathlib import Path
from moviepy.editor import (
    ColorClip, TextClip, CompositeVideoClip, AudioFileClip
)
from src.config import Config

def split_script(script: str, max_chars=120):
    words = script.split()
    chunks = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = current + " " + word if current else word
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks

def create_video(audio_path: str, script: str, output_path: str, duration: int):
    """Siyah arka plan + beyaz yazı videosu üret."""
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, duration)
    
    lines = split_script(script)
    if not lines:
        lines = ["(No content)"]
    
    clips = []
    start_time = 0.0
    for line in lines:
        if start_time >= total_duration:
            break
        
        word_count = len(line.split())
        line_duration = max(3.0, min(word_count * 0.4, total_duration - start_time))
        end_time = start_time + line_duration
        
        try:
            txt_clip = TextClip(
                line,
                font="Arial-Bold",
                fontsize=56,
                color="white",
                size=(1920 - 200, None),
                method="caption"
            ).set_position(("center", 850))
        except:
            txt_clip = TextClip(
                line,
                fontsize=50,
                color="white",
                size=(1920 - 200, None),
                method="caption"
            ).set_position(("center", 850))
        
        txt_clip = txt_clip.set_start(start_time).set_duration(line_duration)
        clips.append(txt_clip)
        start_time = end_time
    
    background = ColorClip(size=(1920, 1080), color=(0,0,0), duration=total_duration)
    final_video = CompositeVideoClip([background] + clips)
    final_video = final_video.set_audio(audio).set_duration(total_duration)
    
    final_video.write_videofile(
        output_path,
        fps=24,
        audio_codec="aac",
        temp_audiofile=str(Path(output_path).with_suffix(".m4a")),
        remove_temp=True,
        logger=None,
        threads=4
    )
    return output_path