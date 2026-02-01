#!/usr/bin/env python3
"""
Test script to validate FastAPI middleware setup
"""
import sys
import asyncio
from fastapi.testclient import TestClient
from main import app

def test_middleware_setup():
    print("✓ FastAPI middleware setup validation")
    print(f"✓ Python version: {sys.version}")
    
    # Test FastAPI app
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    if response.status_code == 200:
        print("✓ Root endpoint working")
        print(f"✓ Response: {response.json()}")
    else:
        print(f"✗ Root endpoint failed: {response.status_code}")
    
    # Test health endpoint
    response = client.get("/health")
    if response.status_code == 200:
        print("✓ Health endpoint working")
        print(f"✓ Response: {response.json()}")
    else:
        print(f"✗ Health endpoint failed: {response.status_code}")
    
    print("\nMiddleware setup validation complete!")

if __name__ == "__main__":
    test_middleware_setup()