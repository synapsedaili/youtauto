# src/fast_generator.py
import os
import tempfile
import shutil
from pathlib import Path
import numpy as np
import asyncio
import edge_tts
import multiprocessing
from PIL import Image, ImageDraw, ImageFont

# MoviePy importları
from moviepy.editor import ColorClip, CompositeVideoClip, AudioFileClip, ImageClip, concatenate_videoclips, \
    CompositeAudioClip
import moviepy.audio.fx.all as afx

# YouTube upload için gerekli
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import pickle

# ======================
# SİSTEM VE FPS AYARLARI
# ======================
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

FPS = 24

# Görsel Listeleri - src/image klasöründen
def get_shorts_images():
    """src/image/ klasöründen 1s.jpg, 2s.jpg, ... tarzı görselleri al."""
    image_dir = Path("src/image")
    if image_dir.exists():
        images = []
        for i in range(1, 9):  # 1s.jpg'den 8s.jpg'ye kadar
            img_path = image_dir / f"{i}s.jpg"
            if img_path.exists():
                images.append(str(img_path))
        return images
    return []

def get_podcast_images():
    """src/image/ klasöründen 1.jpg, 2.jpg, ..., 12.jpg tarzı görselleri al."""
    image_dir = Path("src/image")
    if image_dir.exists():
        images = []
        for i in range(1, 13):  # 1.jpg'den 12.jpg'ye kadar
            img_path = image_dir / f"{i}.jpg"
            if img_path.exists():
                images.append(str(img_path))
        return images
    return []

SHORTS_IMAGES = get_shorts_images()
PODCAST_IMAGES = get_podcast_images()

# Varsayılan scriptler
TOPIC = "1961: Soviet Alfa-Class Submarine Design Initiated (USSR)"

SHORTS_SCRIPT = """
In 1961, Soviet engineers secretly began designing the Alfa-class submarine. This wasn't just another warship—it was a revolutionary underwater predator that would change naval warfare forever.

Could titanium hulls really withstand deep ocean pressures?

For the full story, listen to today's podcast!

Like, comment, and subscribe for more Cold War mysteries!
""".strip()

PODCAST_SCRIPT = """
Welcome to Synapse Daily. Today we explore the 1961 Soviet Alfa-class submarine design—a story verified through declassified documents.

Chapter 1: The Vision
In 1961, amid the Cold War tensions, Soviet engineers at the Rubin Central Design Bureau began developing a revolutionary submarine concept. Historical records show this was more than ambition—it was detailed planning for an unprecedented titanium-hulled vessel.

Chapter 2: Technical Innovation
The design pushed 1960s technology to its limits. Engineers developed novel solutions for radiation shielding, life support, and deep-sea navigation. Declassified technical reports show how they solved problems we still face today.

Chapter 3: The Legacy
What strikes me most is their unwavering belief in impossible engineering. Even after various setbacks, they kept detailed notes. Their vision lives on in modern submarine design.

If you enjoyed this dive into Cold War history, don't forget to like, comment your thoughts below, and subscribe for more fascinating stories!
""".strip()


# ======================
# SHORTS İÇİN ÇOKLU GÖRSEL VE KEN BURNS
# ======================
def create_shorts_bg(image_list, total_duration, width, height):
    clips = []
    duration_per_img = 6.0
    elapsed = 0.0

    for i, img_path in enumerate(image_list):
        if elapsed >= total_duration: break

        current_clip_dur = (total_duration - elapsed) if i == len(image_list) - 1 else min(duration_per_img,
                                                                                           total_duration - elapsed)

        if Path(img_path).exists():
            clip = ImageClip(img_path).resize(height=height)
            if clip.w < width: clip = clip.resize(width=width)

            clip = (clip.set_duration(current_clip_dur)
                    .resize(lambda t: 1 + 0.1 * (t / current_clip_dur))
                    .set_position('center'))
            clips.append(clip)
            elapsed += current_clip_dur
        else:
            clips.append(ColorClip((width, height), (50, 50, 50)).set_duration(current_clip_dur))
            elapsed += current_clip_dur

    return concatenate_videoclips(clips).set_duration(total_duration)


# ======================
# PODCAST İÇİN ÇOKLU GÖRSEL FONKSİYONU
# ======================
def create_podcast_bg(image_list, total_duration, width, height):
    clips = []
    # Mevcut olan görselleri filtrele
    valid_images = [img for img in image_list if Path(img).exists()]

    if not valid_images:
        return ColorClip((width, height), (30, 30, 30)).set_duration(total_duration)

    elapsed_time = 0.0
    for i, img_path in enumerate(valid_images):
        if elapsed_time >= total_duration:
            break

        # Eğer son görseldeysek, kalan tüm süreyi ona ver
        if i == len(valid_images) - 1:
            current_duration = total_duration - elapsed_time
        else:
            # Diğer her görsel tam 120 saniye (2 dk) kalsın
            # Ama video süresinden fazlasını almasın
            current_duration = min(120.0, total_duration - elapsed_time)

        if current_duration <= 0:
            break

        clip = ImageClip(img_path).resize(width=width)
        if clip.h < height:
            clip = clip.resize(height=height)

        # Süreyi set ediyoruz ve zoom efektini bu süreye göre ayarlıyoruz
        clip = (clip.set_duration(current_duration)
                .resize(lambda t, dur=current_duration: 1 + 0.05 * (t / dur))
                .set_position('center'))

        clips.append(clip)
        elapsed_time += current_duration

    return concatenate_videoclips(clips).set_duration(total_duration)


