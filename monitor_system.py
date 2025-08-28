#!/usr/bin/env python3
import os
import time
import requests
from datetime import datetime

def check_system_health():
    """Check system health endpoints"""
    base_url = os.environ.get('API_URL', 'http://localhost:5000')
    
    endpoints = [
        '/api/health',
        '/api/info',
        '/api/decompose'
    ]
    
    print(f"🔍 Monitoring system health at {base_url}")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint}: {response.status_code} - {response.json().get('status', '')}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

if __name__ == "__main__":
    while True:
        print(f"\\n📅 {datetime.now().isoformat()}")
        check_system_health()
        print("=" * 50)
        time.sleep(300)  # Check every 5 minutes
