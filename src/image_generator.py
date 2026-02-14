# src/image_generator.py
"""
Playwright Image Generator
========================

Uses Playwright with stealth plugin for Qwen image generation
"""

import os
import time
import asyncio
from pathlib import Path
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class PlaywrightImageGenerator:
    def __init__(self):
        self.browser = None
        self.page = None
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_encryption_key(self):
        """Get encryption key from environment."""
        key = os.getenv('ENCRYPTION_KEY')
        if key:
            return key.encode()
        return Fernet.generate_key()
    
    def _decrypt_credentials(self):
        """Decrypt Qwen credentials."""
        encrypted_username = os.getenv('QWEN_USER_ENC')
        encrypted_password = os.getenv('QWEN_PASS_ENC')
        
        if not encrypted_username or not encrypted_password:
            raise ValueError("Encrypted credentials not found in environment")
        
        username = self.cipher.decrypt(encrypted_username.encode()).decode()
        password = self.cipher.decrypt(encrypted_password.encode()).decode()
        
        return username, password
    
    async def _setup_browser(self):
        """Setup stealth browser."""
        self.playwright = await async_playwright().start()
        
        # Launch browser with stealth
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        
        # Create context with realistic settings
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['notifications'],
            java_script_enabled=True,
            bypass_csp=True
        )
        
        self.page = await context.new_page()
        
        # Apply stealth
        await stealth_async(self.page)
    
    async def _login(self, username: str, password: str):
        """Login to Qwen AI."""
        await self.page.goto("https://chat.qwen.ai/login")
        await self.page.wait_for_load_state("networkidle")
        
        # Fill login form
        await self.page.fill('input[name="email"]', username)
        await self.page.fill('input[name="password"]', password)
        
        # Human-like delay
        await asyncio.sleep(2 + (time.time() % 3))
        
        # Submit
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")
        
        # Wait for dashboard
        await self.page.wait_for_selector('//button[contains(text(), "+")]')
    
    async def generate_images_from_script(self, topic: str, script: str, mode: str):
        """Generate images from script using Playwright."""
        try:
            # Decrypt credentials
            username, password = self._decrypt_credentials()
            
            # Setup browser
            await self._setup_browser()
            
            # Login
            await self._login(username, password)
            
            # Generate images
            if mode == "podcast":
                return await self._generate_podcast_images(topic, script)
            else:
                return await self._generate_shorts_images(topic, script)
                
        except Exception as e:
            logger.error(f"❌ Playwright image generation failed: {str(e)}")
            return self._generate_fallback_images(topic, mode)
        finally:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
    
    async def _generate_single_image(self, prompt: str, aspect_ratio: str, seq: int) -> str:
        """Generate single image using Playwright."""
        try:
            # Navigate to Qwen AI
            await self.page.goto("https://chat.qwen.ai")
            await self.page.wait_for_selector('//button[contains(text(), "+")]')
            
            # Click + button
            await self.page.click('//button[contains(text(), "+")]')
            await asyncio.sleep(2)
            
            # Click Create Image
            await self.page.wait_for_selector('//button[contains(text(), "Create Image")]')
            await self.page.click('//button[contains(text(), "Create Image")]')
            
            # Wait for textarea
            await self.page.wait_for_selector('textarea')
            
            # Select aspect ratio
            try:
                await self.page.click(f'//label[contains(text(), "{aspect_ratio}")]')
            except:
                try:
                    await self.page.click(f'//button[contains(@aria-label, "{aspect_ratio}")]')
                except:
                    pass
            
            await asyncio.sleep(1)
            
            # Fill prompt
            await self.page.fill('textarea', prompt)
            await asyncio.sleep(1)
            
            # Generate
            try:
                await self.page.click('//button[contains(text(), "Generate")]')
            except:
                await self.page.click('//button[contains(text(), "Create")]')
            
            # Wait for download button with dynamic waiting
            logger.info(f"⏳ Waiting for image generation (sequence {seq})...")
            max_retries = 40
            image_ready = False
            
            for i in range(max_retries):
                try:
                    await self.page.wait_for_selector('//button[contains(text(), "Download")]', timeout=10000)
                    image_ready = True
                    break
                except:
                    if i % 3 == 0:
                        logger.info(f"   Still generating... ({(i+1)*10}s)")
                    continue
            
            if not image_ready:
                raise TimeoutError("Image generation took too long")
            
            # Download
            await self.page.click('//button[contains(text(), "Download")]')
            
            # Save image
            current_index = 1
            filename = f"{current_index}_{seq}.png"
            target_dir = Config.DATA_DIR / "images" / ("pod" if "16:9" in aspect_ratio else "sor")
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename
            
            logger.info(f"✅ Image saved: {target_path}")
            return str(target_path)
            
        except Exception as e:
            logger.error(f"❌ Single image generation failed: {str(e)}")
            return None
    
    async def _generate_podcast_images(self, topic: str, script: str) -> list:
        """Generate podcast images."""
        images = []
        chapters = self._extract_chapters(script)
        
        for i, chapter in enumerate(chapters[:5]):
            prompt = self._create_safe_prompt_from_chapter(chapter, topic, "podcast")
            img_path = await self._generate_single_image(prompt, "16:9", i + 1)
            if img_path:
                images.append(img_path)
            await asyncio.sleep(2)
        
        while len(images) < 20:
            overview_prompt = f"Professional overview image of '{topic}' showing multiple related elements. Documentary style. 16:9 aspect ratio."
            img_path = await self._generate_single_image(overview_prompt, "16:9", len(images) + 1)
            if img_path:
                images.append(img_path)
            await asyncio.sleep(2)
        
        return images[:20]
    
    async def _generate_shorts_images(self, topic: str, script: str) -> list:
        """Generate shorts images."""
        images = []
        lines = script.split('\n')
        
        for i in range(6):
            if i < len(lines) and lines[i].strip():
                segment = lines[i][:150]
                prompt = self._create_safe_prompt_from_content(segment, topic, "shorts")
            else:
                prompt = f"Engaging vertical image for '{topic}' - key moment or concept. Mobile optimized. 9:16 aspect ratio."
            
            img_path = await self._generate_single_image(prompt, "9:16", i + 1)
            if img_path:
                images.append(img_path)
            await asyncio.sleep(2)
        
        return images[:6]
    
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
    
    def _create_safe_prompt_from_chapter(self, chapter: str, topic: str, mode: str) -> str:
        """Create safe prompt from chapter."""
        safe_chapter = self._sanitize_text(chapter)
        if mode == "podcast":
            return f"A cinematic, documentary-style image representing '{safe_chapter}'. Professional photography, realistic lighting. 16:9 aspect ratio. No violence, no explicit content, no adult themes."
        else:
            return f"Eye-catching, vertical composition image representing: '{safe_chapter}'. Social media optimized. 9:16 aspect ratio. No violence, no explicit content, no adult themes."
    
    def _create_safe_prompt_from_content(self, content: str, topic: str, mode: str) -> str:
        """Create safe prompt from content."""
        safe_content = self._sanitize_text(content)
        if mode == "podcast":
            return f"Highly detailed visual representation of key elements from: '{safe_content}'. Museum exhibit style. 16:9 aspect ratio. No violence, no explicit content, no adult themes."
        else:
            return f"Engaging vertical image for content: '{safe_content}'. Mobile optimized. 9:16 aspect ratio. No violence, no explicit content, no adult themes."
    
    def _sanitize_text(self, text: str) -> str:
        """Remove potentially problematic words."""
        unsafe_words = ["violence", "blood", "weapon", "gun", "knife", "attack", "fight", "nude", "sex", "explicit", "adult", "horror", "scary", "terror", "kill", "murder", "death", "corpse", "zombie", "ghost", "demon", "nuclear", "bomb", "explosion", "war", "battle", "combat"]
        sanitized = text.lower()
        for word in unsafe_words:
            sanitized = sanitized.replace(word, "scene")
        return sanitized
    
    def _generate_fallback_images(self, topic: str, mode: str) -> list:
        """Generate fallback images."""
        import PIL.Image as Image
        import PIL.ImageDraw as ImageDraw
        import PIL.ImageFont as ImageFont
        
        images = []
        count = 20 if mode == "podcast" else 6
        
        for i in range(count):
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
            
            safe_topic = self._sanitize_text(topic)
            bbox = draw.textbbox((0, 0), safe_topic, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            draw.text((x, y), safe_topic, fill='white', font=font)
            img.save(target_path)
            images.append(str(target_path))
        
        logger.warning(f"⚠️ Fallback images generated: {len(images)}")
        return images

async def generate_daily_images_async():
    """Async main function."""
    generator = PlaywrightImageGenerator()
    
    from src.utils import get_todays_idea
    from src.script_generator import generate_podcast_script, generate_shorts_script
    
    topic = get_todays_idea()
    podcast_script = generate_podcast_script(topic)
    shorts_script = generate_shorts_script(topic)
    
    podcast_images = await generator.generate_images_from_script(topic, podcast_script, "podcast")
    shorts_images = await generator.generate_images_from_script(topic, shorts_script, "shorts")
    
    logger.info(f"✅ Playwright Images generated: {len(podcast_images)} podcast, {len(shorts_images)} shorts")
    
    return podcast_images, shorts_images

def generate_daily_images():
    """Sync wrapper for async function."""
    return asyncio.run(generate_daily_images_async())

if __name__ == "__main__":
    generate_daily_images()
