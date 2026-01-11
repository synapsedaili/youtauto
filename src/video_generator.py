# src/video_generator.py
import os
import tempfile
import multiprocessing
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ColorClip, CompositeVideoClip, AudioFileClip, ImageClip, concatenate_videoclips
)
from src.config import Config
from src.utils import setup_logging, get_current_index

logger = setup_logging()

CORES = multiprocessing.cpu_count()
logger.info(f"⚙️ CPU Çekirdek Sayısı: {CORES}")

def _is_nvidia_gpu() -> bool:
    try:
        import subprocess
        result = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except:
        return False

def clean_text(text: str) -> str:
    """Unicode karakterleri ASCII’ye çevirir."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ascii', 'ignore').decode('ascii')

def _create_text_image(text: str, width: int, height: int, fontsize: int, is_shorts: bool) -> Image.Image:
    # ŞEFFAF ARKA PLAN
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # RGBA → şeffaf
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", fontsize)
    except OSError:
        try:
            font = ImageFont.truetype("Arial.ttf", fontsize)
        except OSError:
            font = ImageFont.load_default()

    text = clean_text(text)
    max_width = width - (150 if is_shorts else 200)
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

    y_offset = height - 400 if is_shorts else height - 300
    for line in lines[:3]:
        # Sadece beyaz yazı + siyah gölge
        draw.text((52, y_offset+2), line, font=font, fill=(0, 0, 0, 128))  # Gölgе
        draw.text((50, y_offset), line, font=font, fill=(255, 255, 255, 255))  # Yazı
        y_offset += fontsize + 10

    return img

def _create_text_clips(script: str, width: int, height: int, is_shorts: bool, duration: float) -> list:
    """Metni zaman damgalarına göre TextClip/ImageClip listesi haline getirir."""
    lines = script.split(". ")
    text_clips = []
    start_time = 0.0
    fontsize = 48 if is_shorts else 64
    max_words = 8 if is_shorts else 180
    words = line.split()[:max_words]
    line = " ".join(words)
  
    for line in lines:
        if start_time >= duration:
            break

        word_count = len(line.split())
        seg_duration = max(2.0 if is_shorts else 3.0, min(word_count * (0.4 if is_shorts else 0.5), duration - start_time))

        try:
            from moviepy.video.tools.subtitles import TextClip
            txt_clip = TextClip(
                line,
                font="Arial-Bold",
                fontsize=fontsize,
                color="white",
                size=(width - 150 if is_shorts else width - 200, None),
                method="caption",
                stroke_color="black",
                stroke_width=2
            ).set_position(("center", "bottom"))  # 👈 YAZI ALT KISIMDA
        except Exception:
            img = _create_text_image(line, width, height, fontsize, is_shorts)
            txt_clip = ImageClip(np.array(img), duration=seg_duration)
            txt_clip = txt_clip.set_position(("center", "bottom"))  

        txt_clip = txt_clip.set_start(start_time).set_duration(seg_duration)
        text_clips.append(txt_clip)
        start_time += seg_duration

    return text_clips

def _get_script_chunk(script: str, start_time: float, end_time: float, is_podcast: bool) -> str:
    """Script’in belirli zaman aralığına denk gelen kısmını döndürür."""
    words = script.split()
    wpm = 150 if is_podcast else 180
    start_word = int((start_time / 60) * wpm)
    end_word = int((end_time / 60) * wpm)
    return " ".join(words[start_word:end_word])

class KenBurnsImageClip(ImageClip):
    def __init__(self, img_path, duration, target_size, zoom_factor=1.05):
        super().__init__(img_path)
        self.duration = duration
        self.target_size = target_size
        self.zoom_factor = zoom_factor
        
        original_img = Image.open(img_path).convert("RGB")
        target_ratio = target_size[0] / target_size[1]
        img_ratio = original_img.width / original_img.height
        
        if img_ratio > target_ratio:
            new_height = target_size[1]
            new_width = int(new_height * img_ratio)
        else:
            new_width = target_size[0]
            new_height = int(new_width / img_ratio)
        
        zoomed_width = int(new_width * self.zoom_factor)
        zoomed_height = int(new_height * self.zoom_factor)
        
        img_start = original_img.resize((zoomed_width, zoomed_height), Image.LANCZOS)
        img_end = original_img.resize((new_width, new_height), Image.LANCZOS)
        
        self.img_start = np.array(img_start)
        self.img_end = np.array(img_end)
    
    def get_frame(self, t):
        if t < 0 or t > self.duration:
            t = max(0, min(self.duration, t))
        
        ratio = t / self.duration
        current_width = int(self.img_start.shape[1] * (1 - ratio) + self.img_end.shape[1] * ratio)
        current_height = int(self.img_start.shape[0] * (1 - ratio) + self.img_end.shape[0] * ratio)
        
        if current_width <= 0 or current_height <= 0:
            current_width, current_height = 1, 1
        
        pil_start = Image.fromarray(self.img_start)
        pil_end = Image.fromarray(self.img_end)
        
        blended = Image.blend(
            pil_start.resize((current_width, current_height), Image.LANCZOS),
            pil_end.resize((current_width, current_height), Image.LANCZOS),
            ratio
        )
        
        result = Image.new("RGB", self.target_size, (0, 0, 0))
        x = (self.target_size[0] - blended.width) // 2
        y = (self.target_size[1] - blended.height) // 2
        result.paste(blended, (x, y))
        
        return np.array(result)

def create_shorts_video(audio_path: str, script: str, output_path: str):
    logger.info("🎥 Shorts videosu üretiliyor (Ken Burns + Ultrafast)...")
    
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, Config.SHORTS_DURATION)
    
    width, height = 1080, 1920
    current_index = get_current_index()
    # 👇 SHORTS GÖRSELİ ARTIK 'sor' KLASÖRÜNDE
    image_path = Config.DATA_DIR / "images" / "sor" / f"{current_index}.png"
    
    if image_path.exists():
        logger.info(f"🖼️ Shorts görseli kullanılıyor: {image_path} (Ken Burns efektiyle)")
        background = KenBurnsImageClip(str(image_path), duration=total_duration, target_size=(width, height), zoom_factor=1.02)
    else:
        logger.warning(f"⚠️ Shorts görseli bulunamadı → Siyah arka plan")
        background = ColorClip((width, height), (0, 0, 0), duration=total_duration)

    text_clips = _create_text_clips(script, width, height, is_shorts=True, duration=total_duration)
    final_video = CompositeVideoClip([background] + text_clips)
    final_video = final_video.set_audio(audio).set_duration(total_duration)
    
    final_video.write_videofile(
        str(output_path),
        fps=24,
        codec="h264_nvenc" if _is_nvidia_gpu() else "libx264",
        audio_codec="aac",
        threads=CORES,
        preset="fast" if _is_nvidia_gpu() else "ultrafast",
        logger=None
    )
    
    logger.info(f"✅ Shorts videosu hazır: {output_path}")


def create_podcast_video(audio_path: str, script: str, output_path: str):
    logger.info("🎥 Podcast videosu üretiliyor (Görsel + Ken Burns + Parçalı Render)...")
    
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, Config.PODCAST_DURATION)
    
    width, height = 1920, 1080
    current_index = get_current_index()
   
    image_path = Config.DATA_DIR / "images" / "pod" / f"{current_index}.png"
    
    if image_path.exists():
        logger.info(f"🖼️ Podcast görseli kullanılıyor: {image_path} (Ken Burns efektiyle)")
        background_base = KenBurnsImageClip(str(image_path), duration=total_duration, target_size=(width, height), zoom_factor=1.01)
    else:
        logger.warning(f"⚠️ Podcast görseli bulunamadı → Siyah arka plan")
        background_base = ColorClip((width, height), (0, 0, 0), duration=total_duration)

    chunk_duration = total_duration / 3
    chunks = []
    
    for i in range(3):
        start_time = i * chunk_duration
        end_time = min((i + 1) * chunk_duration, total_duration)
        chunk_script = _get_script_chunk(script, start_time, end_time, is_podcast=True)
        
        text_clips = _create_text_clips(chunk_script, width, height, is_shorts=False, duration=(end_time - start_time))
        bg_clip = background_base.subclip(start_time, end_time)
        chunk_audio = audio.subclip(start_time, end_time)
        
        chunk_video = CompositeVideoClip([bg_clip] + text_clips)
        chunk_video = chunk_video.set_audio(chunk_audio)
        chunks.append(chunk_video)
    
    final_video = concatenate_videoclips(chunks)
    
    final_video.write_videofile(
        str(output_path),
        fps=24,
        codec="h264_nvenc" if _is_nvidia_gpu() else "libx264",
        audio_codec="aac",
        threads=CORES,
        preset="fast" if _is_nvidia_gpu() else "ultrafast",
        logger=None
    )
    
    logger.info(f"✅ Podcast videosu hazır: {output_path}")
    
    final_video.write_videofile(
        str(output_path),
        fps=24,
        codec="h264_nvenc" if _is_nvidia_gpu() else "libx264",
        audio_codec="aac",
        threads=CORES,
        preset="fast" if _is_nvidia_gpu() else "ultrafast",
        logger=None
    )
    
    logger.info(f"✅ Podcast videosu hazır: {output_path}") 
