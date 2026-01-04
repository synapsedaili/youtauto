# src/upload_video.py
import os
import base64
import pickle
import logging
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config
from src.utils import setup_logging, save_upload_log

logger = setup_logging()

def get_authenticated_service():
    """Token'ı hem yerelde hem sunucuda yönetir."""
    creds = None
    # ✅ YENİ: YOUTUBE_TOKEN_ENCODED olarak güncelle
    token_base64 = os.environ.get("YOUTUBE_TOKEN_ENCODED")

    if token_base64:
        logger.info("🔗 Token Environment Variable'dan okunuyor...")
        try:
            token_data = base64.b64decode(token_base64)
            creds = pickle.loads(token_data)
        except Exception as e:
            logger.error(f"❌ Token decode hatası: {e}")
            creds = None
    else:
        if os.path.exists("token.pickle"):
            logger.info("📁 Token yerel dosyadan okunuyor...")
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

    # Token'ı yenile
    if creds and creds.expired and creds.refresh_token:
        logger.info("🔄 Token süresi dolmuş, yenileniyor...")
        creds.refresh(Request())

    if not creds or not creds.valid:
        raise RuntimeError("❌ YouTube kimlik doğrulaması başarısız!")

    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle."""
    youtube = get_authenticated_service()

    safe_title = title[:95] + "..." if len(title) > 95 else title
    tags = Config.SHORTS_TAGS if mode == "shorts" else Config.PODCAST_TAGS
    category_id = "22" if mode == "shorts" else "27"

    request_body = {
        "snippet": {
            "title": safe_title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    logger.info(f"📤 {mode.upper()} videosu YouTube'a yükleniyor: {title}")
    media_file = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"📤 Upload ilerlemesi: %{int(status.progress() * 100)}")

    video_id = response["id"]
    logger.info(f"✅ YouTube ID: {video_id}")
    save_upload_log(video_id, safe_title, mode)
    return video_id
