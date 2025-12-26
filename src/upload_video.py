# src/upload_video.py
import os
import pickle
import base64
import json
import logging
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from src.config import Config
from src.utils import setup_logging, save_upload_log

logger = setup_logging()

def decode_youtube_credentials():
    """GitHub Secrets'ten YouTube kimlik bilgilerini decode et."""
    logger.info("🔑 YouTube kimlik bilgileri decode ediliyor...")
    
    encoded_credentials = os.environ.get("YOUTUBE_TOKEN_ENCODED") or os.environ.get("YOUTUBE_CREDENTIALS")
    
    if not encoded_credentials:
        raise ValueError("YOUTUBE_CREDENTIALS veya YOUTUBE_TOKEN_ENCODED ayarlanmamış!")
    
    try:
        # Base64 decode et
        decoded_data = base64.b64decode(encoded_credentials).decode("utf-8")
        
        # JSON format kontrolü
        try:
            json.loads(decoded_data)
            is_json = True
        except:
            is_json = False
        
        if is_json:
            client_secret_path = Config.TEMP_DIR / "client_secret.json"
            with open(client_secret_path, "w") as f:
                f.write(decoded_data)
            logger.info("✅ YouTube kimlik bilgileri (JSON) başarıyla decode edildi.")
            return str(client_secret_path)
        else:
            token_path = Config.TEMP_DIR / "token.pickle"
            with open(token_path, "wb") as f:
                f.write(decoded_data.encode("latin-1") if isinstance(decoded_data, str) else decoded_data)
            logger.info("✅ YouTube token.pickle dosyası başarıyla decode edildi.")
            return str(token_path)
            
    except Exception as e:
        logger.error(f"❌ Kimlik bilgileri decode hatası: {str(e)}")
        raise

def authenticate_youtube():
    """YouTube API için yetkilendirme yap (GÜVENLİ SÜRÜM)"""
    logger.info("🔑 YouTube API yetkilendirmesi yapılıyor...")
    
    token_path = Config.TEMP_DIR / "token.pickle"
    creds = None
    
    # Token'ı GitHub Secrets'ten al
    encoded_token = os.environ.get("YOUTUBE_TOKEN_ENCODED")
    if not encoded_token:
        raise ValueError("YOUTUBE_TOKEN_ENCODED secret'i ayarlanmamış!")
    
    try:
        # Token'ı decode et (hex format)
        decoded_token = bytes.fromhex(encoded_token)
        with open(token_path, "wb") as f:
            f.write(decoded_token)
        
        # Token'ı yükle
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
        
        # Geçerlilik kontrolü
        if not creds.valid:
            logger.warning("⚠️ Token geçersiz, yenilemeye çalışma...")
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Yenilenen token'ı tekrar kaydet
                with open(token_path, "wb") as f:
                    pickle.dump(creds, f)
                logger.info("✅ Token başarıyla yenilendi!")
            else:
                raise RuntimeError("TOKEN_YENİLENEMEDİ - YENİ TOKEN GEREKLİ")
        
        logger.info("✅ YouTube yetkilendirmesi başarılı.")
        return build("youtube", "v3", credentials=creds)
        
    except Exception as e:
        logger.critical(f"❌ YouTube yetkilendirme HATASI: {str(e)}")
        logger.critical("💡 ÇÖZÜM: YENİ TOKEN OLUŞTURUN VE GITHUB SECRETS'İ GÜNCELLEYİN")
        raise

def upload_to_youtube(video_path: str, title: str, description: str, privacy_status: str, mode: str):
    """Videoyu YouTube'a yükle (GÜVENİLİR)"""
    try:
        youtube = authenticate_youtube()
        
        # YouTube meta verileri
        safe_title = title[:95] + "..." if len(title) > 95 else title
        tags = ["ColdWar", "History", "Shorts", "SynapseDaily"] if mode == "shorts" else ["ColdWarTech", "UnbuiltCities", "RetroFuturism", "HistoryPodcast"]
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
        
        # Log kaydet
        save_upload_log(video_id, safe_title, mode)
        
        return video_id
        
    except Exception as e:
        logger.critical(f"❌ YOUTUBE YÜKLEME HATASI: {str(e)}")
        raise