# ======================
# METİN RESMİ OLUŞTURUCU
# ======================
def create_text_image(text, width, height, is_shorts):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fontsize = 80 if is_shorts else 60
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    if is_shorts:
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test = current_line + " " + word if current_line else word
            if draw.textbbox((0, 0), test, font=font)[2] < width * 0.8:
                current_line = test
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        full_text = "\n".join(lines)
        bbox = draw.multiline_textbbox((0, 0), full_text, font=font, align="center")
        x = (width - (bbox[2] - bbox[0])) // 2
        y = (height - (bbox[3] - bbox[1])) // 2
        draw.multiline_text((x, y), full_text, font=font, fill="white", stroke_width=4, stroke_fill="black",
                            align="center")
    else:
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            if draw.textbbox((0, 0), current_line + " " + word, font=font)[2] <= width - 200:
                current_line += (" " + word if current_line else word)
            else:
                lines.append(current_line);
                current_line = word
        lines.append(current_line)
        y_offset = 180
        for line in lines:
            draw.text((180, y_offset), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
            y_offset += fontsize + 15
    return img


# ======================
# YOUTUBE UPLOAD İŞLEMLERİ
# ======================
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    """YouTube API authenticated service döndürür."""
    credentials = None
    
    # token.pickle dosyası varsa yükle
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    # credentials geçerli değilse yeniden authenticate et
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Yeni credentials'ı kaydet
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    return build('youtube', 'v3', credentials=credentials)


def upload_to_youtube(video_path, title, description, privacy_status="private"):
    """YouTube'a video upload eder."""
    youtube = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['Cold War', 'History', 'Documentary', 'Soviet'],
            'categoryId': '27'  # Education
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"📦 Upload progress: {int(status.progress() * 100)}%")
    
    print(f"✅ Video uploaded successfully! Video ID: {response['id']}")
    return response['id']


# ======================
# ANA VİDEO ÜRETİMİ + UPLOAD
# ======================
def create_and_upload_video(script, title, description, is_shorts=True):
    print(f"🎥 {('Shorts' if is_shorts else 'Podcast')} üretimi başladı...")
    
    # Geçici dosya oluştur
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
        temp_path = temp_video.name
    
    temp_dir = Path(tempfile.mkdtemp())
    temp_audio = temp_dir / "audio.mp3"

    asyncio.run(edge_tts.Communicate(script, "en-US-GuyNeural").save(str(temp_audio)))
    voice_audio = AudioFileClip(str(temp_audio))
    duration = voice_audio.duration

    # --- ARKA PLAN SESİ ---
    ambient_path = "data/1.mp3"  # Arka plan sesi
    if os.path.exists(ambient_path):
        try:
            ambient_audio = AudioFileClip(ambient_path)
            ambient_audio = afx.audio_loop(ambient_audio, duration=duration)
            ambient_audio = ambient_audio.volumex(0.15)
            final_audio = CompositeAudioClip([voice_audio, ambient_audio])
            print("✅ Arka plan sesi (data/1.mp3) başarıyla eklendi.")
        except Exception as e:
            print(f"⚠️ Arka plan sesi eklenirken hata: {e}")
            final_audio = voice_audio
    else:
        print("⚠️ data/1.mp3 bulunamadı, sadece konuşma sesi kullanılıyor.")
        final_audio = voice_audio

    width, height = (1080, 1920) if is_shorts else (1920, 1080)

    if is_shorts:
        background = create_shorts_bg(SHORTS_IMAGES, duration, width, height)
    else:
        background = create_podcast_bg(PODCAST_IMAGES, duration, width, height)

    overlay = ColorClip((width, height), (0, 0, 0)).set_duration(duration).set_opacity(0.4)

    words = script.split()
    chunk_size = 4 if is_shorts else 50
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    text_clips = []
    start_time = 0.0
    speed = (duration / len(words)) * chunk_size

    for chunk in chunks:
        if start_time >= duration: break
        c_dur = min(speed, duration - start_time)
        text_img = create_text_image(chunk, width, height, is_shorts)
        img_p = temp_dir / f"t_{start_time}.png"
        text_img.save(str(img_p))
        text_clips.append(ImageClip(str(img_p)).set_duration(c_dur).set_start(start_time).set_position('center'))
        start_time += c_dur

    final = CompositeVideoClip([background, overlay] + text_clips).set_audio(final_audio).set_duration(duration)

    final.write_videofile(
        temp_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=multiprocessing.cpu_count(),
        preset="ultrafast",
        logger=None
    )
    
    print(f"✅ Video üretildi: {temp_path}")
    
    # YouTube upload
    print("📤 YouTube'a upload ediliyor...")
    video_id = upload_to_youtube(temp_path, title, description, "private")
    
    # Geçici dosyaları temizle
    os.unlink(temp_path)
    shutil.rmtree(temp_dir)
    
    print(f"🎉 {('Shorts' if is_shorts else 'Podcast')} tamamlandı! Video ID: {video_id}")
    return video_id


if __name__ == "__main__":
    print("🚀 Fast Video Generator Başlatılıyor...")
    print(f"📊 Shorts görselleri: {len(SHORTS_IMAGES)} adet")
    print(f"📊 Podcast görselleri: {len(PODCAST_IMAGES)} adet")
    
    # Shorts upload
    create_and_upload_video(
        SHORTS_SCRIPT,
        "Soviet Alfa-Class Submarine Design (1961) - Shorts",
        "1961: Soviet Alfa-Class Submarine Design Initiated - Cold War Mystery",
        is_shorts=True
    )
    
    # Podcast upload
    create_and_upload_video(
        PODCAST_SCRIPT,
        "Soviet Alfa-Class Submarine Design (1961) - Documentary",
        "Detailed documentary about the 1961 Soviet Alfa-Class Submarine Design - Cold War Engineering",
        is_shorts=False
    )
    
    print("🎉 Tüm işlemler tamamlandı!")
