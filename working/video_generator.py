# /kaggle/working/video_generator.py
"""
Kaggle Video Generator - SAFE PRODUCTION VERSION
================================================

Wan2.1-T2V-1.3B ile 120 video üretimi
Tüm ban önleme önlemleri dahil (Cooldown, Local Load, Zip Upload)
"""

import os
import sys
import json
import time
import random
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# ============================================
# 1. LOGGING SETUP
# ============================================
def log(message):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

log("🚀 Kaggle Video Generator Started")
log("=" * 60)

# ============================================
# 2. CONFIGURATION
# ============================================
CONFIG = {
    "model_path": "/kaggle/input/wan21-t2v-13b-weights/Wan2.1-T2V-1.3B",
    "prompts_path": "/kaggle/input/github-inputs/jobs.json",
    "output_dir": "/tmp/videos",
    "working_dir": "/kaggle/working",
    "hf_repo_id": "YOUR_USERNAME/video-archive",  # ⚠️ KENDİ KULLANICI ADINI YAZ
    "total_clips": 120,
    "cooldown_every": 10,  # Her 10 videoda mola
    "cooldown_duration": (45, 90),  # 45-90 saniye rastgele
    "video_duration": 5,  # saniye
    "fps": 6,
    "frames": 30,  # 5sn * 6fps
    "height": 512,
    "width": 512,
    "num_inference_steps": 50,
    "guidance_scale": 7.5
}

# Create output directory
Path(CONFIG["output_dir"]).mkdir(parents=True, exist_ok=True)
log(f"📁 Output directory: {CONFIG['output_dir']}")

# ============================================
# 3. LOAD PROMPTS
# ============================================
log("📖 Loading prompts...")

try:
    with open(CONFIG["prompts_path"], "r", encoding="utf-8") as f:
        prompts_data = json.load(f)
    
    log(f"✅ Loaded {len(prompts_data)} prompts")
    
except Exception as e:
    log(f"❌ Failed to load prompts: {str(e)}")
    # Create fallback prompts
    prompts_data = [
        {"id": f"vid_{i:03d}", "prompt": f"Professional documentary scene {i}", "duration": 5}
        for i in range(CONFIG["total_clips"])
    ]
    log(f"⚠️ Using {len(prompts_data)} fallback prompts")

# ============================================
# 4. LOAD MODEL (INTERNET OFF MODE)
# ============================================
log("🔧 Loading Wan2.1 model from local dataset...")

try:
    import torch
    from diffusers import WanVideoPipeline
    
    # Check if model exists
    if not Path(CONFIG["model_path"]).exists():
        raise FileNotFoundError(f"Model not found at: {CONFIG['model_path']}")
    
    # Load model (LOCAL FILES ONLY - Critical for Internet Off)
    pipe = WanVideoPipeline.from_pretrained(
        CONFIG["model_path"],
        torch_dtype=torch.float16,
        local_files_only=True,  # ✅ NO INTERNET TRAFFIC
        variant="fp16"
    ).to("cuda")
    
    log("✅ Model loaded successfully!")
    
    # Check GPU memory
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    log(f"💾 GPU Memory: {gpu_memory:.2f} GB")
    
except Exception as e:
    log(f"❌ Model loading failed: {str(e)}")
    raise

# ============================================
# 5. VIDEO GENERATION LOOP (WITH COOLDOWN)
# ============================================
log("🎬 Starting video generation...")
log(f"📋 Total clips: {len(prompts_data)}")

stats = {
    "successful": 0,
    "failed": 0,
    "start_time": datetime.now(),
    "videos": []
}

import imageio

