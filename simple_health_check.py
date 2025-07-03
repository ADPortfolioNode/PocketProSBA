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
        print(f"❌ {name}: Connection error - {e.reason}")
        return False
    except socket.timeout:
        print(f"❌ {name}: Timeout")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def check_backend_health():
    """Check if the backend API is healthy."""
    return check_service("Backend API", "http://localhost:5000/health")

def check_docker_backend_health():
    """Check if the Docker backend API is healthy."""
    return check_service("Docker Backend API", "http://localhost:10000/health")

def check_frontend():
    """Check if the frontend is available."""
    return check_service("Frontend", "http://localhost:3000")

def check_chroma():
    """Check if ChromaDB is available."""
    return check_service("ChromaDB", "http://localhost:8000/api/v2/heartbeat")

def main():
    """Run health checks for all services."""
    print("=======================================")
    print("PocketPro:SBA Edition Health Check")
    print("=======================================")
    
    results = {
        "Backend API": check_backend_health(),
        "Docker Backend API": check_docker_backend_health(),
        "Frontend": check_frontend(),
        "ChromaDB": check_chroma()
    }
    
    # Print summary
    print("\nSummary:")
    for service, result in results.items():
        status = "✅ Healthy" if result else "❌ Unhealthy"
        print(f"{service}: {status}")
    
    # Overall status
    if all(results.values()):
        print("\n✅ All services are healthy!")
        return 0
    else:
        print("\n❌ Some services are unhealthy!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
