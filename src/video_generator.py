# src/video_generator.py
import os
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ColorClip, CompositeVideoClip, AudioFileClip
from src.config import Config
from src.utils import setup_logging, split_script_into_chunks

logger = setup_logging()

def create_text_image(text: str, width: int, height: int, font_size: int = 70, color: str = "white") -> Image.Image:
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

def create_shorts_video(audio_path: str, script: str, output_path: str):
    """1 dakikalık Shorts videosu üretir (dikey format)."""
    logger.info("🎥 Shorts videosu üretiliyor...")
    
    # 1. Ses süresini al
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, Config.SHORTS_DURATION)  # 60 sn
    
    # 2. Metni kır
    lines = split_script_into_chunks(script, max_chars=80)
    if not lines:
        lines = ["(No content)"]
    
    # 3. Arka plan (SD görseli) - SHORTS İÇİN DİKEY FORMAT
    width, height = 1080, 1920  # Dikey (Shorts formatı)
    
    # SD görselini yükle (varsa)
    sd_background_path = "sd_background.jpg"
    if os.path.exists(sd_background_path):
        from moviepy.editor import ImageClip
        # Eski sürümde ANTIALIAS hatası veriyor, resize ederken dikkatli ol
        try:
            background = ImageClip(sd_background_path).resize((width, height)).set_duration(total_duration)
        except:
            # Hata durumunda siyah arka plan
            background = ColorClip(size=(width, height), color=(0, 0, 0), duration=total_duration)
    else:
        # Yoksa siyah arka plan
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
        
        # Pillow ile metin görseli oluştur (BÜYÜK YAZI!)
        text_img = create_text_image(line, width, height, font_size=70, color="white")
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
    total_duration = min(audio.duration, Config.PODCAST_DURATION)  # 900 sn (15 dk)
    
    # 2. Metni kır
    lines = split_script_into_chunks(script, max_chars=110)
    if not lines:
        lines = ["(No content)"]
    
    # 3. Arka plan (siyah) - PODCAST İÇİN YATAY FORMAT
    width, height = 1920, 1080  # Full HD
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
        
        # Pillow ile metin görseli oluştur (BÜYÜK YAZI!)
        text_img = create_text_image(line, width, height, font_size=70, color="white")
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