for i, prompt_data in enumerate(prompts_data):
    try:
        prompt = prompt_data.get("prompt", "")
        video_id = prompt_data.get("id", f"vid_{i:03d}")
        
        log(f"🎥 [{i+1}/{len(prompts_data)}] Generating: {video_id}")
        
        # Generate video
        video_frames = pipe(
            prompt,
            num_frames=CONFIG["frames"],
            height=CONFIG["height"],
            width=CONFIG["width"],
            num_inference_steps=CONFIG["num_inference_steps"],
            guidance_scale=CONFIG["guidance_scale"]
        ).frames[0]
        
        # Save to TEMP directory (not working dir)
        video_path = Path(CONFIG["output_dir"]) / f"{video_id}.mp4"
        imageio.mimsave(str(video_path), video_frames, fps=CONFIG["fps"])
        
        file_size = video_path.stat().st_size / 1024 / 1024
        log(f"   ✅ Saved: {video_path.name} ({file_size:.2f} MB)")
        
        stats["successful"] += 1
        stats["videos"].append({
            "id": video_id,
            "path": str(video_path),
            "size_mb": round(file_size, 2)
        })
        
        # 🛡️ BAN PREVENTION: Cooldown every 10 videos
        if (i + 1) % CONFIG["cooldown_every"] == 0:
            rest_time = random.uniform(*CONFIG["cooldown_duration"])
            log(f"   ⏸️  GPU cooldown: {rest_time:.0f} seconds...")
            time.sleep(rest_time)
            
            # Clear GPU memory
            torch.cuda.empty_cache()
            log("   🧹 GPU memory cleaned")
        
    except Exception as e:
        log(f"   ❌ Failed: {str(e)}")
        stats["failed"] += 1
        continue

# ============================================
# 6. CREATE ZIP BUNDLE (SINGLE FILE UPLOAD)
# ============================================
log("📦 Creating zip bundle...")

zip_path = Path(CONFIG["working_dir"]) / "videos_bundle.zip"

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for video_file in Path(CONFIG["output_dir"]).glob("*.mp4"):
        zipf.write(video_file, arcname=video_file.name)

zip_size = zip_path.stat().st_size / 1024 / 1024
log(f"✅ Zip created: {zip_path.name} ({zip_size:.2f} MB)")

# ============================================
# 7. UPLOAD TO HUGGINGFACE
# ============================================
log("📤 Uploading to HuggingFace...")

try:
    from huggingface_hub import HfApi, login
    
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        # Try from Kaggle secrets
        hf_token = ""  # Add your token here or use Kaggle secrets
    
    if hf_token:
        login(token=hf_token)
        api = HfApi()
        
        # Upload entire folder
        api.upload_folder(
            folder_path=str(CONFIG["output_dir"]),
            repo_id=CONFIG["hf_repo_id"],
            repo_type="dataset",
            token=hf_token
        )
        
        log(f"✅ Uploaded to HuggingFace: {CONFIG['hf_repo_id']}")
    else:
        log("⚠️ HF_TOKEN not found, skipping upload")
        log("📁 Videos saved locally in: " + CONFIG["output_dir"])
        
except Exception as e:
    log(f"❌ HuggingFace upload failed: {str(e)}")
    log("📁 Videos saved locally in: " + CONFIG["output_dir"])

# ============================================
# 8. FINAL STATISTICS
# ============================================
end_time = datetime.now()
duration = (end_time - stats["start_time"]).total_seconds()

log("=" * 60)
log("📊 GENERATION COMPLETE")
log(f"   Total prompts: {len(prompts_data)}")
log(f"   Successful: {stats['successful']}")
log(f"   Failed: {stats['failed']}")
log(f"   Success rate: {(stats['successful']/len(prompts_data)*100):.1f}%")
log(f"   Total time: {duration/3600:.2f} hours")
log(f"   Average per video: {duration/len(prompts_data):.1f} seconds")
log(f"   Total size: {zip_size:.2f} MB")
log("=" * 60)

# ============================================
# 9. CLEANUP
# ============================================
log("🧹 Cleaning up...")

del pipe
torch.cuda.empty_cache()

log("✅ Kaggle Video Generator Finished")
