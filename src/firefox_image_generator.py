# src/firefox_image_generator.py
"""
Firefox Image Generator - FIXED VERSION
=====================

Uses Firefox instead of Chrome for Qwen image generation
"""

import os
import time
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import RemoteConnection
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class FirefoxImageGenerator:
    def __init__(self):
        self.driver = None
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
    
    def _setup_firefox_driver(self):
        """Setup Firefox driver with maximum timeouts."""
        # ✅ CRITICAL: Set global connection timeout
        RemoteConnection.set_timeout(600)  # 10 minutes
        
        firefox_options = Options()
        firefox_options.add_argument("--headless")  # Background mode
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.add_argument("--disable-blink-features=AutomationControlled")
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        
        # Set Firefox internal timeouts
        firefox_options.set_preference("http.response.timeout", 600)  # 10 minutes
        firefox_options.set_preference("dom.max_script_run_time", 600)  # 10 minutes
        firefox_options.set_preference("dom.max_chrome_script_run_time", 600)  # 10 minutes
        
        # Set user agent
        firefox_options.set_preference("general.useragent.override", 
                                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
        
        # Create service
        service = Service("/usr/bin/geckodriver")
        
        # Create driver
        self.driver = webdriver.Firefox(service=service, options=firefox_options)
        
        # Set timeouts
        self.driver.implicitly_wait(60)
        self.driver.set_page_load_timeout(600)
        self.driver.set_script_timeout(600)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _smart_delay(self):
        """Add human-like random delay."""
        import random
        delay = 2 + random.uniform(0, 3)  # 2-5 seconds
        time.sleep(delay)
    
    def generate_images_from_script(self, topic: str, script: str, mode: str):
        """Generate images from script using Firefox."""
        try:
            # Decrypt credentials
            username, password = self._decrypt_credentials()
            
            # Setup Firefox driver
            self._setup_firefox_driver()
            
            # Login securely
            self._firefox_login(username, password)
            
            # Generate images based on script
            if mode == "podcast":
                return self._generate_podcast_images_firefox(topic, script)
            else:  # shorts
                return self._generate_shorts_images_firefox(topic, script)
                
        except Exception as e:
            logger.error(f"❌ Firefox image generation failed: {str(e)}")
            return self._generate_fallback_images(topic, mode)
        finally:
            if self.driver:
                try:
                    self.driver.close()  # ✅ Close current window first
                except:
                    pass
                try:
                    self.driver.quit()   # ✅ Then quit driver
                except:
                    pass
    
    def _firefox_login(self, username: str, password: str):
        """Firefox login with new UI flow."""
        self.driver.get("https://chat.qwen.ai")
        self._smart_delay()
        
        # Find and fill login fields
        email_input = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        password_input = self.driver.find_element(By.NAME, "password")
        
        # Human-like typing
        for char in username:
            email_input.send_keys(char)
            time.sleep(0.1)
        
        self._smart_delay()
        
        for char in password:
            password_input.send_keys(char)
            time.sleep(0.1)
        
        self._smart_delay()
        
        # Submit
        submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        
        # Wait for dashboard
        WebDriverWait(self.driver, 120).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '+')]"))
        )
    
    def _generate_podcast_images_firefox(self, topic: str, script: str) -> list:
        """Generate 20 podcast images using Firefox."""
        images = []
        
        # Extract chapters from script
        chapters = self._extract_chapters(script)
        
        # Generate prompt for each chapter
        for i, chapter in enumerate(chapters[:5]):  # First 5 chapters
            prompt = self._create_safe_prompt_from_chapter(chapter, topic, "podcast")
            img_path = self._generate_single_image_firefox(prompt, "16:9", i + 1)
            if img_path:
                images.append(img_path)
            self._smart_delay()
        
        # Fill remaining slots
        while len(images) < 20:
            overview_prompt = f"Professional overview image of '{topic}' showing multiple related elements. Documentary style. 16:9 aspect ratio."
            img_path = self._generate_single_image_firefox(overview_prompt, "16:9", len(images) + 1)
            if img_path:
                images.append(img_path)
            self._smart_delay()
        
        return images[:20]
    
    def _generate_shorts_images_firefox(self, topic: str, script: str) -> list:
        """Generate 6 shorts images using Firefox."""
        images = []
        
        lines = script.split('\n')
        
        for i in range(6):
            if i < len(lines) and lines[i].strip():
                segment = lines[i][:150]
                prompt = self._create_safe_prompt_from_content(segment, topic, "shorts")
            else:
                prompt = f"Engaging vertical image for '{topic}' - key moment or concept. Mobile optimized. 9:16 aspect ratio."
            
            img_path = self._generate_single_image_firefox(prompt, "9:16", i + 1)
            if img_path:
                images.append(img_path)
            self._smart_delay()
        
        return images[:6]
    
    def _generate_single_image_firefox(self, prompt: str, aspect_ratio: str, seq: int) -> str:
        """Generate single image using Firefox with dynamic waiting."""
        try:
            # Navigate to image generation
            self.driver.get("https://chat.qwen.ai")
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '+')]"))
            )
            
            # Click the + button
            plus_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '+')]")
            plus_btn.click()
            self._smart_delay()
            
            # Wait for dropdown menu and click "Create Image"
            create_image_btn = WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create Image')]"))
            )
            create_image_btn.click()
            
            # Wait for image generation interface
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "textarea"))
            )
            
            # Select aspect ratio
            try:
                selectors = [
                    f"//label[contains(text(), '{aspect_ratio}')]",
                    f"//button[contains(@aria-label, '{aspect_ratio}')]",
                    f"//div[contains(text(), '{aspect_ratio}')]",
                    f"//span[contains(text(), '{aspect_ratio}')]"
                ]
                
                selected = False
                for selector in selectors:
                    try:
                        ratio_btn = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        ratio_btn.click()
                        selected = True
                        break
                    except:
                        continue
                
                if not selected:
                    dropdowns = self.driver.find_elements(By.XPATH, "//select | //button[contains(@class, 'ratio')] | //div[contains(@role, 'combobox')]")
                    for dropdown in dropdowns:
                        try:
                            dropdown.click()
                            time.sleep(1)
                            ratio_options = self.driver.find_elements(By.XPATH, f"//option[contains(text(), '{aspect_ratio}')] | //div[contains(text(), '{aspect_ratio}')]")
                            if ratio_options:
                                ratio_options[0].click()
                                selected = True
                                break
                        except:
                            continue
            except:
                pass
            
            self._smart_delay()
            
            # Fill prompt
            prompt_input = self.driver.find_element(By.TAG_NAME, "textarea")
            for char in prompt:
                prompt_input.send_keys(char)
                time.sleep(0.05)
            
            self._smart_delay()
            
            # Generate
            generate_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Generate')] | //button[contains(text(), 'Create')]")
            generate_btn.click()
            
            # ✅ DYNAMIC WAITING INSTEAD OF time.sleep(120)
            logger.info(f"⏳ Waiting for image generation (sequence {seq})...")
            max_retries = 40  # 40 * 10s = 400s (~6.5 minutes)
            image_ready = False
            
            for i in range(max_retries):
                try:
                    download_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download')] | //button[contains(text(), 'Save')]"))
                    )
                    if download_btn:
                        image_ready = True
                        break
                except:
                    if i % 3 == 0:  # Log every 30 seconds
                        logger.info(f"   Still generating... ({(i+1)*10}s)")
                    continue
            
            if not image_ready:
                raise TimeoutError("Image generation took too long or failed on Qwen side.")
            
            # Download
            download_btn.click()
            
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
        """Create safe, detailed prompt from chapter."""
        safe_chapter = self._sanitize_text(chapter)
        safe_topic = self._sanitize_text(topic)
        
        if mode == "podcast":
            return f"A cinematic, documentary-style image representing '{safe_chapter}'. Professional photography, realistic lighting. 16:9 aspect ratio. No violence, no explicit content, no adult themes. Safe for all audiences."
        else:  # shorts
            return f"Eye-catching, vertical composition image representing: '{safe_chapter}'. Social media optimized. 9:16 aspect ratio. No violence, no explicit content, no adult themes. Safe for all audiences."
    
    def _create_safe_prompt_from_content(self, content: str, topic: str, mode: str) -> str:
        """Create safe prompt from content snippet."""
        safe_content = self._sanitize_text(content)
        safe_topic = self._sanitize_text(topic)
        
        if mode == "podcast":
            return f"Highly detailed visual representation of key elements from: '{safe_content}'. Museum exhibit style. 16:9 aspect ratio. No violence, no explicit content, no adult themes. Safe for all audiences."
        else:  # shorts
            return f"Engaging vertical image for content: '{safe_content}'. Mobile optimized. 9:16 aspect ratio. No violence, no explicit content, no adult themes. Safe for all audiences."
    
    def _sanitize_text(self, text: str) -> str:
        """Remove potentially problematic words."""
        unsafe_words = [
            "violence", "blood", "weapon", "gun", "knife", "attack", "fight", 
            "nude", "sex", "explicit", "adult", "horror", "scary", "terror",
            "kill", "murder", "death", "corpse", "zombie", "ghost", "demon",
            "nuclear", "bomb", "explosion", "war", "battle", "combat"
        ]
        
        sanitized = text.lower()
        for word in unsafe_words:
            sanitized = sanitized.replace(word, "scene")
        
        return sanitized
    
    def _generate_fallback_images(self, topic: str, mode: str) -> list:
        """Generate fallback images if secure generation fails."""
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

def generate_daily_images():
    """Main function to generate images using Firefox."""
    generator = FirefoxImageGenerator()
    
    from src.utils import get_todays_idea
    from src.script_generator import generate_podcast_script, generate_shorts_script
    
    topic = get_todays_idea()
    podcast_script = generate_podcast_script(topic)
    shorts_script = generate_shorts_script(topic)
    
    podcast_images = generator.generate_images_from_script(topic, podcast_script, "podcast")
    shorts_images = generator.generate_images_from_script(topic, shorts_script, "shorts")
    
    logger.info(f"✅ Firefox Images generated: {len(podcast_images)} podcast, {len(shorts_images)} shorts")
    
    return podcast_images, shorts_images

if __name__ == "__main__":
    generate_daily_images()
