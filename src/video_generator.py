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
from src.utils import setup_logging
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

def get_all_images_from_folder(folder_path: Path) -> list:
    """
    Klasördeki TÜM görselleri bulur (1.png, 2.png, 3.png... şeklinde).
    Args:
        folder_path: Klasör yolu
    Returns:
        list: Görsel yolları listesi (sıralı)
    """
    image_paths = []
    index = 1
    
    # 1.png'den başla, dosya bulunana kadar devam et
    while True:
        img_path = folder_path / f"{index}.png"
        if img_path.exists():
            image_paths.append(str(img_path))
            logger.debug(f"🖼️ Görsel bulundu: {img_path}")
            index += 1
        else:
            # Dosya yoksa döngüyü bitir
            logger.info(f"✅ Toplam {len(image_paths)} görsel bulundu ({folder_path.name}/)")
            break
        
        # Güvenlik: Maksimum 100 görsel
        if index > 100:
            logger.warning(f"⚠️ Maksimum görsel sayısına ulaşıldı (100)")
            break
    
    return image_paths

# ====================== PODCAST İÇİN ÖZEL KEN BURNS SİSTEMİ ======================

def create_podcast_bg_with_timed_effects(image_paths, total_duration, width, height):
    """
    Podcast için zamanlamalı Ken Burns efekti:
    - 0-5 dk: Sürekli Ken Burns
    - 5-9 dk: 30sn efekt VAR, 30sn efekt YOK
    - 9+ dk: Efektsiz (statik)
    - Her görsel 25 sn ekranda kalır
    - Görseller başa döner (loop)
    """
    clips = []
    elapsed = 0.0
    image_index = 0
    
    # Görsel yoksa siyah ekran
    if not image_paths:
        logger.warning("⚠️ Podcast görseli bulunamadı → Siyah arka plan")
        return ColorClip((width, height), (0, 0, 0)).set_duration(total_duration)
    
    while elapsed < total_duration:
        # Görsel index'i loop yap (başa dön)
        if image_index >= len(image_paths):
            image_index = 0
            logger.info("🔄 Podcast görselleri başa döndü (loop)")
        
        img_path = image_paths[image_index]
        
        # Her görsel 25 saniye ekranda kalır
        remaining_time = total_duration - elapsed
        clip_duration = min(25.0, remaining_time)
        
        if Path(img_path).exists():
            logger.info(f"🖼️ Podcast görseli #{image_index + 1}: {Path(img_path).name} ({elapsed:.1f}s - {elapsed + clip_duration:.1f}s)")
            
            # Görseli yükle ve boyutlandır
            clip = ImageClip(str(img_path))
            clip_ratio = clip.w / clip.h
            target_ratio = width / height
            
            if clip_ratio > target_ratio:
                clip = clip.resize(height=height)
            else:
                clip = clip.resize(width=width)
            
            # Ken Burns efekti zamanlaması
            if elapsed < 300:  # 0-5 dk: Sürekli Ken Burns
                clip = clip.set_duration(clip_duration).resize(
                    lambda t: 1 + 0.02 * (t / clip_duration)
                ).set_position('center')
                
            elif elapsed < 540:  # 5-9 dk: 30sn efekt VAR, 30sn efekt YOK
                cycle_position = (elapsed - 300) % 60  # 0-60 sn arası döngü
                
                if cycle_position < 30:  # İlk 30sn: Ken Burns VAR
                    clip = clip.set_duration(clip_duration).resize(
                        lambda t: 1 + 0.02 * (t / clip_duration)
                    ).set_position('center')
                else:  # Son 30sn: Ken Burns YOK (statik)
                    clip = clip.set_duration(clip_duration).set_position('center')
                    
            else:  # 9+ dk: Efektsiz (statik)
                clip = clip.set_duration(clip_duration).set_position('center')
            
            clips.append(clip)
            elapsed += clip_duration
            image_index += 1
        else:
            logger.warning(f"⚠️ Görsel bulunamadı: {img_path}")
            clips.append(ColorClip((width, height), (0, 0, 0)).set_duration(clip_duration))
            elapsed += clip_duration
            image_index += 1
    
    return concatenate_videoclips(clips).set_duration(total_duration)

# ====================== SHORTS İÇİN ÖZEL CANLI EFEKT SİSTEMİ ======================

