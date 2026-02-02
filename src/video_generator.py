# src/video_generator.py
import os
import tempfile
import shutil
import multiprocessing
import asyncio
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ColorClip, CompositeVideoClip, AudioFileClip, ImageClip, concatenate_videoclips, CompositeAudioClip, concatenate_audioclips
)
from src.config import Config
from src.utils import setup_logging, get_current_index
from src.tts import generate_voice_with_edge_tts

logger = setup_logging()
CORES = multiprocessing.cpu_count()
FPS = 24  # Sabit FPS

def clean_text(text: str) -> str:
    """Unicode karakterleri temizler."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')

def _is_nvidia_gpu() -> bool:
    """NVIDIA GPU var mı kontrol eder."""
    try:
        import subprocess
        result = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except:
        return False

def create_shorts_bg(image_list, total_duration, width, height):
    """Shorts için çoklu görsel arka plan oluşturur (Ken Burns efektiyle)."""
    clips = []
    duration_per_img = 10.0
    elapsed = 0.0

    for i, img_path in enumerate(image_list):
        if elapsed >= total_duration: 
            break

        # Son görselse kalan süreyi al, değilse 10 saniye
        current_clip_dur = (total_duration - elapsed) if i == len(image_list) - 1 else min(duration_per_img, total_duration - elapsed)

        if Path(img_path).exists():
            logger.info(f"🖼️ Shorts görseli kullanılıyor: {img_path}")
            # 👇 PIL hata düzeltmesi - Image.ANTIALIAS yerine Image.LANCZOS
            clip = ImageClip(str(img_path))
            # Oranı koru
            clip_ratio = clip.w / clip.h
            target_ratio = width / height
            
            if clip_ratio > target_ratio:
                clip = clip.resize(height=height)
            else:
                clip = clip.resize(width=width)
            
            # Zoom efekti - PIL hata düzeltmesi
            clip = (clip.set_duration(current_clip_dur)
                    .resize(lambda t: 1 + 0.03 * (t / current_clip_dur))  # Daha yavaş zoom
                    .set_position('center'))
            clips.append(clip)
            elapsed += current_clip_dur
        else:
            logger.warning(f"⚠️ Shorts görseli bulunamadı: {img_path}")
            clips.append(ColorClip((width, height), (0, 0, 0)).set_duration(current_clip_dur))
            elapsed += current_clip_dur

    if not clips:
        logger.warning("⚠️ Hiç shorts görseli bulunamadı → Siyah arka plan")
        return ColorClip((width, height), (0, 0, 0)).set_duration(total_duration)
    
    return concatenate_videoclips(clips).set_duration(total_duration)

def create_fast_active_bg(bg_path, total_duration, width, height):
    """Podcast için tek görsel arka plan oluşturur (Ken Burns efektiyle)."""
    # 👇 None kontrolü eklendi
    if bg_path is None or not Path(str(bg_path)).exists():
        logger.warning(f"⚠️ Görsel bulunamadı → Siyah arka plan: {bg_path}")
        return ColorClip((width, height), (0, 0, 0)).set_duration(total_duration)

    logger.info(f"🖼️ Görsel kullanılıyor: {bg_path}")
    
    img = ImageClip(str(bg_path))
    # Oranı koru
    img_ratio = img.w / img.h
    target_ratio = width / height
    
    if img_ratio > target_ratio:
        img = img.resize(height=height)
    else:
        img = img.resize(width=width)
    
    zoom_dur = min(60, total_duration)
    static_dur = max(0, total_duration - zoom_dur)
    
    active_part = img.set_duration(zoom_dur).resize(lambda t: 1 + 0.02 * (t / zoom_dur))
    if static_dur > 0:
        static_part = img.set_duration(static_dur).resize(1.02)
        return concatenate_videoclips([active_part, static_part]).set_position('center')
    
    return active_part.set_position('center')

def create_text_image(text, width, height, is_shorts):
    """Metni şeffaf arka planlı görsel olarak oluşturur."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Font boyutları
    fontsize = 72 if is_shorts else 60
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", fontsize)
    except OSError:
        try:
            font = ImageFont.truetype("Arial-Bold.ttf", fontsize)
        except OSError:
            font = ImageFont.load_default()

    text = clean_text(text)
    
    if is_shorts:
        # Shorts için ortalanmış metin
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] < width * 0.85:
                current_line = test
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Tüm metni ortala
        full_text = "\n".join(lines)
        bbox = draw.multiline_textbbox((0, 0), full_text, font=font, align="center")
        x = (width - (bbox[2] - bbox[0])) // 2
        y = (height - (bbox[3] - bbox[1])) // 2 - 50  # Ekranın ortasından biraz yukarı
        
        draw.multiline_text(
            (x, y), 
            full_text, 
            font=font, 
            fill="white", 
            stroke_width=3, 
            stroke_fill="black",
            align="center"
        )
    else:
        # Podcast için alt metin
        max_width = width - 200
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            test_line = current_line + (" " + word if current_line else word)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # En fazla 3 satır göster
        lines = lines[:3]
        y_offset = height - 350  # Ekranın alt kısmından
        
        for line in lines:
            draw.text(
                (150, y_offset), 
                line, 
                font=font, 
                fill="white", 
                stroke_width=2, 
                stroke_fill="black"
            )
            y_offset += fontsize + 10

    return img

