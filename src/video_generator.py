# src/video_generator.py 
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ColorClip, CompositeVideoClip, AudioFileClip, ImageClip
from src.config import Config

def create_shorts_video(audio_path: str, script: str, output_path: str):
    logger.info("🎥 Shorts videosu üretiliyor...")
    
    # 1. Ses ve süre
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, Config.SHORTS_DURATION)
    
    # 2. Arka plan: GÖRSEL veya siyah ekran
    width, height = 1080, 1920  # Dikey Shorts formatı
    
    # GÜN SAYISINI OKU
    current_index = 1
    if Config.SIDEA_FILE.exists():
        try:
            with open(Config.SIDEA_FILE, "r") as f:
                # sidea.txt = bugünkü konunun indeksi (1 tabanlı)
                current_index = int(f.read().strip())
        except:
            current_index = 1

    # GÖRSEL YOLU
    image_path = Config.DATA_DIR / "images" / f"{current_index}.png"
    
    if image_path.exists():
        logger.info(f"🖼️ Görsel kullanılıyor: {image_path}")
        from PIL import Image as PilImage
        def resize_frame(frame):
            img = PilImage.fromarray(frame)
            return np.array(img.resize((width, height), PilImage.LANCZOS))
        
        background = ImageClip(str(image_path))
        background = background.fl_image(resize_frame).set_duration(total_duration)
    else:
        logger.warning(f"⚠️ Görsel bulunamadı: {image_path} → Siyah arka plan kullanılıyor")
        background = ColorClip((width, height), (0, 0, 0), duration=total_duration)

    # 3. METİN BÖLME + YAZI BOYUTU (10x BÜYÜK!)
    lines = script.split(". ")
    text_clips = []
    start_time = 0.0

    for line in lines:
        if start_time >= total_duration:
            break
        
        word_count = len(line.split())
        duration = max(2.0, min(word_count * 0.4, total_duration - start_time))
        
        # 🎯 YAZI BOYUTU: EN AZ 80px (önceki: 60 → küçük kalıyordu)
        try:
            txt_clip = TextClip(
                line,
                font="Arial-Bold",
                fontsize=80,  # 🧨 10 KAT BÜYÜK!
                color="white",
                size=(width - 150, None),
                method="caption",
                stroke_color="black",
                stroke_width=2
            ).set_position(("center", height - 400))
        except:
            txt_clip = TextClip(
                line,
                fontsize=80,  # 🧨
                color="white",
                size=(width - 150, None),
                method="caption"
            ).set_position(("center", height - 400))

        txt_clip = txt_clip.set_start(start_time).set_duration(duration)
        text_clips.append(txt_clip)
        start_time += duration

    # 4. BİRLEŞTİR
    final_video = CompositeVideoClip([background] + text_clips)
    final_video = final_video.set_audio(audio).set_duration(total_duration)
    
    final_video.write_videofile(
        str(output_path),
        fps=24,
        audio_codec="aac",
        temp_audiofile=str(Path(output_path).with_suffix(".m4a")),
        remove_temp=True,
        logger=None,
        threads=4
    )
    
    logger.info(f"✅ Shorts videosu hazır: {output_path}")


def create_podcast_video(audio_path: str, script: str, output_path: str):
    logger.info("🎥 Podcast videosu üretiliyor...")
    
    # 1. Ses ve süre
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, Config.PODCAST_DURATION)  # 15 dk
    
    # 2. Arka plan: HER ZAMAN SİYAH (görsel yok)
    width, height = 1920, 1080
    background = ColorClip((width, height), (0, 0, 0), duration=total_duration)

    # 3. METİN BÖLME + YAZI BOYUTU
    lines = script.split(". ")
    text_clips = []
    start_time = 0.0

    for line in lines:
        if start_time >= total_duration:
            break
        
        word_count = len(line.split())
        duration = max(3.0, min(word_count * 0.5, total_duration - start_time))
        
        # 🎯 YAZI BOYUTU: 64px → 90px (okunaklı)
        try:
            txt_clip = TextClip(
                line,
                font="Arial-Bold",
                fontsize=90,  # 🧨 BÜYÜTÜLDÜ
                color="white",
                size=(width - 200, None),
                method="caption",
                stroke_color="black",
                stroke_width=2
            ).set_position(("center", height - 300))
        except:
            txt_clip = TextClip(
                line,
                fontsize=90,  # 🧨
                color="white",
                size=(width - 200, None),
                method="caption"
            ).set_position(("center", height - 300))

        txt_clip = txt_clip.set_start(start_time).set_duration(duration)
        text_clips.append(txt_clip)
        start_time += duration

    # 4. BİRLEŞTİR
    final_video = CompositeVideoClip([background] + text_clips)
    final_video = final_video.set_audio(audio).set_duration(total_duration)
    
    final_video.write_videofile(
        str(output_path),
        fps=24,
        audio_codec="aac",
        temp_audiofile=str(Path(output_path).with_suffix(".m4a")),
        remove_temp=True,
        logger=None,
        threads=4
    )
    
    logger.info(f"✅ Podcast videosu hazır: {output_path}")
