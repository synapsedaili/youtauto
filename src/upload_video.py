# src/upload_video.py
import os
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1" 
import pickle
import base64
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """YouTube API için yetkilendirme yap."""
    logger.info("🔑 YouTube API yetkilendirmesi yapılıyor...")

    # token.pickle dosyasını decode et (GitHub Secrets'ten gelen base64 string)
    encoded_token = os.environ.get("YOUTUBE_TOKEN_ENCODED")
    if not encoded_token:
        raise ValueError("YOUTUBE_TOKEN_ENCODED ayarlanmamış!")

    token_bytes = base64.b64decode(encoded_token)
    creds = pickle.loads(token_bytes)

    # Token yenileme
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    logger.info("✅ YouTube yetkilendirmesi tamamlandı.")
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle."""
    youtube = authenticate_youtube()

    # YouTube meta verileri
    safe_title = title[:95] + "..." if len(title) > 95 else title
    tags = Config.SHORTS_TAGS if mode == "shorts" else Config.PODCAST_TAGS
    category_id = "22" if mode == "shorts" else "27"  # People & Blogs / Education

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

    # Upload
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
    
    return video_id
