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
    token_base64 = os.environ.get("YOUTUBE_TOKEN_ENCODED")

    if not token_base64:
        logger.error("❌ YOUTUBE_TOKEN_ENCODED environment variable bulunamadı!")
        raise RuntimeError("❌ YouTube kimlik doğrulaması başarısız!")

    try:
        token_data = base64.b64decode(token_base64)
        creds = pickle.loads(token_data)
    except Exception as e:
        logger.error(f"❌ Token decode hatası: {e}")
        raise RuntimeError("❌ YouTube kimlik doğrulaması başarısız!")

    if creds and creds.expired and creds.refresh_token:
        logger.info("🔄 Token süresi dolmuş, yenileniyor...")
        creds.refresh(Request())

    if not creds or not creds.valid:
        logger.error("❌ Token geçersiz veya bulunamadı!")
        raise RuntimeError("❌ YouTube kimlik doğrulaması başarısız!")

    # ⚠️ DİKKAT: Oynatma listesi için 'youtube' scope gerekli!
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle."""
    youtube = get_authenticated_service()

    safe_title = title[:95] + "..." if len(title) > 95 else title
    
    # Etiketleri utils'dan al
    from src.utils import generate_seo_tags
    tags_str = generate_seo_tags(title, mode)
    tags_list = tags_str.split()[:20]  # Maks 20 etiket

    category_id = "22" if mode == "shorts" else "27"

    request_body = {
        "snippet": {
            "title": safe_title,
            "description": description,
            "tags": tags_list,
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

def add_video_to_playlist(video_id: str, playlist_id: str):
    """Videoyu belirtilen oynatma listesine ekler."""
    youtube = get_authenticated_service()
    
    logger.info(f"➕ Video {video_id} oynatma listesine ekleniyor: {playlist_id}")
    
    request_body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }
    
    request = youtube.playlistItems().insert(
        part="snippet",
        body=request_body
    )
    
    try:
        response = request.execute()
        logger.info(f"✅ Video oynatma listesine eklendi! PlaylistItem ID: {response['id']}")
    except Exception as e:
        logger.error(f"❌ Oynatma listesine ekleme hatası: {str(e)}")
