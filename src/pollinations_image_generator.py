# src/pollinations_image_generator.py
"""
Multi-API Image Generator
=======================

Uses multiple image generation APIs with fallback
"""

import os
import time
import requests
from pathlib import Path
from urllib.parse import quote
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class MultiAPIImageGenerator:
    def __init__(self):
        self.apis = [
            {
                'name': 'pollinations',
                'url': 'https://image.pollinations.ai/prompt',
                'enabled': True
            },
            {
                'name': 'fallback',
                'url': None,
                'enabled': True
            }
        ]
        
    def _create_safe_prompt(self, prompt: str) -> str:
        """Create safe prompt without parameters."""
        unsafe_words = [
            "violence", "blood", "weapon", "gun", "knife", "attack", "fight", 
            "nude", "sex", "explicit", "adult", "horror", "scary", "terror",
            "kill", "murder", "death", "corpse", "zombie", "ghost", "demon",
            "nuclear", "bomb", "explosion", "war", "battle", "combat"
        ]
        
        safe_prompt = prompt.lower()
        for word in unsafe_words:
            safe_prompt = safe_prompt.replace(word, "scene")
        
        return safe_prompt
    
    def _try_generate_with_api(self, api_name: str, prompt: str, timeout: int = 30) -> bytes:
        """Try to generate image with specific API."""
        if api_name == 'pollinations':
            try:
                encoded_prompt = quote(prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response.content
            except Exception as e:
                logger.warning(f"Pollinations failed: {str(e)}")
                return None
        else:
            return None
    
    def _generate_single_image(self, prompt: str, seq: int, mode: str) -> str:
        """Generate single image with multi-API fallback."""
        safe_prompt = self._create_safe_prompt(prompt)
        
        # Try Pollinations first
        logger.info(f"🎨 Trying Pollinations.ai for image {seq}...")
        image_data = self._try_generate_with_api('pollinations', safe_prompt)
        
        if image_data is None:
            logger.warning(f"⚠️ Pollinations failed, using fallback for image {seq}")
            return self._generate_fallback_single_image(prompt, seq, mode)
        
        # Save successful image
        current_index = 1
        filename = f"{current_index}_{seq}.png"
        target_dir = Config.DATA_DIR / "images" / ("pod" if mode == "podcast" else "sor")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        
        with open(target_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"✅ Image saved: {target_path}")
        return str(target_path)
    
    def _generate_fallback_single_image(self, prompt: str, seq: int, mode: str) -> str:
        """Generate fallback image using PIL."""
        import PIL.Image as Image
        import PIL.ImageDraw as ImageDraw
        import PIL.ImageFont as ImageFont
        
        filename = f"fallback_{mode}_{seq}.png"
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
        
        # Create text from prompt
        display_text = prompt[:50] + "..." if len(prompt) > 50 else prompt
        
        bbox = draw.textbbox((0, 0), display_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), display_text, fill='white', font=font)
        img.save(target_path)
        
        logger.info(f"✅ Fallback image saved: {target_path}")
        return str(target_path)
    
    def generate_images_from_script(self, topic: str, script: str, mode: str, target_count: int = 20):
        """Generate images with multi-API fallback."""
        try:
            if mode == "podcast":
                return self._generate_podcast_images(topic, script, target_count)
            else:  # shorts
                return self._generate_shorts_images(topic, script, target_count)
                
        except Exception as e:
            logger.error(f"❌ Image generation failed: {str(e)}")
            return self._generate_fallback_images(topic, mode, target_count)
    
    def _generate_podcast_images(self, topic: str, script: str, target_count: int) -> list:
        """Generate podcast images with fallback."""
        images = []
        chapters = self._extract_chapters(script)
        
        # Generate from chapters
        for i, chapter in enumerate(chapters[:min(10, target_count)]):
            prompt = f"A cinematic, documentary-style image representing '{chapter}'. Professional photography, realistic lighting."
            img_path = self._generate_single_image(prompt, i + 1, "podcast")
            if img_path:
                images.append(img_path)
            time.sleep(1)
        
        # Generate additional images
        while len(images) < target_count:
            prompt = f"Professional overview image of '{topic}' showing multiple related elements. Documentary style."
            img_path = self._generate_single_image(prompt, len(images) + 1, "podcast")
            if img_path:
                images.append(img_path)
            time.sleep(1)
        
        return images[:target_count]
    
    def _generate_shorts_images(self, topic: str, script: str, target_count: int) -> list:
        """Generate shorts images with fallback."""
        images = []
        lines = script.split('\n')
        
        for i in range(target_count):
            if i < len(lines) and lines[i].strip():
                segment = lines[i][:150]
                prompt = f"Eye-catching vertical image representing: '{segment}'. Social media optimized."
            else:
                prompt = f"Engaging vertical image for '{topic}'. Mobile optimized."
            
            img_path = self._generate_single_image(prompt, i + 1, "shorts")
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
        """Generate all fallback images."""
        images = []
        for i in range(target_count):
            prompt = f"Fallback image {i+1} for {topic}"
            img_path = self._generate_fallback_single_image(prompt, i + 1, mode)
            images.append(img_path)
        return images

def generate_daily_images():
    """Main function to generate images."""
    generator = MultiAPIImageGenerator()
    
    from src.utils import get_todays_idea
    from src.script_generator import generate_podcast_script, generate_shorts_script
    
    topic = get_todays_idea()
    podcast_script = generate_podcast_script(topic)
    shorts_script = generate_shorts_script(topic)
    
    podcast_images = generator.generate_images_from_script(topic, podcast_script, "podcast", 25)
    shorts_images = generator.generate_images_from_script(topic, shorts_script, "shorts", 10)
    
    logger.info(f"✅ Images generated: {len(podcast_images)} podcast, {len(shorts_images)} shorts")
    
    return podcast_images, shorts_images

if __name__ == "__main__":
    generate_daily_images()
