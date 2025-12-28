# src/upload_video.py 
import os
import pickle
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import base64
import json
from src.config import Config
from src.utils import setup_logging, save_upload_log

logger = setup_logging()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def decode_youtube_token():
    """GitHub Secrets'ten base64 decode et."""
    token_b64 = os.environ.get("YOUTUBE_TOKEN_ENCODED")
    if not token_b64:
        raise ValueError("YOUTUBE_TOKEN_ENCODED secret'i ayarlanmamış!")
    
    try:
        # Base64 decode et
        token_data = base64.b64decode(token_b64)
        # Byte'ı pickle objesine çevir
        creds = pickle.loads(token_data)
        return creds
    except Exception as e:
        raise ValueError(f"Token decode hatası: {str(e)}")

def authenticate_youtube():
    """YouTube API için yetkilendirme yap."""
    logger.info("🔑 YouTube API yetkilendirmesi yapılıyor...")
    
    token_path = Config.TEMP_DIR / "token.pickle"
    creds = None
    
    # Önce GitHub Secrets'ten token al
    try:
        creds = decode_youtube_token()
        logger.info("✅ GitHub Secrets'ten token yüklendi")
    except:
        # Token geçersizse, client_secret.json kullan
        logger.warning("⚠️ GitHub token geçersiz, OAuth akışı başlatılıyor...")
        from src.utils import decode_youtube_credentials
        client_secret_path = decode_youtube_credentials()
        
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_path, SCOPES
        )
        creds = flow.run_local_server(port=0, open_browser=False)
        
        # Token'ı kaydet
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
    
    # Token yenile
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Yenilenmiş token'ı kaydet
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
    
    logger.info("✅ YouTube yetkilendirmesi başarılı.")
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle."""
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
