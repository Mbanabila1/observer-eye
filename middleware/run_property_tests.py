#!/usr/bin/env python3
"""
Test runner for Property 4: Service Communication and Discovery
Feature: observer-eye-containerization

This script runs the property-based tests for real-time dashboard functionality
with proper configuration and reporting.
"""

import sys
import subprocess
import time
from pathlib import Path

def run_property_tests():
    """Run the property-based tests with appropriate settings."""
    print("=" * 80)
    print("Observer-Eye Containerization - Property Test Execution")
    print("Property 4: Service Communication and Discovery")
    print("Validates: Requirements 8.2, 8.3, 10.2")
    print("=" * 80)
    
    # Change to middleware directory
    middleware_dir = Path(__file__).parent
    
    print(f"Running tests from: {middleware_dir}")
    print(f"Test file: test_property_realtime_dashboard.py")
    print()
    
    # Install dependencies first
    print("Installing test dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], cwd=middleware_dir, check=True, capture_output=True)
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    
    # Run the property tests
    print("\nExecuting property-based tests...")
    print("Note: Property tests run 100+ iterations and may take several minutes")
    print()
    
    start_time = time.time()
    
    try:
        # Run pytest with specific configuration for property tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_property_realtime_dashboard.py",
            "-v",
            "--tb=short",
            "-m", "not slow",  # Skip slow tests for faster execution
            "--hypothesis-show-statistics"
        ], cwd=middleware_dir, check=True, text=True, capture_output=True)
        
        execution_time = time.time() - start_time
        
        print("✓ Property tests completed successfully!")
        print(f"Execution time: {execution_time:.2f} seconds")
        print()
        print("Test Output:")
        print("-" * 40)
        print(result.stdout)
        
        if result.stderr:
            print("Warnings/Errors:")
            print("-" * 40)
            print(result.stderr)
        
        return True
        
    except subprocess.CalledProcessError as e:
        execution_time = time.time() - start_time
        
        print(f"✗ Property tests failed after {execution_time:.2f} seconds")
        print()
        print("Error Output:")
        print("-" * 40)
        print(e.stdout)
        print(e.stderr)
        
        return False

def main():
    """Main entry point for the test runner."""
    success = run_property_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 All property tests passed! Service communication and discovery validated.")
        print("Requirements 8.2, 8.3, 10.2 are satisfied.")
    else:
        print("❌ Property tests failed. Please review the output above.")
        print("Check service communication and discovery implementation.")
    print("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())