#setup_firefox.py
import subprocess
import os
import platform
from pathlib import Path

def setup_firefox():
    """Setup Firefox browser for image generation."""
    try:
        print("🔧 Installing Firefox...")
        
        # Install Firefox
        if platform.system() == "Linux":
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "firefox"], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["brew", "install", "firefox"], check=True)
        else:
            print(f"❌ Unsupported platform: {platform.system()}")
            return False
        
        print("✅ Firefox installed successfully!")
        
        # Install geckodriver
        print("🔧 Installing geckodriver...")
        subprocess.run(["sudo", "apt-get", "install", "-y", "firefox-geckodriver"], check=True)
        
        print("✅ geckodriver installed!")
        
        # Verify installation
        result = subprocess.run(["firefox", "--version"], capture_output=True, text=True)
        print(f"✅ Firefox version: {result.stdout.strip()}")
        
        result = subprocess.run(["geckodriver", "--version"], capture_output=True, text=True)
        print(f"✅ geckodriver version: {result.stdout.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Firefox setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_firefox()
    if success:
        print("\n✅ Firefox setup completed successfully!")
        print("📝 You can now run: python -m src.firefox_image_generator")
    else:
        print("\n❌ Firefox setup failed!")
        exit(1)
