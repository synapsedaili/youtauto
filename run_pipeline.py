# run_pipeline.py 
def run_shorts_pipeline():
    """Shorts pipeline'ını çalıştırır."""
    logger = setup_logging(Config.OUTPUT_DIR / "shorts.log")
    logger.info("📱 SHORTS PIPELINE BAŞLIYOR...")

    try:
        # Manuel script'i al
        script = get_manual_script("shorts")
        logger.info(f"📝 Shorts script uzunluğu: {len(script)} karakter")
        
        # 👈 sidea.txt yok, sabit index
        logger.info("📊 Yarı otomatik sistem: Görseller elle yönetiliyor")
        
        # Ses dosyasını oluştur
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "shorts_audio.mp3"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Videoyu oluştur
            video_path = temp_path / "shorts_video.mp4"
            logger.info("🎥 Video render ediliyor...")
            create_shorts_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle (private)
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(
                str(video_path), 
                f"Shorts Video",  # Başlık (elle düzenlenecek)
                "Description will be added manually",
                "private",
                "shorts"
            )
            
            add_video_to_playlist(video_id, "PLj-SRcntMu9NhOfPCTJ0gOJcZfKmhaJ80")
            
            logger.info(f"🎉 SHORTS TAMAMLANDI! YouTube ID: {video_id}")

    except Exception as e:
        logger.exception(f"❌ Shorts pipeline hatası: {str(e)}")
        raise

def run_podcast_pipeline():
    """Podcast pipeline'ını çalıştırır."""
    logger = setup_logging(Config.OUTPUT_DIR / "podcast.log")
    logger.info("🎙️ PODCAST PIPELINE BAŞLIYOR...")

    try:
        # Manuel script'i al
        script = get_manual_script("podcast")
        logger.info(f"📝 Podcast script uzunluğu: {len(script)} karakter")
        
        # 👈 sidea.txt yok, sabit index
        logger.info("📊 Yarı otomatik sistem: Görseller elle yönetiliyor")
        
        # Ses dosyasını oluştur
        with tempfile.TemporaryDirectory(dir=str(Config.TEMP_DIR)) as temp_dir:
            temp_path = Path(temp_dir)
            audio_path = temp_path / "podcast_audio.mp3"
            
            logger.info("🎙️ Seslendirme başlatılıyor...")
            asyncio.run(generate_voice_with_edge_tts(script, str(audio_path)))
            
            # Videoyu oluştur
            video_path = temp_path / "podcast_video.mp4"
            logger.info("🎥 Video render ediliyor...")
            create_podcast_video(str(audio_path), script, str(video_path))
            
            # YouTube'a yükle (private)
            logger.info("📤 YouTube'a yükleniyor...")
            video_id = upload_to_youtube(
                str(video_path), 
                f"Podcast Video",  # Başlık (elle düzenlenecek)
                "Description will be added manually",
                "private",
                "podcast"
            )
            
            add_video_to_playlist(video_id, "PLj-SRcntMu9Ng8Snbrm2kkAppJlNHeoq9")
            
            logger.info(f"🎉 PODCAST TAMAMLANDI! YouTube ID: {video_id}")
            # 👈 sidea.txt artırma YOK

    except Exception as e:
        logger.exception(f"❌ Podcast pipeline hatası: {str(e)}")
        raise
