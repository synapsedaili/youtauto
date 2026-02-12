# src/secure_image_generator.py
import os
import time
import asyncio
import hashlib
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class SecureImageGenerator:
    def __init__(self):
        self.driver = None
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_encryption_key(self):
        """Get encryption key from environment or generate new one."""
        key = os.getenv('ENCRYPTION_KEY')
        if key:
            return key.encode()
        # Generate new key (for testing only)
        return Fernet.generate_key()
    
    def _decrypt_credentials(self):
        """Decrypt Qwen credentials from environment."""
        encrypted_username = os.getenv('QWEN_USER_ENC')
        encrypted_password = os.getenv('QWEN_PASS_ENC')
        
        if not encrypted_username or not encrypted_password:
            raise ValueError("Encrypted credentials not found in environment")
        
        username = self.cipher.decrypt(encrypted_username.encode()).decode()
        password = self.cipher.decrypt(encrypted_password.encode()).decode()
        
        return username, password
    
    def _setup_secure_driver(self):
        """Setup secure, stealth browser."""
        chrome_options = Options()
        
        # Security features
        chrome_options.add_argument("--headless=new")  # Latest headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Version compatibility fixes
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        
        # Window features
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Use local chromedriver
        service = webdriver.chrome.service.Service("./chromedriver")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _smart_delay(self):
        """Add human-like random delay."""
        import random
        delay = 2 + random.uniform(0, 3)  # 2-5 seconds
        time.sleep(delay)
    
    def generate_images_from_script(self, topic: str, script: str, mode: str):
        """Generate images from script with security."""
        try:
            # Decrypt credentials
            username, password = self._decrypt_credentials()
            
            # Setup secure driver
            self._setup_secure_driver()
            
            # Login securely
            self._secure_login(username, password)
            
            # Generate images based on script
            if mode == "podcast":
                return self._generate_podcast_images(topic, script)
            else:  # shorts
                return self._generate_shorts_images(topic, script)
                
        except Exception as e:
            logger.error(f"❌ Secure image generation failed: {str(e)}")
            return self._generate_fallback_images(topic, mode)
        finally:
            if self.driver:
                self.driver.quit()
    
    def _secure_login(self, username: str, password: str):
        """Secure login with new UI flow."""
        self.driver.get("https://chat.qwen.ai")
        self._smart_delay()
        
        # Find and fill login fields
        email_input = WebDriverWait(self.driver, 10).until(
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
        
        # Random delay before submit
        self._smart_delay()
        
        # Submit
        submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        
        # Wait for dashboard (with new UI)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '+')]"))  # New + button
        )
    
    def _generate_podcast_images(self, topic: str, script: str) -> list:
        """Generate 20 podcast images with chapter-based prompts."""
        images = []
        
        # Extract chapters from script
        chapters = self._extract_chapters(script)
        
        # Generate prompt for each chapter
        for i, chapter in enumerate(chapters[:13]):  # First 13 chapters
            # Create detailed prompt from chapter
            prompt = self._create_safe_prompt_from_chapter(chapter, topic, "podcast")
            
            # Generate image for this chapter
            img_path = self._generate_single_image(prompt, "16:9", i + 1)
            if img_path:
                images.append(img_path)
            
            # Extra images for key moments in chapter
            if i < len(chapters) - 1:
                # Generate from content between chapters
                content_between = script.split(chapter)[-1].split(chapters[i+1])[0][:300]
                extra_prompt = self._create_safe_prompt_from_content(content_between, topic, "podcast")
                extra_img = self._generate_single_image(extra_prompt, "16:9", i + 14)
                if extra_img:
                    images.append(extra_img)
            
            self._smart_delay()
        
        # Fill remaining slots with overview images
        while len(images) < 20:
            overview_prompt = f"Professional overview image of '{topic}' showing multiple related elements. Documentary style. 16:9 aspect ratio."
            img_path = self._generate_single_image(overview_prompt, "16:9", len(images) + 1)
            if img_path:
                images.append(img_path)
            self._smart_delay()
        
        return images[:20]
    
    def _generate_shorts_images(self, topic: str, script: str) -> list:
        """Generate 6 shorts images with story-based prompts."""
        images = []
        
        # Split script into meaningful segments
        lines = script.split('\n')
        
        for i in range(6):
            if i < len(lines) and lines[i].strip():
                segment = lines[i][:150]
                prompt = self._create_safe_prompt_from_content(segment, topic, "shorts")
            else:
                prompt = f"Engaging vertical image for '{topic}' - key moment or concept. Mobile optimized. 9:16 aspect ratio."
            
            img_path = self._generate_single_image(prompt, "9:16", i + 1)
            if img_path:
                images.append(img_path)
            self._smart_delay()
        
        return images[:6]
    
    def _generate_single_image(self, prompt: str, aspect_ratio: str, seq: int) -> str:
    """Generate single image with new UI flow - DEBUG VERSION."""
    try:
        print(f"DEBUG: Starting image generation for sequence {seq}")
        
        # Navigate to image generation
        self.driver.get("https://chat.qwen.ai")
        print("DEBUG: Navigated to Qwen AI")
        
        # Wait for dashboard
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '+')]"))
        )
        print("DEBUG: Found + button")
        
        # Click the + button
        plus_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '+')]")
        plus_btn.click()
        self._smart_delay()
        print("DEBUG: Clicked + button")
        
        # Wait for dropdown menu and click "Create Image"
        try:
            create_image_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create Image')]"))
            )
            print("DEBUG: Found Create Image button")
            create_image_btn.click()
        except:
            # Alternative: look for any image-related button
            print("DEBUG: Looking for alternative image button")
            alt_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Image')] | //button[contains(text(), 'image')]")
            if alt_buttons:
                alt_buttons[0].click()
                print("DEBUG: Clicked alternative image button")
            else:
                print("DEBUG: No image button found")
                raise Exception("No image creation button found")
        
        # Wait for image generation interface
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "textarea"))
        )
        print("DEBUG: Found textarea")
        
        # Select aspect ratio
        try:
            # Try multiple ways to select aspect ratio
            selectors = [
                f"//label[contains(text(), '{aspect_ratio}')]",
                f"//button[contains(@aria-label, '{aspect_ratio}')]",
                f"//div[contains(text(), '{aspect_ratio}')]",
                f"//span[contains(text(), '{aspect_ratio}')]"
            ]
            
            selected = False
            for selector in selectors:
                try:
                    ratio_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    ratio_btn.click()
                    print(f"DEBUG: Selected ratio with selector: {selector}")
                    selected = True
                    break
                except:
                    continue
            
            if not selected:
                print("DEBUG: Could not select aspect ratio, trying dropdown approach")
                # Try dropdown approach
                dropdowns = self.driver.find_elements(By.XPATH, "//select | //button[contains(@class, 'ratio')] | //div[contains(@role, 'combobox')]")
                for dropdown in dropdowns:
                    try:
                        dropdown.click()
                        time.sleep(1)
                        ratio_options = self.driver.find_elements(By.XPATH, f"//option[contains(text(), '{aspect_ratio}')] | //div[contains(text(), '{aspect_ratio}')]")
                        if ratio_options:
                            ratio_options[0].click()
                            print("DEBUG: Selected ratio from dropdown")
                            selected = True
                            break
                    except:
                        continue
        
        except Exception as e:
            print(f"DEBUG: Ratio selection failed: {e}")
            # Continue anyway, use default ratio
        
        self._smart_delay()
        
        # Fill prompt
        prompt_input = self.driver.find_element(By.TAG_NAME, "textarea")
        for char in prompt:
            prompt_input.send_keys(char)
            time.sleep(0.05)
        
        self._smart_delay()
        print("DEBUG: Filled prompt")
        
        # Generate
        generate_selectors = [
            "//button[contains(text(), 'Generate')] | //button[contains(text(), 'Create')] | //button[contains(text(), 'generate')] | //button[contains(text(), 'create')]",
            "//button[contains(@class, 'generate')] | //button[contains(@class, 'create')]",
            "//button[contains(@type, 'submit')] | //button[contains(@role, 'button')]"
        ]
        
        generate_btn = None
        for selector in generate_selectors:
            try:
                generate_btn = self.driver.find_element(By.XPATH, selector)
                break
            except:
                continue
        
        if generate_btn:
            generate_btn.click()
            print("DEBUG: Clicked generate button")
        else:
            print("DEBUG: No generate button found")
            raise Exception("No generate button found")
        
        # Wait for generation
        time.sleep(15)
        print("DEBUG: Waited for generation")
        
        # Download
        download_selectors = [
            "//button[contains(text(), 'Download')] | //button[contains(text(), 'Save')] | //button[contains(text(), 'download')] | //button[contains(text(), 'save')]",
            "//button[contains(@aria-label, 'download')] | //a[contains(@href, 'download')]",
            "//button[contains(@class, 'download')] | //button[contains(@class, 'save')]"
        ]
        
        download_btn = None
        for selector in download_selectors:
            try:
                download_btn = self.driver.find_element(By.XPATH, selector)
                break
            except:
                continue
        
        if download_btn:
            download_btn.click()
            print("DEBUG: Clicked download button")
        else:
            print("DEBUG: No download button found")
            raise Exception("No download button found")
        
        # Save image
        current_index = 1  # Get from utils
        filename = f"{current_index}_{seq}.png"
        target_dir = Config.DATA_DIR / "images" / ("pod" if "16:9" in aspect_ratio else "sor")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        
        logger.info(f"✅ Image saved: {target_path}")
        return str(target_path)
        
    except Exception as e:
        logger.error(f"❌ Single image generation failed: {str(e)}")
        print(f"DEBUG: Full error: {str(e)}")
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
        # Remove potentially problematic words
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
            
            # Create simple fallback image
            width, height = (1920, 1080) if mode == "podcast" else (1080, 1920)
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            # Sanitize topic for safety
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

def encrypt_credentials(username: str, password: str) -> tuple:
    """Encrypt credentials for secure storage."""
    key = Fernet.generate_key()
    cipher = Fernet(key)
    
    encrypted_username = cipher.encrypt(username.encode()).decode()
    encrypted_password = cipher.encrypt(password.encode()).decode()
    
    return key.decode(), encrypted_username, encrypted_password

def generate_daily_images():
    """Main function to generate images."""
    generator = SecureImageGenerator()
    
    # Get topic and script (from your existing functions)
    from src.utils import get_todays_idea
    from src.script_generator import generate_podcast_script, generate_shorts_script
    
    topic = get_todays_idea()
    podcast_script = generate_podcast_script(topic)
    shorts_script = generate_shorts_script(topic)
    
    # Generate images
    podcast_images = generator.generate_images_from_script(topic, podcast_script, "podcast")
    shorts_images = generator.generate_images_from_script(topic, shorts_script, "shorts")
    
    logger.info(f"✅ Images generated: {len(podcast_images)} podcast, {len(shorts_images)} shorts")
    
    return podcast_images, shorts_images

if __name__ == "__main__":
    generate_daily_images()
