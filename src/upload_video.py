# src/upload_video.py
import os
import pickle
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

def authenticate_youtube():
    """Basit YouTube yetkilendirme"""
    logger.info("🔑 YouTube API yetkilendirmesi yapılıyor...")
    
    # Token'ı doğrudan environment variable'dan al
    encoded_token = Config.YOUTUBE_TOKEN_ENCODED
    
    if not encoded_token:
        error_msg = "YOUTUBE_TOKEN_ENCODED ortam değişkeni ayarlanmamış!"
        logger.critical(f"❌ {error_msg}")
        logger.critical("💡 ÇÖZÜM: GitHub Secrets'te YOUTUBE_TOKEN_ENCODED secret'ini ekleyin")
        raise ValueError(error_msg)
    
    # Token'ı decode et
    try:
        decoded_token = bytes.fromhex(encoded_token)
        creds = pickle.loads(decoded_token)
        
        # Token geçerliliğini kontrol et
        if not creds.valid:
            error_msg = "Token geçersiz veya süresi dolmuş!"
            logger.critical(f"❌ {error_msg}")
            logger.critical("💡 ÇÖZÜM: Yeni token oluşturun ve GitHub Secrets'i güncelleyin")
            raise ValueError(error_msg)
        
        logger.info("✅ YouTube yetkilendirmesi başarılı.")
        return build("youtube", "v3", credentials=creds)
        
    except Exception as e:
        logger.critical(f"❌ Token decode hatası: {str(e)}")
        logger.critical("💡 ÇÖZÜM: Yeni token oluşturun ve GitHub Secrets'i güncelleyin")
        raise

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle"""
    youtube = authenticate_youtube()
    
    safe_title = title[:95] + "..." if len(title) > 95 else title
    tags = Config.SHORTS_TAGS if mode == "shorts" else Config.PODCAST_TAGS
    category_id = "22" if mode == "shorts" else "27"
    
    request_body = {
        "snippet": {
            "title": safe_title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }
    
    logger.info(f"📤 {mode.upper()} videosu YouTube'a yükleniyor: {safe_title}")
    media_file = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            logger.info(f"📤 Upload ilerlemesi: %{progress}")
    
    video_id = response["id"]
    logger.info(f"✅ YouTube ID: {video_id}")
    return video_id
