# src/kaggle/hf_uploader.py
"""
HuggingFace Uploader
==================

Uploads generated videos to HuggingFace Dataset
"""

import os
import time
from pathlib import Path
from typing import List, Optional
from huggingface_hub import HfApi, login
from src.utils.logging import get_logger, log_progress

logger = get_logger()

class HFUploader:
    def __init__(self, token: Optional[str] = None, repo_id: Optional[str] = None):
        """
        Initialize HuggingFace uploader.
        
        Args:
            token (str, optional): HuggingFace API token. Defaults to env var.
            repo_id (str, optional): Dataset repo ID. Defaults to env var.
        """
        self.token = token or os.getenv('HF_TOKEN')
        self.repo_id = repo_id or os.getenv('HF_DATASET_REPO', 'your-username/video-archive')
        
        if not self.token:
            raise ValueError("HuggingFace token not provided")
        
        # Login to HuggingFace
        login(token=self.token)
        
        # Initialize API
        self.api = HfApi()
        
        logger.info(f"✅ HFUploader initialized for repo: {self.repo_id}")
    
    def upload_single_video(self, video_path: str, path_in_repo: str, retry: int = 3) -> bool:
        """
        Upload single video file.
        
        Args:
            video_path (str): Local path to video file
            path_in_repo (str): Path in HuggingFace repo
            retry (int): Number of retry attempts
        
        Returns:
            bool: True if successful
        """
        for attempt in range(retry):
            try:
                logger.info(f"📤 Uploading: {video_path} → {path_in_repo}")
                
                self.api.upload_file(
                    path_or_fileobj=video_path,
                    path_in_repo=path_in_repo,
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    token=self.token
                )
                
                logger.info(f"✅ Uploaded: {path_in_repo}")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Upload attempt {attempt + 1}/{retry} failed: {str(e)}")
                if attempt < retry - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
        
        logger.error(f"❌ Failed to upload after {retry} attempts: {video_path}")
        return False
    
    def upload_folder(self, folder_path: str, path_in_repo: str = "", retry: int = 3) -> bool:
        """
        Upload entire folder of videos.
        
        Args:
            folder_path (str): Local folder path
            path_in_repo (str): Path in HuggingFace repo
            retry (int): Number of retry attempts
        
        Returns:
            bool: True if successful
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            logger.error(f"❌ Folder does not exist: {folder_path}")
            return False
        
        # Get all video files
        video_files = list(folder.glob("*.mp4"))
        
        if not video_files:
            logger.warning(f"⚠️ No video files found in: {folder_path}")
            return False
        
        logger.info(f"📦 Found {len(video_files)} videos to upload")
        
        # Upload each video
        successful = 0
        failed = 0
        
        for i, video_file in enumerate(video_files):
            # Calculate path in repo
            if path_in_repo:
                repo_path = f"{path_in_repo}/{video_file.name}"
            else:
                repo_path = video_file.name
            
            # Upload
            if self.upload_single_video(str(video_file), repo_path, retry):
                successful += 1
            else:
                failed += 1
            
            # Progress log
            log_progress(i + 1, len(video_files), f"Uploaded {successful}, Failed {failed}")
            
            # Rate limiting (avoid API throttling)
            if (i + 1) % 10 == 0:
                logger.info("⏸️  Rate limit pause (10 seconds)...")
                time.sleep(10)
        
        logger.info(f"📊 Upload complete: {successful} successful, {failed} failed")
        return failed == 0
    
    def upload_as_zip(self, folder_path: str, zip_name: str = "videos_bundle.zip", retry: int = 3) -> bool:
        """
        Compress folder to zip and upload as single file.
        
        Args:
            folder_path (str): Local folder path
            zip_name (str): Name of zip file
            retry (int): Number of retry attempts
        
        Returns:
            bool: True if successful
        """
        import zipfile
        
        folder = Path(folder_path)
        zip_path = folder.parent / zip_name
        
        if not folder.exists():
            logger.error(f"❌ Folder does not exist: {folder_path}")
            return False
        
        # Create zip file
        logger.info(f"📦 Creating zip archive: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            video_files = list(folder.glob("*.mp4"))
            for video_file in video_files:
                zipf.write(video_file, arcname=video_file.name)
        
        logger.info(f"✅ Zip created: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)")
        
        # Upload zip
        success = self.upload_single_video(str(zip_path), zip_name, retry)
        
        # Clean up zip
        if zip_path.exists():
            zip_path.unlink()
        
        return success
    
    def create_dataset_if_not_exists(self, private: bool = True) -> bool:
        """
        Create dataset repo if it doesn't exist.
        
        Args:
            private (bool): Whether dataset should be private
        
        Returns:
            bool: True if successful or already exists
        """
        try:
            # Try to get repo info
            self.api.repo_info(repo_id=self.repo_id, repo_type="dataset", token=self.token)
            logger.info(f"✅ Dataset already exists: {self.repo_id}")
            return True
        except:
            # Repo doesn't exist, create it
            try:
                logger.info(f"📁 Creating new dataset: {self.repo_id}")
                
                self.api.create_repo(
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    private=private,
                    token=self.token
                )
                
                logger.info(f"✅ Dataset created: {self.repo_id}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to create dataset: {str(e)}")
                return False

def upload_videos_to_hf(video_folder: str, date_str: str = None) -> bool:
    """
    Convenience function to upload videos.
    
    Args:
        video_folder (str): Path to video folder
        date_str (str, optional): Date string for folder organization
    
    Returns:
        bool: True if successful
    """
    try:
        uploader = HFUploader()
        
        # Create dataset if needed
        uploader.create_dataset_if_not_exists(private=True)
        
        # Organize by date
        if date_str:
            path_in_repo = f"{date_str}"
        else:
            path_in_repo = ""
        
        # Upload as zip (more efficient for many files)
        success = uploader.upload_as_zip(video_folder, f"videos_{date_str or 'bundle'}.zip")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test upload
    import sys
    if len(sys.argv) > 1:
        video_folder = sys.argv[1]
        date_str = sys.argv[2] if len(sys.argv) > 2 else None
        upload_videos_to_hf(video_folder, date_str)
    else:
        print("Usage: python hf_uploader.py <video_folder> [date_str]")
