# src/kaggle/video_generator.py
"""
Kaggle Video Generator
====================

Generates 120 videos from prompt list using Wan2.1-T2V model
Optimized for Kaggle GPU with ban prevention
"""

import os
import json
import time
import random
import torch
from pathlib import Path
from typing import List, Dict
from diffusers import WanVideoPipeline
from src.utils.logging import get_logger, log_progress, log_session_start, log_session_end
from src.kaggle.hf_uploader import HFUploader

logger = get_logger()

class KaggleVideoGenerator:
    def __init__(self, model_path: str = None):
        """
        Initialize video generator.
        
        Args:
            model_path (str, optional): Path to Wan2.1 model. Defaults to Kaggle dataset path.
        """
        self.model_path = model_path or "/kaggle/input/wan21-t2v-13b-weights/Wan2.1-T2V-1.3B"
        self.pipe = None
        self.output_dir = Path("/tmp/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ VideoGenerator initialized")
        logger.info(f"📁 Model path: {self.model_path}")
        logger.info(f"📁 Output dir: {self.output_dir}")
    
    def load_model(self):
        """Load Wan2.1 model from local dataset."""
        try:
            logger.info("🔧 Loading Wan2.1 model...")
            
            # Check if model exists
            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"Model not found at: {self.model_path}")
            
            # Load model (local files only for Internet Off mode)
            self.pipe = WanVideoPipeline.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                local_files_only=True,  # Critical for Internet Off mode
                variant="fp16"
            ).to("cuda")
            
            logger.info("✅ Model loaded successfully!")
            
            # Check GPU memory
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"💾 GPU Memory: {gpu_memory:.2f} GB")
            
        except Exception as e:
            logger.error(f"❌ Model loading failed: {str(e)}")
            raise
    
    def generate_video(self, prompt: str, video_id: str, num_frames: int = 30, 
                      height: int = 512, width: int = 512) -> str:
        """
        Generate single video from prompt.
        
        Args:
            prompt (str): Text prompt for video generation
            video_id (str): Unique video identifier
            num_frames (int): Number of frames (30 frames = 5 seconds at 6fps)
            height (int): Video height
            width (int): Video width
        
        Returns:
            str: Path to generated video
        """
        try:
            logger.debug(f"🎬 Generating video {video_id}: {prompt[:50]}...")
            
            # Generate video
            video_frames = self.pipe(
                prompt,
                num_frames=num_frames,
                height=height,
                width=width,
                num_inference_steps=50,
                guidance_scale=7.5
            ).frames[0]
            
            # Save video
            import imageio
            video_path = self.output_dir / f"{video_id}.mp4"
            imageio.mimsave(str(video_path), video_frames, fps=6)
            
            file_size = video_path.stat().st_size / 1024 / 1024
            logger.debug(f"✅ Saved: {video_path} ({file_size:.2f} MB)")
            
            return str(video_path)
            
        except Exception as e:
            logger.error(f"❌ Video generation failed for {video_id}: {str(e)}")
            return None
    
    def generate_batch(self, prompts: List[Dict], session_id: str = None) -> Dict:
        """
        Generate batch of videos with ban prevention.
        
        Args:
            prompts (List[Dict]): List of prompt dictionaries
            session_id (str, optional): Session identifier
        
        Returns:
            Dict: Generation statistics
        """
        stats = {
            "total": len(prompts),
            "successful": 0,
            "failed": 0,
            "videos": []
        }
        
        if session_id:
            log_session_start("Video Generation", session_id)
        
        logger.info(f"📋 Starting batch generation: {len(prompts)} videos")
        
        for i, prompt_data in enumerate(prompts):
            try:
                prompt = prompt_data.get('prompt', '')
                video_id = prompt_data.get('id', f'vid_{i:03d}')
                
                # Generate video
                video_path = self.generate_video(prompt, video_id)
                
                if video_path:
                    stats["successful"] += 1
                    stats["videos"].append({
                        "id": video_id,
                        "path": video_path,
                        "prompt": prompt
                    })
                else:
                    stats["failed"] += 1
                
                # Progress log
                log_progress(i + 1, len(prompts), f"Success: {stats['successful']}, Failed: {stats['failed']}")
                
                # 🛡️ BAN PREVENTION: Rest every 10 videos
                if (i + 1) % 10 == 0:
                    rest_time = random.randint(45, 90)
                    logger.info(f"⏸️  GPU cooldown: {rest_time} seconds...")
                    time.sleep(rest_time)
                    
                    # Clear GPU memory
                    torch.cuda.empty_cache()
                
            except Exception as e:
                logger.error(f"❌ Error at video {i}: {str(e)}")
                stats["failed"] += 1
                continue
        
        if session_id:
            log_session_end(session_id, "complete", stats)
        
        return stats
    
    def cleanup(self):
        """Clean up GPU memory."""
        if self.pipe:
            del self.pipe
        torch.cuda.empty_cache()
        logger.info("🧹 GPU memory cleaned")

def run_kaggle_generation(prompts_path: str = None, session_id: str = None):
    """
    Main function for Kaggle video generation.
    
    Args:
        prompts_path (str, optional): Path to prompts JSON file
        session_id (str, optional): Session identifier
    """
    try:
        # Load prompts
        if not prompts_path:
            prompts_path = "/kaggle/input/daily-prompts/prompts.json"
        
        logger.info(f"📖 Loading prompts from: {prompts_path}")
        
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        logger.info(f"📋 Loaded {len(prompts)} prompts")
        
        # Initialize generator
        generator = KaggleVideoGenerator()
        
        # Load model
        generator.load_model()
        
        # Generate videos
        stats = generator.generate_batch(prompts, session_id)
        
        # Upload to HuggingFace
        logger.info("📤 Uploading to HuggingFace...")
        
        uploader = HFUploader()
        uploader.create_dataset_if_not_exists(private=True)
        
        date_str = session_id.split('_')[0] if session_id else time.strftime('%Y%m%d')
        success = uploader.upload_as_zip(
            str(generator.output_dir),
            f"videos_{date_str}.zip"
        )
        
        if success:
            logger.info("✅ All videos uploaded to HuggingFace!")
        else:
            logger.warning("⚠️ Some videos failed to upload")
        
        # Cleanup
        generator.cleanup()
        
        # Print final stats
        logger.info("=" * 60)
        logger.info("📊 GENERATION COMPLETE")
        logger.info(f"   Total: {stats['total']}")
        logger.info(f"   Successful: {stats['successful']}")
        logger.info(f"   Failed: {stats['failed']}")
        logger.info(f"   Success Rate: {(stats['successful']/stats['total']*100):.1f}%")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    prompts_path = sys.argv[1] if len(sys.argv) > 1 else None
    session_id = sys.argv[2] if len(sys.argv) > 2 else time.strftime('%Y%m%d_%H%M%S')
    run_kaggle_generation(prompts_path, session_id)
