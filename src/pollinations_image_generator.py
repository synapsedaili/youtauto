# src/pollinations_image_generator.py
"""
Pollinations.ai Image Generator
============================

Uses Pollinations.ai API for image generation
No browser automation required
"""

import os
import time
import requests
from pathlib import Path
from urllib.parse import quote
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class PollinationsImageGenerator:
    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt"
        
    def _create_safe_prompt(self, prompt: str, mode: str) -> str:
        """Create safe prompt for Pollinations.ai."""
        unsafe_words = [
            "violence", "blood", "weapon", "gun", "knife", "attack", "fight", 
            "nude", "sex", "explicit", "adult", "horror", "scary", "terror",
            "kill", "murder", "death", "corpse", "zombie", "ghost", "demon",
            "nuclear", "bomb", "explosion", "war", "battle", "combat"
        ]
        
        safe_prompt = prompt.lower()
        for word in unsafe_words:
            safe_prompt = safe_prompt.replace(word, "scene")
        
        if mode == "podcast":
            return f"{safe_prompt} --ar 16:9 --quality high --style realistic --no violence, blood, weapons"
        else:  # shorts
            return f"{safe_prompt} --ar 9:16 --quality high --style cinematic --no violence, blood, weapons"
    
    def _generate_single_image(self, prompt: str, aspect_ratio: str, seq: int, mode: str) -> str:
        """Generate single image using Pollinations.ai API."""
        try:
            safe_prompt = self._create_safe_prompt(prompt, mode)
            encoded_prompt = quote(safe_prompt)
            url = f"{self.base_url}/{encoded_prompt}"
            
            logger.info(f"🎨 Generating image {seq} via Pollinations.ai...")
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            current_index = 1
            filename = f"{current_index}_{seq}.png"
            target_dir = Config.DATA_DIR / "images" / ("pod" if mode == "podcast" else "sor")
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename
            
            with open(target_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Image saved: {target_path}")
            return str(target_path)
            
        except Exception as e:
            logger.error(f"❌ Pollinations.ai image generation failed: {str(e)}")
            return None
    
    def generate_images_from_script(self, topic: str, script: str, mode: str, target_count: int = 20):
        """Generate images from script using Pollinations.ai."""
        try:
            if mode == "podcast":
                return self._generate_podcast_images(topic, script, target_count)
            else:  # shorts
                return self._generate_shorts_images(topic, script, target_count)
                
        except Exception as e:
            logger.error(f"❌ Pollinations.ai generation failed: {str(e)}")
            return self._generate_fallback_images(topic, mode, target_count)
    
    def _generate_podcast_images(self, topic: str, script: str, target_count: int) -> list:
        """Generate podcast images (default 25)."""
        images = []
        chapters = self._extract_chapters(script)
        
        # Generate from chapters (first 10 chapters for better coverage)
        for i, chapter in enumerate(chapters[:10]):
            prompt = f"A cinematic, documentary-style image representing '{chapter}'. Professional photography, realistic lighting, museum exhibit quality."
            img_path = self._generate_single_image(prompt, "16:9", i + 1, "podcast")
            if img_path:
                images.append(img_path)
            time.sleep(1)
        
        # Generate additional images to reach target count
        while len(images) < target_count:
            prompt = f"Professional overview image of '{topic}' showing multiple related elements. Documentary style, historical archive quality, cinematic lighting."
            img_path = self._generate_single_image(prompt, "16:9", len(images) + 1, "podcast")
            if img_path:
                images.append(img_path)
            time.sleep(1)
        
        return images[:target_count]
    
    def _generate_shorts_images(self, topic: str, script: str, target_count: int) -> list:
        """Generate shorts images (default 10)."""
        images = []
        lines = script.split('\n')
        
        for i in range(target_count):
            if i < len(lines) and lines[i].strip():
                segment = lines[i][:150]
                prompt = f"Eye-catching, vertical composition image representing: '{segment}'. Social media optimized, mobile friendly, cinematic quality."
            else:
                prompt = f"Engaging vertical image for '{topic}' - key moment or concept. Mobile optimized, social media friendly, professional quality."
            
            img_path = self._generate_single_image(prompt, "9:16", i + 1, "shorts")
            if img_path:
                images.append(img_path)
            time.sleep(1)
        
        return images[:target_count]
    
    def _extract_chapters(self, script: str) -> list:
        """Extract chapter titles from script."""
        chapters = []
        lines = script.split('\n')
        
        for line in lines:
            if line.strip().startswith('Chapter'):
                chapter_title = line.strip()
                if ':' in chapter_title:
                    chapter_title = chapter_title.split(':', 1)[1].strip()
                chapters.append(f"Chapter: {chapter_title}")
        
        return chapters if chapters else [f"Chapter 1: {script[:100]}..."]
    
    def _generate_fallback_images(self, topic: str, mode: str, target_count: int) -> list:
        """Generate fallback images if Pollinations fails."""
        import PIL.Image as Image
        import PIL.ImageDraw as ImageDraw
        import PIL.ImageFont as ImageFont
        
        images = []
        
        for i in range(target_count):
            filename = f"fallback_{mode}_{i+1}.png"
            target_dir = Config.DATA_DIR / "images" / ("pod" if mode == "podcast" else "sor")
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename
            
            width, height = (1920, 1080) if mode == "podcast" else (1080, 1920)
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), topic, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            draw.text((x, y), topic, fill='white', font=font)
            img.save(target_path)
            images.append(str(target_path))
        
        logger.warning(f"⚠️ Fallback images generated: {len(images)}")
        return images

def generate_daily_images():
    """Main function to generate images using Pollinations.ai."""
    generator = PollinationsImageGenerator()
    
    from src.utils import get_todays_idea
    from src.script_generator import generate_podcast_script, generate_shorts_script
    
    topic = get_todays_idea()
    podcast_script = generate_podcast_script(topic)
    shorts_script = generate_shorts_script(topic)
    
    podcast_images = generator.generate_images_from_script(topic, podcast_script, "podcast", 25)
    shorts_images = generator.generate_images_from_script(topic, shorts_script, "shorts", 10)
    
    logger.info(f"✅ Pollinations Images generated: {len(podcast_images)} podcast, {len(shorts_images)} shorts")
    
    return podcast_images, shorts_images

if __name__ == "__main__":
    generate_daily_images()
