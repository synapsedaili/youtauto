#setup_chromedriver.py
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

def get_chromedriver_url(major_version):
    """Get ChromeDriver download URL for specific major version."""
    # New ChromeDriver distribution API
    import urllib.request
    import json
    
    try:
        # ChromeDriver API endpoint
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        
        # urllib ile request at
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        # Find matching version (try exact match first)
        for version_info in data['versions']:
            if version_info['version'] == f"{major_version}.0.7632.45":  # Exact match
                downloads = version_info['downloads']['chromedriver']
                for download in downloads:
                    if 'linux64' in download['platform']:
                        print(f"✅ Found exact ChromeDriver: {version_info['version']}")
                        return download['url'], version_info['version']
        
        # If exact not found, find major version match
        for version_info in data['versions']:
            if version_info['version'].startswith(major_version + '.'):
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
        
        # urllib ile download
        import urllib.request
        urllib.request.urlretrieve(download_url, "chromedriver.zip")
        
        # Extract
        import zipfile
        with zipfile.ZipFile("chromedriver.zip", 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # Find extracted folder (usually chromedriver-linux64/)
        import glob
        extracted_dirs = glob.glob("chromedriver-*")
        if extracted_dirs:
            extracted_dir = extracted_dirs[0]
            chromedriver_path = Path(extracted_dir) / "chromedriver"
        else:
            chromedriver_path = Path("chromedriver-linux64/chromedriver")
        
        # Make executable
        chromedriver_path.chmod(0o755)
        
        # Remove zip
        Path("chromedriver.zip").unlink()
        
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
    
    # Verify installation
    try:
        subprocess.run([str(chromedriver_path), "--version"], check=True, capture_output=True)
        print("✅ ChromeDriver verification successful!")
    except:
        print("⚠️ ChromeDriver may not be accessible")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_chromedriver()
    if success:
        print("\n✅ Setup completed successfully!")
        print("📝 You can now run: python -m src.secure_image_generator")
    else:
        print("\n❌ Setup failed!")
        exit(1)
