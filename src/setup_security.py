# setup_security.py
"""
Security Setup Script
===================

Encrypt credentials and generate secure configuration
"""

from src.secure_image_generator import encrypt_credentials
import os

def setup_encrypted_credentials():
    """Setup encrypted credentials."""
    username = input("Enter Qwen email: ")
    password = input("Enter Qwen password: ")
    
    key, encrypted_user, encrypted_pass = encrypt_credentials(username, password)
    
    print("\n🔐 ENCRYPTED CREDENTIALS (copy to GitHub Secrets):")
    print(f"ENCRYPTION_KEY={key}")
    print(f"QWEN_USER_ENC={encrypted_user}")
    print(f"QWEN_PASS_ENC={encrypted_pass}")
    
    print("\n📋 Instructions:")
    print("1. Go to GitHub → Settings → Secrets and Variables → Actions")
    print("2. Add the above 3 secrets")
    print("3. Never commit these values to git!")

if __name__ == "__main__":
    setup_encrypted_credentials()