def create_shorts_bg_with_live_effect(image_paths, total_duration, width, height):
    """
    Shorts için canlı efekt sistemi:
    - Her görsel 5.5 sn ekranda kalır
    - 1. görsel: Ken Burns YOK (statik)
    - 2.+ görseller: Ken Burns VAR
    - Görseller başa DÖNMEZ (son görsel video sonuna kadar kalır)
    """
    clips = []
    elapsed = 0.0
    image_index = 0
    
    # Görsel yoksa siyah ekran
    if not image_paths:
        logger.warning("⚠️ Shorts görseli bulunamadı → Siyah arka plan")
        return ColorClip((width, height), (0, 0, 0)).set_duration(total_duration)
    
    while elapsed < total_duration:
        # Son görseldeyiz ve video bitmek üzere → başa DÖNME (son görseli uzat)
        if image_index >= len(image_paths):
            # Son görseli video sonuna kadar uzat
            remaining_time = total_duration - elapsed
            if remaining_time > 0:
                last_img_path = image_paths[-1]
                logger.info(f"🖼️ Shorts son görsel uzatılıyor: {Path(last_img_path).name} ({remaining_time:.1f}s)")
                
                clip = ImageClip(str(last_img_path))
                clip_ratio = clip.w / clip.h
                target_ratio = width / height
                
                if clip_ratio > target_ratio:
                    clip = clip.resize(height=height)
                else:
                    clip = clip.resize(width=width)
                
                # Son görsel de Ken Burns ile (çünkü 1. değil)
                if len(image_paths) > 1:
                    clip = clip.set_duration(remaining_time).resize(
                        lambda t: 1 + 0.03 * (t / remaining_time)
                    ).set_position('center')
                else:
                    clip = clip.set_duration(remaining_time).set_position('center')
                
                clips.append(clip)
                elapsed += remaining_time
            break
        
        img_path = image_paths[image_index]
        
        # Her görsel 5.5 saniye ekranda kalır
        remaining_time = total_duration - elapsed
        clip_duration = min(5.5, remaining_time)
        
        if Path(img_path).exists():
            logger.info(f"🖼️ Shorts görseli #{image_index + 1}: {Path(img_path).name} ({elapsed:.1f}s - {elapsed + clip_duration:.1f}s)")
            
            # Görseli yükle ve boyutlandır
            clip = ImageClip(str(img_path))
            clip_ratio = clip.w / clip.h
            target_ratio = width / height
            
            if clip_ratio > target_ratio:
                clip = clip.resize(height=height)
            else:
                clip = clip.resize(width=width)
            
            # 1. görsel: Ken Burns YOK, diğerleri: Ken Burns VAR
            if image_index == 0:
                # İlk görsel statik
                clip = clip.set_duration(clip_duration).set_position('center')
                logger.debug(f"  → İlk görsel: Statik (Ken Burns YOK)")
            else:
                # Diğer görseller: Ken Burns efekti
                clip = clip.set_duration(clip_duration).resize(
                    lambda t: 1 + 0.03 * (t / clip_duration)
                ).set_position('center')
                logger.debug(f"  → Görsel #{image_index + 1}: Ken Burns VAR")
            
            clips.append(clip)
            elapsed += clip_duration
            image_index += 1
        else:
            logger.warning(f"⚠️ Görsel bulunamadı: {img_path}")
            clips.append(ColorClip((width, height), (0, 0, 0)).set_duration(clip_duration))
            elapsed += clip_duration
            image_index += 1
    
    return concatenate_videoclips(clips).set_duration(total_duration)

# ====================== METİN GÖRSEL OLUŞTURUCU ======================

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
        # Shorts için ortalanmış metin (tek satır)
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
        y = (height - (bbox[3] - bbox[1])) // 2 - 50
        
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
        # Podcast için alt metin (maks 3 satır)
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
        y_offset = height - 350
        
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

# ====================== ANA VİDEO ÜRETİM FONKSİYONU ======================

