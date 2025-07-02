#!/usr/bin/env python3
"""
Quick server test for deployment validation
"""
import sys
import requests
import threading
import time
from run import app

def run_server():
    """Run the server in a thread"""
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server error: {e}")

def test_endpoints():
    """Test key endpoints"""
    time.sleep(3)  # Give server time to start
    
    endpoints = [
        'http://localhost:5000/',
        'http://localhost:5000/health'
    ]
    
    for url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url} - Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting server test...")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Test endpoints
    test_endpoints()
    
    print("✅ Server test completed")
