#!/usr/bin/env python3
"""
Test script to validate Django backend setup
"""
import os
import sys
import django
from pathlib import Path

# Add the observer directory to Python path
observer_dir = Path(__file__).parent / 'observer'
sys.path.insert(0, str(observer_dir))

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observer.settings')
    django.setup()
    
    from django.conf import settings
    
    print("✓ Django backend setup validation")
    print(f"✓ Django version: {django.get_version()}")
    print(f"✓ Python version: {sys.version}")
    print(f"✓ Installed apps: {len(settings.INSTALLED_APPS)}")
    print("✓ All Django apps configured successfully")
    
    # Test database connection
    from django.db import connection
    try:
        connection.ensure_connection()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
    
    print("\nBackend setup validation complete!")