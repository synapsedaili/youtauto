# kaggle/wan21_video_generator.py
"""
Kaggle Video Generator - Wan2.1-T2V
=================================
Generates 120 videos from prompt list with ban prevention
"""

import os
import json
import time
import random
import torch
from pathlib import Path
from diffusers import WanVideoPipeline
from huggingface_hub import HfApi

print("🔧 Loading Wan2.1 model from local dataset...")

# Load from Kaggle Dataset (Internet Off compatible)
model_path = "/kaggle/input/wan21-t2v-13b-weights"
pipe = WanVideoPipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    local_files_only=True  # Critical for Internet Off mode
).to("cuda")

print("✅ Model loaded successfully!")

# Load prompt list
print("📖 Loading prompt list...")
with open("/kaggle/input/daily-prompts/prompts.json", "r") as f:
    prompts = json.load(f)

print(f"📋 Found {len(prompts)} prompts to process")

# Output directory
output_dir = Path("/tmp/videos")
output_dir.mkdir(parents=True, exist_ok=True)

# Video generation loop with ban prevention
for i, prompt_data in enumerate(prompts):
    try:
        prompt = prompt_data['prompt']
        video_id = prompt_data.get('scene', i)
        
        print(f"🎬 Generating video {i+1}/{len(prompts)}: {video_id}")
        
        # Generate 5-second video (30 frames at 6fps)
        video_frames = pipe(
            prompt,
            num_frames=30,
            height=512,
            width=512,
            num_inference_steps=50,
            guidance_scale=7.5
        ).frames[0]
        
        # Save video
        import imageio
        video_path = output_dir / f"{video_id:03d}.mp4"
        imageio.mimsave(str(video_path), video_frames, fps=6)
        
        print(f"✅ Saved: {video_path}")
        
        # 🛡️ BAN PREVENTION: Rest every 10 clips
        if (i + 1) % 10 == 0:
            rest_time = random.randint(45, 90)
            print(f"⏸️  Resting GPU for {rest_time} seconds...")
            time.sleep(rest_time)
            
    except Exception as e:
        print(f"❌ Error generating video {i}: {str(e)}")
        continue

# Upload to HuggingFace
print("📤 Uploading to HuggingFace...")
api = HfApi(token=os.getenv('HF_TOKEN'))

api.upload_folder(
    folder_path=str(output_dir),
    repo_id="YOUR_USERNAME/video-archive",
    repo_type="dataset",
    token=os.getenv('HF_TOKEN')
)

print("✅ All videos uploaded to HuggingFace!")

# Clean up
import gc
del pipe
gc.collect()
torch.cuda.empty_cache()
