# src/upload_video.py
import os
import pickle
import base64
import logging
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config
from src.utils import setup_logging, save_upload_log

logger = setup_logging()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """Token.pickle dosyasını doğrudan kullan."""
    logger.info("🔑 YouTube API yetkilendirmesi yapılıyor...")
    
    # GitHub Secrets'ten token'ı al
    token_b64 = os.environ.get("YOUTUBE_TOKEN_ENCODED")
    if not token_b64:
        raise ValueError("YOUTUBE_TOKEN_ENCODED secret'i ayarlanmamış!")
    
    try:
        # Base64 decode et
        token_data = base64.b64decode(token_b64)
        
        # Token'ı yükle
        creds = pickle.loads(token_data)
        
        # Token yenile (expire olmamışsa)
        if creds and creds.expired and creds.refresh_token:
            logger.info("🔄 Token yenileniyor...")
            creds.refresh(Request())
            
            # Yenilenmiş token'ı tekrar base64'le (isteğe bağlı)
            renewed_token_b64 = base64.b64encode(pickle.dumps(creds)).decode("utf-8")
            # Bu yenilenmiş token'ı GitHub Secrets'te güncellemelisiniz
        
        logger.info("✅ Token doğrudan yüklendi ve doğrulandı.")
        return build("youtube", "v3", credentials=creds)
        
    except Exception as e:
        logger.error(f"❌ Token yükleme hatası: {str(e)}")
        raise

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle (token.pickle ile)."""
    import os
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    
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
    
    logger.info(f"📤 {mode.upper()} videosu YouTube'a yükleniyor: {title}")
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
    save_upload_log(video_id, safe_title, mode)
    
    return video_id