def create_video_with_chunks(script, output_path, is_shorts=True):
    """
    Yeni video üretim fonksiyonu - metni akıcı parçalara bölerek render eder + arka plan sesi ekler.
    
    Args:
        script (str): Üretilecek metin
        output_path (str): Çıktı video yolu
        is_shorts (bool): Shorts mı podcast mi?
    """
    logger.info(f"🎥 {'Shorts' if is_shorts else 'Podcast'} videosu üretiliyor (Yeni algoritma + arka plan sesi)...")
    
    # Geçici dizin oluştur
    with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
        temp_path = Path(temp_dir)
        audio_path = temp_path / "audio.mp3"
        
        # SESLİNDİRME BURADA ÇAĞRILIYOR
        asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
        audio = AudioFileClip(str(audio_path))
        total_duration = min(audio.duration, Config.SHORTS_DURATION if is_shorts else Config.PODCAST_DURATION)
        
        # Arka plan sesi ekle
        bg_audio_path = Config.DATA_DIR / "1.mp3"  # Odun ateşi sesi
        if bg_audio_path.exists():
            bg_audio = AudioFileClip(str(bg_audio_path))
            # Arka plan sesini loop yap
            if bg_audio.duration < total_duration:
                loops_needed = int(total_duration // bg_audio.duration) + 1
                bg_audio = concatenate_audioclips([bg_audio] * loops_needed)
            # Sessizliği kırp
            bg_audio = bg_audio.subclip(0, total_duration)
            # Ses seviyesini %10 yap
            bg_audio = bg_audio.volumex(0.1)  # 👈 ARKA PLAN SES SEVİYESİ
            # Ana sesle birleştir
            combined_audio = CompositeAudioClip([audio, bg_audio])
        else:
            # Arka plan sesi yoksa sadece ana ses
            combined_audio = audio
        
        # Video boyutları
        width, height = (1080, 1920) if is_shorts else (1920, 1080)
        
        # Görsel listesini hazırla
        current_index = get_current_index()
        image_paths = []
        
        if is_shorts:
            # Shorts görselleri: sor klasörü
            # Önce çoklu: 1_1.png, 1_2.png, 1_3.png
            for i in range(1, 6):  # En fazla 5 görsel dene
                img_path = Config.DATA_DIR / "images" / "sor" / f"{current_index}_{i}.png"
                if img_path.exists():
                    image_paths.append(str(img_path))
            
            # Çoklu yoksa tek: 1.png
            if not image_paths:
                img_path = Config.DATA_DIR / "images" / "sor" / f"{current_index}.png"
                if img_path.exists():
                    image_paths = [str(img_path)]
            
            # Hala yoksa alternatifler
            if not image_paths:
                for idx in [current_index - 1, current_index + 1, 1]:  # önceki, sonraki, default 1
                    img_path = Config.DATA_DIR / "images" / "sor" / f"{idx}.png"
                    if img_path.exists():
                        image_paths = [str(img_path)]
                        break
        else:
            # Podcast görseli: pod klasörü (tek görsel)
            img_path = Config.DATA_DIR / "images" / "pod" / f"{current_index}.png"
            
            # Alternatif arama
            if not img_path.exists():
                for idx in [current_index - 1, current_index + 1, 1]:  # önceki, sonraki, default 1
                    alt_path = Config.DATA_DIR / "images" / "pod" / f"{idx}.png"
                    if alt_path.exists():
                        img_path = alt_path
                        break
            
            if img_path.exists():
                image_paths = [str(img_path)]

        # Arka plan oluştur
        if is_shorts:
            background = create_shorts_bg(image_paths, total_duration, width, height)
        else:
            bg_path = image_paths[0] if image_paths else None
            background = create_fast_active_bg(bg_path, total_duration, width, height)
        
        # Yarı şeffaf overlay
        overlay = ColorClip((width, height), (0, 0, 0)).set_duration(total_duration).set_opacity(0.3)
        
        # Metni parçalara böl
        words = script.split()
        chunk_size = 4 if is_shorts else 50
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        
        text_clips = []
        start_time = 0.0
        
        # Her parça için süre hesapla
        avg_word_duration = total_duration / len(words) if words else 0.3
        for chunk in chunks:
            if start_time >= total_duration:
                break
                
            # Kelime sayısına göre süre hesapla
            word_count = len(chunk.split())
            chunk_duration = max(1.5, min(word_count * avg_word_duration * 1.2, total_duration - start_time))
            
            # Metin görselini oluştur
            text_img = create_text_image(chunk, width, height, is_shorts)
            img_path = temp_path / f"text_{start_time:.1f}.png"
            text_img.save(str(img_path))
            
            # Text clip oluştur
            txt_clip = (ImageClip(str(img_path), duration=chunk_duration, transparent=True)
                        .set_start(start_time)
                        .set_position('center' if is_shorts else ('center', 'bottom')))
            
            text_clips.append(txt_clip)
            start_time += chunk_duration
        
        # Final videoyu birleştir
        final_video = CompositeVideoClip([background, overlay] + text_clips).set_audio(combined_audio).set_duration(total_duration)
        
        # Videoyu yaz (MoviePy 1.0.3 uyumlu parametreler)
        codec = "h264_nvenc" if _is_nvidia_gpu() else "libx264"
        preset = "fast" if _is_nvidia_gpu() else "ultrafast"  # Daha uyumlu preset
        
        final_video.write_videofile(
            str(output_path),
            fps=FPS,
            codec=codec,
            audio_codec="aac",
            threads=CORES,
            preset=preset,
            logger=None
        )
        
        logger.info(f"✅ Video hazır: {output_path}")
        
        # 👇 STRING PATH'I PATH OBJESİNE ÇEVİR
        output_file_path = Path(output_path)
        logger.info(f"📊 Video boyutu: {output_file_path.stat().st_size / (1024*1024):.2f} MB")


def create_shorts_video(audio_path: str, script: str, output_path: str):
    """Geriye uyumluluk için - yeni fonksiyona yönlendirir."""
    logger.info(f"🎥 Shorts videosu üretiliyor (Yeni algoritma)...")
    
    # Sadece video üretimi yap (ses zaten mevcut)
    create_video_with_chunks(script, output_path, is_shorts=True)

def create_podcast_video(audio_path: str, script: str, output_path: str):
    """Geriye uyumluluk için - yeni fonksiyona yönlendirir."""
    logger.info(f"🎥 Podcast videosu üretiliyor (Yeni algoritma)...")
    
    create_video_with_chunks(script, output_path, is_shorts=False)
