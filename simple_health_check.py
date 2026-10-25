#!/usr/bin/env python3
"""
Simple health check script for PocketPro:SBA Edition that doesn't require external packages
"""
import socket
import sys
import urllib.request
import urllib.error
import time
import json

BACKEND_HEALTH_URL = "http://localhost:5000/api/health"
FRONTEND_URL = "http://localhost:3000/"
CHROMA_HEALTH_URL = "http://localhost:8000/api/v1/heartbeat"


def check_service(name, url, timeout=10):
    """Check if a service is responding."""
    try:
        print(f"Checking {name} at {url}...")
        response = urllib.request.urlopen(url, timeout=timeout)
        if response.getcode() == 200:
            print(f"[OK] {name}: OK")
            return True
        else:
            print(f"[FAIL] {name}: HTTP {response.getcode()}")
            return False
    except urllib.error.URLError as e:
        print(f"[FAIL] {name}: Connection error - {e.reason}")
        return False
    except socket.timeout:
        print(f"[FAIL] {name}: Timeout")
        return False
    except Exception as e:
        print(f"[FAIL] {name}: Error - {e}")
        return False

def check_backend_health():
    """Check if the backend API is healthy."""
    return check_service("Backend API", BACKEND_HEALTH_URL)

def check_frontend():
    """Check if the frontend is available."""
    return check_service("Frontend", FRONTEND_URL)

def check_chroma():
    """Check if ChromaDB is available."""
    return check_service("ChromaDB", CHROMA_HEALTH_URL)

def main():
    """Run health checks for all services."""
    print("=======================================")
    print("PocketPro:SBA Edition Health Check")
    print("=======================================")
    
    results = {
        "Backend API": check_backend_health(),
        "Frontend": check_frontend(),
        "ChromaDB": check_chroma()
    }
    
    # Print summary
    print("\nSummary:")
    for service, result in results.items():
        status = "[OK] Healthy" if result else "[FAIL] Unhealthy"
        print(f"{service}: {status}")
    
    # Overall status
    if all(results.values()):
        print("\n[OK] All services are healthy!")
        return 0
    else:
        print("\n[FAIL] Some services are unhealthy!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
