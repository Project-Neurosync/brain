#!/usr/bin/env python3
"""
Debug script to test configuration loading
"""

import os
from config.settings import get_settings

def debug_config():
    """Debug configuration loading"""
    print("=== Configuration Debug ===")
    
    # Check environment variables directly
    print(f"DATABASE_URL from os.environ: {os.environ.get('DATABASE_URL', 'NOT SET')}")
    print(f"OPENAI_API_KEY from os.environ: {os.environ.get('OPENAI_API_KEY', 'NOT SET')}")
    
    # Check .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ .env file exists: {os.path.abspath(env_file)}")
        with open(env_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:20], 1):  # First 20 lines
                if 'DATABASE_URL' in line or 'OPENAI_API_KEY' in line:
                    print(f"Line {i}: {line.strip()}")
    else:
        print("❌ .env file not found")
    
    # Load settings and check values
    try:
        settings = get_settings()
        print(f"\n=== Settings Object ===")
        print(f"database_url: {settings.database_url}")
        print(f"openai_api_key: {'SET' if settings.openai_api_key else 'NOT SET'}")
        print(f"secret_key: {'SET' if settings.secret_key else 'NOT SET'}")
        
        # Check if it's reading from environment or using defaults
        if "localhost" in settings.database_url:
            print("⚠️  WARNING: Using localhost database URL (not reading from .env)")
        else:
            print("✅ Using custom database URL from environment")
            
    except Exception as e:
        print(f"❌ Error loading settings: {e}")

if __name__ == "__main__":
    debug_config()
