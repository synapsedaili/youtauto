#setup_firefox.py
import subprocess
import os
import platform
import requests
import zipfile
from pathlib import Path

def setup_firefox():
    """Setup Firefox browser for image generation."""
    try:
        print("🔧 Installing Firefox...")
        
        # Install Firefox
        if platform.system() == "Linux":
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "firefox"], check=True)
        else:
            print(f"❌ Unsupported platform: {platform.system()}")
            return False
        
        print("✅ Firefox installed successfully!")
        
        # Manually download and install geckodriver
        print("🔧 Downloading geckodriver...")
        
        # Detect system architecture
        arch = platform.machine()
        if arch == "x86_64":
            gecko_url = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz"
        elif arch in ["arm64", "aarch64"]:
            gecko_url = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux-aarch64.tar.gz"
        else:
            print(f"❌ Unsupported architecture: {arch}")
            return False
        
        # Download geckodriver
        import urllib.request
        urllib.request.urlretrieve(gecko_url, "geckodriver.tar.gz")
        
        # Extract
        import tarfile
        with tarfile.open("geckodriver.tar.gz", 'r:gz') as tar:
            tar.extractall('.')
        
        # Make executable
        geckodriver_path = Path("geckodriver")
        geckodriver_path.chmod(0o755)
        
        # Move to system path
        subprocess.run(["sudo", "mv", "geckodriver", "/usr/local/bin/geckodriver"], check=True)
        
        # Remove archive
        Path("geckodriver.tar.gz").unlink()
        
        print("✅ geckodriver installed!")
        
        # Verify installation
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
