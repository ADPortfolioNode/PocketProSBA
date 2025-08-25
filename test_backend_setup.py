#!/usr/bin/env python3
"""
Test script to verify backend setup and basic functionality
"""

import sys
import os
import subprocess
import requests
import time

def test_config_validation():
    """Test configuration validation"""
    try:
        # Import and test config
        sys.path.insert(0, "backend")
        from config import Config
        
        config = Config()
        config.validate()
        print("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    try:
        # Start the backend server in a subprocess
        backend_process = subprocess.Popen([
            sys.executable, "-m", "flask", "run",
            "--port", "5001",  # Use a different port to avoid conflicts
            "--debug"
        ], cwd="backend", env=os.environ.copy())
        
        # Wait for server to start
        time.sleep(3)
        
        # Test health endpoint
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Backend health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
        
        # Stop the server
        backend_process.terminate()
        backend_process.wait()
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running PocketPro SBA backend tests...\n")
    
    tests = [
        ("Configuration Validation", test_config_validation),
        ("Backend Health Check", test_backend_health),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print()
    
    print("📊 Test Results:")
    print("-" * 40)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("-" * 40)
    if all_passed:
        print("🎉 All tests passed! Backend is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
