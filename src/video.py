# video.py
import os
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from moviepy.video.VideoClip import ColorClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

# === ⚠️ ELEVENLABS API ANAHTARI ===
ELEVENLABS_API_KEY = "YOUR_API_KEY_HERE"  # ← BURAYI DOLDUR!

# === ÇIKTI KLASÖRLERİ ===
OUTPUT_DIR = r"C:\Users\gktg9\PycharmProjects\YouTube\output"
VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

def split_text_into_lines(text: str, max_chars_per_line=60):
    """İngilizce metin için uygun satır bölme."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            current_line += (" " + word) if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def text_to_speech_elevenlabs(text: str, output_path: str):
    """ElevenLabs ile İNGİLİZCE ses üretimi (yüksek kalite)."""
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "YOUR_API_KEY_HERE":
        raise ValueError("❌ Please set your ELEVENLABS_API_KEY in video.py")

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    # 🗣️ İngilizce için en iyi seslerden biri: "Domi" (clear, energetic)
    response = client.text_to_speech.convert(
        voice_id="AZnzlk1XvdvUeBnXmlld",  # Domi (İngilizce için mükemmel)
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text[:2500],
        model_id="eleven_turbo_v2",  # hızlı ve iyi İngilizce
        voice_settings=VoiceSettings(
            stability=0.75,        # daha tutarlı ton
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    with open(output_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

def create_video_from_script(script: str, idea_title: str, use_ai_background=False) -> str:
    # Dosya adı (İngilizce karakterlere uygun)
    safe_name = "".join(c for c in idea_title if c.isalnum() or c in " _-")[:30]
    video_path = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
    audio_path = os.path.join(AUDIO_DIR, f"{safe_name}.mp3")

    # === 1. İNGİLİZCE SES ÜRETİMİ ===
    try:
        text_to_speech_elevenlabs(script, audio_path)
    except Exception as e:
        # Fallback: gTTS ile İngilizce ses
        try:
            from gtts import gTTS
            tts = gTTS(text=script[:400], lang="en", slow=False)
            tts.save(audio_path)
        except:
            raise RuntimeError(f"🔊 Ses hatası: {e}")

    # === 2. ARKA PLAN (SİYAH) ===
    width, height = 1280, 720
    background = ColorClip(size=(width, height), color=(0, 0, 0), duration=120)

    # === 3. METİN İŞLEME ===
    lines = split_text_into_lines(script, max_chars_per_line=65)  # İngilizce için biraz daha geniş
    if not lines:
        lines = ["(No content)"]

    # === 4. SES SÜRESİ ===
    audio = AudioFileClip(audio_path)
    total_duration = min(audio.duration, 120)  # max 2 dakika
    time_per_line = max(2.8, total_duration / len(lines))

    # === 5. YAZI KLİPLERİ (BEYAZ, ORTALI) ===
    text_clips = []
    for i, line in enumerate(lines):
        start_t = i * time_per_line
        end_t = min(start_t + time_per_line, total_duration)
        if start_t >= total_duration:
            break

        try:
            txt_clip = TextClip(
                line,
                font="Arial-Bold",  # İngilizce'de bold daha okunaklı
                fontsize=54,
                color="white",
                size=(width - 120, None),
                method="caption"
            )
        except:
            txt_clip = TextClip(
                line,
                fontsize=50,
                color="white",
                size=(width - 120, None),
                method="caption"
            )

        txt_clip = (
            txt_clip
            .set_position(("center", height - 130))
            .set_start(start_t)
            .set_duration(end_t - start_t)
            .fadein(0.3)
            .fadeout(0.3)
        )
        text_clips.append(txt_clip)

    # === 6. BİRLEŞTİR ===
    final_video = CompositeVideoClip([background] + text_clips)
    final_video = final_video.set_audio(audio).set_duration(total_duration)

    # === 7. KAYDET ===
    final_video.write_videofile(
        video_path,
        fps=24,
        audio_codec="aac",
        temp_audiofile=os.path.join(AUDIO_DIR, "temp-audio.m4a"),
        remove_temp=True,
        logger=None,
        threads=2
    )

    return video_path