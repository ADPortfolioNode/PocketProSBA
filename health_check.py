#!/usr/bin/env python3
"""
Health check and verification script for PocketPro:SBA Edition
"""
import urllib.request
import urllib.error
import socket
import sys
import time
import json

def check_service(name, url, timeout=10):
    """Check if a service is responding."""
    try:
        print(f"Checking {name} at {url}...")
        response = urllib.request.urlopen(url, timeout=timeout)
        if response.getcode() == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.getcode()}")
            return False
    except urllib.error.URLError as e:
        print(f"❌ {name}: Connection refused - {e.reason}")
        return False
    except socket.timeout:
        print(f"❌ {name}: Timeout")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def check_backend_health():
    """Check backend health endpoint."""
    try:
        response = urllib.request.urlopen("http://localhost:5000/health", timeout=10)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            print(f"✅ Backend Health: {data.get('status', 'unknown')}")
            services = data.get('services', {})
            for service, status in services.items():
                print(f"  - {service}: {status}")
            return True
        else:
            print(f"❌ Backend Health: HTTP {response.getcode()}")
            return False
    except Exception as e:
        print(f"❌ Backend Health: Error - {e}")
        return False

def main():
    """Run all health checks."""
    print("=== PocketPro:SBA Edition Health Check ===\n")
    
    services = [
        ("ChromaDB", "http://localhost:8000/api/v2/heartbeat"),
        ("Backend API", "http://localhost:5000/health"),
        ("Frontend", "http://localhost:10000")
    ]
    
    all_healthy = True
    
    for name, url in services:
        if not check_service(name, url):
            all_healthy = False
        time.sleep(1)  # Brief pause between checks
    
    print("\n=== Detailed Backend Health ===")
    if not check_backend_health():
        all_healthy = False
    
    print("\n=== Summary ===")
    if all_healthy:
        print("✅ All services are healthy!")
        sys.exit(0)
    else:
        print("❌ Some services are not responding correctly")
        print("\nTroubleshooting:")
        print("1. Make sure Docker containers are running: docker-compose ps")
        print("2. Check logs: docker-compose logs")
        print("3. Verify .env file has GEMINI_API_KEY set")
        sys.exit(1)

if __name__ == "__main__":
    main()
