#!/usr/bin/env python3
"""
Dynamic ChromeDriver Setup
=========================

Automatically detects Chrome version and downloads matching ChromeDriver
"""

import subprocess
import requests
import zipfile
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

def get_chromedriver_url(major_version):
    """Get ChromeDriver download URL for specific major version."""
    # New ChromeDriver distribution API
    api_url = f"https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        # Find matching version
        for version_info in data['versions']:
            if version_info['version'].startswith(major_version + '.'):
                # Look for Linux 64-bit download
                downloads = version_info['downloads']['chromedriver']
                for download in downloads:
                    if 'linux64' in download['platform']:
                        print(f"✅ Found ChromeDriver: {version_info['version']}")
                        return download['url'], version_info['version']
        
        print(f"❌ No ChromeDriver found for major version {major_version}")
        return None, None
    except Exception as e:
        print(f"❌ Could not fetch ChromeDriver info: {e}")
        return None, None

def download_chromedriver(download_url, version):
    """Download and extract ChromeDriver."""
    try:
        print(f"📥 Downloading ChromeDriver {version}...")
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Save zip file
        zip_path = Path("chromedriver.zip")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # Make executable
        chromedriver_path = Path("chromedriver-linux64/chromedriver")
        chromedriver_path.chmod(0o755)
        
        # Remove zip
        zip_path.unlink()
        
        print(f"✅ ChromeDriver installed: {chromedriver_path}")
        return str(chromedriver_path)
    except Exception as e:
        print(f"❌ Could not download ChromeDriver: {e}")
        return None

def setup_chromedriver():
    """Main setup function."""
    print("🔧 Setting up ChromeDriver...")
    
    # Get Chrome version
    major_version, full_version = get_chrome_version()
    if not major_version:
        print("❌ Cannot proceed without Chrome version")
        return False
    
    # Get ChromeDriver URL
    download_url, driver_version = get_chromedriver_url(major_version)
    if not download_url:
        print("❌ Cannot find compatible ChromeDriver")
        return False
    
    # Download ChromeDriver
    chromedriver_path = download_chromedriver(download_url, driver_version)
    if not chromedriver_path:
        print("❌ Failed to download ChromeDriver")
        return False
    
    # Add to PATH
    current_path = os.environ.get('PATH', '')
    new_path = f"{os.getcwd()}:{current_path}"
    os.environ['PATH'] = new_path
    
    print(f"🚀 ChromeDriver ready! Available at: {chromedriver_path}")
    print(f"📋 PATH updated: {new_path}")
    
    return True

if __name__ == "__main__":
    success = setup_chromedriver()
    if success:
        print("\n✅ Setup completed successfully!")
        print("📝 You can now run: python -m src.secure_image_generator")
    else:
        print("\n❌ Setup failed!")
        exit(1)