#!/usr/bin/env python3
"""
Dynamic ChromeDriver Setup
=========================

Automatically detects Chrome version and downloads matching ChromeDriver
"""

import subprocess
import os
import platform
from pathlib import Path

def get_chrome_version():
    """Get installed Chrome version."""
    try:
        if platform.system() == "Linux":
            result = subprocess.run(['google-chrome', '--version'], 
                                  capture_output=True, text=True)
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], 
                                  capture_output=True, text=True)
        elif platform.system() == "Windows":
            result = subprocess.run(['chrome', '--version'], 
                                  capture_output=True, text=True)
        else:
            raise Exception(f"Unsupported platform: {platform.system()}")
        
        version_line = result.stdout.strip()
        # Parse version (e.g., "Google Chrome 145.0.7632.45")
        version = version_line.split()[2]  # "145.0.7632.45"
        major_version = version.split('.')[0]  # "145"
        
        print(f"✅ Chrome version detected: {version} (major: {major_version})")
        return major_version, version
    except Exception as e:
        print(f"❌ Could not detect Chrome version: {e}")
        return None, None

def get_latest_chromedriver_url():
    """Get the latest ChromeDriver URL from the new API."""
    import urllib.request
    import json
    
    try:
        # Use the new ChromeDriver API
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
        
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        # Get the latest stable version
        latest_version = data['channels']['Stable']['version']
        print(f"✅ Latest ChromeDriver version: {latest_version}")
        
        # Find Linux 64-bit download
        downloads = data['channels']['Stable']['downloads']['chromedriver']
        for download in downloads:
            if 'linux64' in download['platform']:
                print(f"✅ Found ChromeDriver download for {latest_version}")
                return download['url'], latest_version
        
        print("❌ No Linux ChromeDriver found")
        return None, None
    except Exception as e:
        print(f"❌ Could not fetch ChromeDriver: {e}")
        return None, None

def download_and_setup_chromedriver():
    """Download and setup ChromeDriver."""
    try:
        # Get ChromeDriver
        download_url, version = get_latest_chromedriver_url()
        if not download_url:
            print("❌ Cannot get ChromeDriver URL")
            return False
        
        print(f"📥 Downloading ChromeDriver {version}...")
        
        # Download
        import urllib.request
        urllib.request.urlretrieve(download_url, "chromedriver.zip")
        
        # Extract
        import zipfile
        with zipfile.ZipFile("chromedriver.zip", 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # Find and make executable
        import glob
        extracted_dirs = glob.glob("chromedriver-*")
        if extracted_dirs:
            extracted_dir = extracted_dirs[0]
            chromedriver_path = Path(extracted_dir) / "chromedriver"
        else:
            # Fallback to old naming
            chromedriver_path = Path("chromedriver-linux64/chromedriver")
        
        chromedriver_path.chmod(0o755)
        
        # Remove zip
        Path("chromedriver.zip").unlink()
        
        print(f"✅ ChromeDriver ready: {chromedriver_path}")
        
        # Remove old ChromeDriver from system
        os.system("sudo rm -f /usr/bin/chromedriver")
        os.system("sudo rm -f /usr/local/bin/chromedriver")
        
        # Copy to system path
        import shutil
        shutil.copy2(chromedriver_path, "/usr/local/bin/chromedriver")
        
        print("✅ ChromeDriver copied to system PATH")
        
        # Verify
        result = subprocess.run(["chromedriver", "--version"], capture_output=True, text=True)
        print(f"✅ ChromeDriver version: {result.stdout.strip()}")
        
        return True
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def setup_chromedriver():
    """Main setup function."""
    print("🔧 Setting up ChromeDriver...")
    
    # Remove existing ChromeDriver
    print("🧹 Removing existing ChromeDriver...")
    os.system("sudo rm -f /usr/bin/chromedriver")
    os.system("sudo rm -f /usr/local/bin/chromedriver")
    
    # Setup new ChromeDriver
    success = download_and_setup_chromedriver()
    
    if success:
        print("\n✅ ChromeDriver setup completed successfully!")
        print("📝 You can now run: python -m src.secure_image_generator")
        return True
    else:
        print("\n❌ ChromeDriver setup failed!")
        return False

if __name__ == "__main__":
    success = setup_chromedriver()
    if not success:
        exit(1)
