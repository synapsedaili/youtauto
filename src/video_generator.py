# src/video_generator.py

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
    
    # 4. Yazı klipleri
    text_clips = []
    start_time = 0.0
    for line in lines:
        if start_time >= total_duration:
            break
        
        # Satır süresi
        word_count = len(line.split())
        duration = max(1.5, min(word_count * 0.35, total_duration - start_time))
        end_time = start_time + duration
        
        # Beyaz yazı
        try:
            txt_clip = TextClip(
                line,
                font="Arial-Bold",
                fontsize=60,
                color="white",
                size=(width - 100, None),
                method="caption"
            ).set_position(("center", height - 400))  # Alt kısım
        except:
            txt_clip = TextClip(
                line,
                fontsize=50,
                color="white",
                size=(width - 100, None),
                method="caption"
            ).set_position(("center", height - 400))
        
        # Zaman ve efekt ayarla
        txt_clip = (
            txt_clip
            .set_start(start_time)
            .set_duration(duration)
            .fadein(0.2)
            .fadeout(0.2)
        )
        text_clips.append(txt_clip)  # 👈 BU SATIR EKLENDİ (önemli!)
        start_time = end_time
    
    # 5. ARKA PLAN + YAZILARI BİRLEŞTİR
    final_video = CompositeVideoClip([background] + text_clips)  # 👈 [background] + text_clips
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
    
    # 4. Yazı klipleri
    text_clips = []
    start_time = 0.0
    for line in lines:
        if start_time >= total_duration:
            break
        
        # Satır süresi
        word_count = len(line.split())
        duration = max(3.0, min(word_count * 0.4, total_duration - start_time))
        end_time = start_time + duration
        
        # Beyaz yazı
        try:
            txt_clip = TextClip(
                line,
                font="Arial-Bold",
                fontsize=56,
                color="white",
                size=(width - 200, None),
                method="caption"
            ).set_position(("center", height - 200))  # Alt kısım
        except:
            txt_clip = TextClip(
                line,
                fontsize=50,
                color="white",
                size=(width - 200, None),
                method="caption"
            ).set_position(("center", height - 200))
        
        # Zaman ve efekt ayarla
        txt_clip = (
            txt_clip
            .set_start(start_time)
            .set_duration(duration)
            .fadein(0.3)
            .fadeout(0.3)
        )
        text_clips.append(txt_clip)  # 👈 BU SATIR EKLENDİ (önemli!)
        start_time = end_time
    
    # 5. ARKA PLAN + YAZILARI BİRLEŞTİR
    final_video = CompositeVideoClip([background] + text_clips)  # 👈 [background] + text_clips
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
