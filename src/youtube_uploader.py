# src/youtube_uploader.py
import os
import json
import base64
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_client():
    """YouTube API istemcisi oluştur."""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            b64_data = os.environ["YOUTUBE_CREDENTIALS"]
            credentials = json.loads(base64.b64decode(b64_data))
            with open("client_secret.json", "w") as f:
                json.dump(credentials, f)
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    
    return build("youtube", "v3", credentials=creds)

def upload_video(video_path: str, title: str, description: str, privacy: str, is_shorts: bool):
    """Videoyu YouTube'a yükle."""
    youtube = get_youtube_client()
    
    tags = Config.SHORTS_TAGS if is_shorts else Config.PODCAST_TAGS
    category_id = "22" if is_shorts else "27"
    
    request_body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {"privacyStatus": privacy}
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
    
    return response["id"]