def create_video_with_chunks(script, output_path, is_shorts=True):
    """
    Video üretim fonksiyonu - özel Ken Burns zamanlaması ile.
    
    Args:
        script (str): Üretilecek metin
        output_path (str): Çıktı video yolu
        is_shorts (bool): Shorts mı podcast mi?
    """
    logger.info(f"🎥 {'Shorts' if is_shorts else 'Podcast'} videosu üretiliyor (Dinamik görsel tarama)...")
    
    # Geçici dizin oluştur
    with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
        temp_path = Path(temp_dir)
        audio_path = temp_path / "audio.mp3"
        
        # SESLİNDİRME
        asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
        audio = AudioFileClip(str(audio_path))
        total_duration = min(audio.duration, Config.MAX_SHORTS_DURATION if is_shorts else Config.MAX_PODCAST_DURATION)
        
        # Arka plan sesi ekle
        bg_audio_path = Config.DATA_DIR / "1.mp3"
        if bg_audio_path.exists():
            bg_audio = AudioFileClip(str(bg_audio_path))
            if bg_audio.duration < total_duration:
                loops_needed = int(total_duration // bg_audio.duration) + 1
                bg_audio = concatenate_audioclips([bg_audio] * loops_needed)
            bg_audio = bg_audio.subclip(0, total_duration)
            bg_audio = bg_audio.volumex(0.1)
            combined_audio = CompositeAudioClip([audio, bg_audio])
        else:
            combined_audio = audio
        
        # Video boyutları
        width, height = (1080, 1920) if is_shorts else (1920, 1080)
        
        # 👇 DİNAMİK GÖRSEL TARAMA
        if is_shorts:
            # Shorts görselleri: sor klasörü
            sor_folder = Config.DATA_DIR / "images" / "sor"
            image_paths = get_all_images_from_folder(sor_folder)
        else:
            # Podcast görselleri: pod klasörü
            pod_folder = Config.DATA_DIR / "images" / "pod"
            image_paths = get_all_images_from_folder(pod_folder)

        # 👇 ÖZEL KEN BURNS ZAMANLAMASI
        if is_shorts:
            background = create_shorts_bg_with_live_effect(image_paths, total_duration, width, height)
        else:
            background = create_podcast_bg_with_timed_effects(image_paths, total_duration, width, height)
        
        # Yarı şeffaf overlay
        overlay = ColorClip((width, height), (0, 0, 0)).set_duration(total_duration).set_opacity(0.3)
        
        # Metni parçalara böl (ses-yazı uyumu)
        words = script.split()
        text_clips = []
        start_time = 0.0
        
        avg_word_duration = total_duration / len(words) if words else 0.3
        words_per_line = 4 if is_shorts else 8
        
        for i in range(0, len(words), words_per_line):
            if start_time >= total_duration:
                break
            
            line_words = words[i:i + words_per_line]
            line_text = " ".join(line_words)
            
            if not line_text.strip():
                continue
            
            line_duration = len(line_words) * avg_word_duration
            line_duration = max(1.0, min(line_duration, total_duration - start_time))
            
            text_img = create_text_image(line_text, width, height, is_shorts)
            img_path = temp_path / f"text_{start_time:.1f}.png"
            text_img.save(str(img_path))
            
            txt_clip = (ImageClip(str(img_path), duration=line_duration, transparent=True)
                        .set_start(start_time)
                        .set_position('center' if is_shorts else ('center', 'bottom')))
            
            text_clips.append(txt_clip)
            start_time += line_duration
        
        # Final videoyu birleştir
        final_video = CompositeVideoClip([background, overlay] + text_clips).set_audio(combined_audio).set_duration(total_duration)
        
        # Videoyu yaz
        codec = "h264_nvenc" if _is_nvidia_gpu() else "libx264"
        preset = "fast" if _is_nvidia_gpu() else "ultrafast"
        
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
        
        output_file_path = Path(output_path)
        logger.info(f"📊 Video boyutu: {output_file_path.stat().st_size / (1024*1024):.2f} MB")


def create_shorts_video(audio_path: str, script: str, output_path: str):
    """Geriye uyumluluk için - yeni fonksiyona yönlendirir."""
    logger.info(f"🎥 Shorts videosu üretiliyor (Canlı efekt sistemi)...")
    create_video_with_chunks(script, output_path, is_shorts=True)

def create_podcast_video(audio_path: str, script: str, output_path: str):
    """Geriye uyumluluk için - yeni fonksiyona yönlendirir."""
    logger.info(f"🎥 Podcast videosu üretiliyor (Zamanlamalı Ken Burns)...")
    create_video_with_chunks(script, output_path, is_shorts=False)
