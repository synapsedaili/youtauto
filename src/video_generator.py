# src/video_generator.py
import os
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ColorClip, CompositeVideoClip, AudioFileClip
import numpy as np
from src.config import Config
from src.utils import setup_logging, sanitize_filename

logger = setup_logging()

def create_text_image(text: str, width: int, height: int, font_size: int = 50, color: str = "white") -> Image.Image:
    """Pillow ile metin içeren bir görsel oluştur."""
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Metni ortala
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, font=font, fill=color)
    return img

def split_script_into_chunks(script: str, max_chars=120) -> list:
    """Metni ekran sığacak şekilde kırpar."""
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

def create_shorts_video(audio_path: str, script: str, output_path: str):
    """1 dakikalık Shorts videosu üretir (dikey format)."""
    logger.info("🎥 Shorts videosu üretiliyor...")
    
    # 1. Ses süresini al
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, Config.SHORTS_DURATION)
    
    # 2. Metni kır
    lines = split_script_into_chunks(script, max_chars=80)
    if not lines:
        lines = ["(No content)"]
    
    # 3. Arka plan (siyah) - SHORTS İÇİN DİKEY FORMAT
    width, height = 1080, 1920  # Dikey (Shorts formatı)
    background = ColorClip(size=(width, height), color=(0, 0, 0), duration=total_duration)
    
    # 4. Metin görselleri oluştur
    text_clips = []
    start_time = 0.0
    for line in lines:
        if start_time >= total_duration:
            break
        
        # Satır süresi
        word_count = len(line.split())
        duration = max(1.5, min(word_count * 0.35, total_duration - start_time))
        end_time = start_time + duration
        
        # Pillow ile metin görseli oluştur
        text_img = create_text_image(line, width, height, font_size=60, color="white")
        text_img_path = f"/tmp/temp_text_{hash(line)}.png"
        text_img.save(text_img_path)
        
        # Pillow görselini MoviePy ile kullan
        from moviepy.editor import ImageClip
        txt_clip = ImageClip(text_img_path).set_duration(duration).set_start(start_time)
        
        text_clips.append(txt_clip)
        start_time = end_time
    
    # 5. ARKA PLAN + METİN GÖRSELLERİNİ BİRLEŞTİR
    all_clips = [background] + text_clips
    final_video = CompositeVideoClip(all_clips)
    final_video = final_video.set_audio(audio).set_duration(total_duration)
    
    # 6. Kaydet
    final_video.write_videofile(
        output_path,
        fps=24,
        audio_codec="aac",
        temp_audiofile=str(Path(output_path).with_suffix(".m4a")),
        remove_temp=True,
        logger=None,
        threads=4
    )
    
    logger.info(f"✅ Shorts videosu hazır: {output_path}")
    return output_path

def create_podcast_video(audio_path: str, script: str, output_path: str):
    """15 dakikalık podcast videosu üretir (yatay format)."""
    logger.info("🎥 Podcast videosu üretiliyor...")
    
    # 1. Ses süresini al
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, Config.PODCAST_DURATION)
    
    # 2. Metni kır
    lines = split_script_into_chunks(script, max_chars=110)
    if not lines:
        lines = ["(No content)"]
    
    # 3. Arka plan (siyah) - PODCAST İÇİN YATAY FORMAT
    width, height = 1920, 1080  # Yatay (Full HD)
    background = ColorClip(size=(width, height), color=(0, 0, 0), duration=total_duration)
    
    # 4. Metin görselleri oluştur
    text_clips = []
    start_time = 0.0
    for line in lines:
        if start_time >= total_duration:
            break
        
        # Satır süresi
        word_count = len(line.split())
        duration = max(3.0, min(word_count * 0.4, total_duration - start_time))
        end_time = start_time + duration
        
        # Pillow ile metin görseli oluştur
        text_img = create_text_image(line, width, height, font_size=56, color="white")
        text_img_path = f"/tmp/temp_text_{hash(line)}.png"
        text_img.save(text_img_path)
        
        # Pillow görselini MoviePy ile kullan
        from moviepy.editor import ImageClip
        txt_clip = ImageClip(text_img_path).set_duration(duration).set_start(start_time)
        
        text_clips.append(txt_clip)
        start_time = end_time
    
    # 5. ARKA PLAN + METİN GÖRSELLERİNİ BİRLEŞTİR
    all_clips = [background] + text_clips
    final_video = CompositeVideoClip(all_clips)
    final_video = final_video.set_audio(audio).set_duration(total_duration)
    
    # 6. Kaydet
    final_video.write_videofile(
        output_path,
        fps=24,
        audio_codec="aac",
        temp_audiofile=str(Path(output_path).with_suffix(".m4a")),
        remove_temp=True,
        logger=None,
        threads=4
    )
    
    logger.info(f"✅ Podcast videosu hazır: {output_path}")
    return output_path
