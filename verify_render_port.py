#!/usr/bin/env python3
"""
Port verification script for Render.com deployments
This script checks if the application is correctly binding to the PORT
environment variable provided by Render.com
"""
import os
import sys
import requests
import json
import time
import socket

def check_port_binding(port=None):
    """
    Check if the port is correctly bound by the application
    """
    if port is None:
        port = os.environ.get('PORT', 5000)
    
    try:
        port = int(port)
    except ValueError:
        print(f"❌ Invalid port value: {port}")
        return False
    
    print(f"🔍 Checking if application is bound to port {port}")
    
    # Try to connect to the port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    
    try:
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            print(f"✅ Successfully connected to port {port}")
            return True
        else:
            print(f"❌ Failed to connect to port {port} (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Error checking port {port}: {e}")
        return False
    finally:
        sock.close()

def check_health_endpoint(port=None):
    """
    Check if the health endpoint is responding
    """
    if port is None:
        port = os.environ.get('PORT', 5000)
    
    try:
        port = int(port)
    except ValueError:
        print(f"❌ Invalid port value: {port}")
        return False
    
    url = f"http://localhost:{port}/health"
    print(f"🔍 Checking health endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def check_port_debug_endpoint(port=None):
    """
    Check the port-debug endpoint for more information
    """
    if port is None:
        port = os.environ.get('PORT', 5000)
    
    try:
        port = int(port)
    except ValueError:
        print(f"❌ Invalid port value: {port}")
        return False
    
    url = f"http://localhost:{port}/port-debug"
    print(f"🔍 Checking port-debug endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Port debug information:")
            print(f"   Configured Port: {data.get('configured_port', 'unknown')}")
            print(f"   Environment Variables:")
            for key, value in data.get('environment_variables', {}).items():
                print(f"      {key}: {value}")
            return True
        else:
            print(f"❌ Port debug check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Port debug check failed: {e}")
        return False

def main():
    """
    Main function
    """
    print("🚀 Render.com Port Verification")
    print(f"⚙️  Environment:")
    print(f"   PORT: {os.environ.get('PORT', 'Not set')}")
    print(f"   FLASK_APP: {os.environ.get('FLASK_APP', 'Not set')}")
    print(f"   FLASK_ENV: {os.environ.get('FLASK_ENV', 'Not set')}")
    
    port = os.environ.get('PORT')
    if port is None:
        print("⚠️  PORT environment variable not set, using default port 5000")
        port = 5000
    
    # Run the checks
    port_bound = check_port_binding(port)
    health_check = check_health_endpoint(port)
    port_debug = check_port_debug_endpoint(port)
    
    # Print summary
    print("\n📋 Verification Summary:")
    print(f"   Port Binding: {'✅ PASS' if port_bound else '❌ FAIL'}")
    print(f"   Health Check: {'✅ PASS' if health_check else '❌ FAIL'}")
    print(f"   Port Debug: {'✅ PASS' if port_debug else '❌ FAIL'}")
    
    if port_bound and health_check and port_debug:
        print("\n🎉 All checks passed! The application is correctly configured for Render.com")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
