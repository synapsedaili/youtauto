# src/upload_video.py
import os
import pickle
import base64
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """YouTube API için yetkilendirme yap (hata güvenli)."""
    logger.info("🔑 YouTube API yetkilendirmesi yapılıyor...")
    
    # 1. Önce token.pickle var mı kontrol et
    token_path = Config.TEMP_DIR / "token.pickle"
    if token_path.exists():
        try:
            with open(token_path, "rb") as f:
                creds = pickle.load(f)
            if creds and creds.valid:
                logger.info("✅ Mevcut token kullanılabilir.")
                return build("youtube", "v3", credentials=creds)
        except Exception as e:
            logger.warning(f"⚠️ Token okunamadı: {e}")
    
    # 2. client_secret.json oluştur
    try:
        b64_data = os.environ["YOUTUBE_CREDENTIALS"]
        credentials = json.loads(base64.b64decode(b64_data).decode("utf-8"))
        client_secret_path = Config.TEMP_DIR / "client_secret.json"
        with open(client_secret_path, "w") as f:
            json.dump(credentials, f)
    except Exception as e:
        logger.error(f"❌ YouTube kimlik bilgileri decode edilemedi: {e}")
        raise ValueError("YOUTUBE_CREDENTIALS geçersiz!")
    
    # 3. Yeni yetkilendirme yap
    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=False)
        
        # Token'ı kaydet
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)
        
        logger.info("✅ Yeni YouTube yetkilendirmesi tamamlandı.")
        return build("youtube", "v3", credentials=creds)
    
    except Exception as e:
        logger.error(f"❌ YouTube yetkilendirme hatası: {e}")
        raise

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle."""
    youtube = authenticate_youtube()  # Artık None döndürmez!
    
    safe_title = (title[:95] + "...") if len(title) > 95 else title
    tags = Config.SHORTS_TAGS if mode == "shorts" else Config.PODCAST_TAGS
    category_id = "22" if mode == "shorts" else "27"
    
    body = {
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
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
    
    logger.info(f"✅ YouTube ID: {response['id']}")
    return response["id"]
