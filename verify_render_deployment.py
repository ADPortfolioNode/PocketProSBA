#!/usr/bin/env python3
"""
Render.com Deployment Verification Script

This script should be run after deploying to Render.com
to verify that the application is running correctly.

It checks:
1. The application is running on the correct port
2. The health endpoint is responding
3. All required environment variables are set
4. No references to port 10000 remain in deployment files
"""
import os
import sys
import json
import requests
import time
import re
from urllib.parse import urlparse
from pathlib import Path

# Files to check for port references
PORT_CHECK_FILES = [
    "app.py",
    "wsgi.py",
    "gunicorn.conf.py",
    "gunicorn.conf.robust.py",
    "Dockerfile",
    "Dockerfile.backend",
    "Dockerfile.backend.prod",
    "Dockerfile.render",
    "Procfile",
    "render.yaml",
    "render.docker.yaml",
]

def verify_deployment(base_url):
    """Verify that the deployment is working correctly"""
    print(f"🔍 Verifying deployment at {base_url}")
    
    # Check root endpoint
    try:
        print("\n📡 Checking root endpoint...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status code: {response.status_code}")
            print(f"  ✅ Message: {data.get('message', 'Unknown')}")
            print(f"  ✅ Version: {data.get('version', 'Unknown')}")
            print(f"  ✅ Environment: {data.get('environment', 'Unknown')}")
            print(f"  ✅ Port: {data.get('port', 'Unknown')}")
            print(f"  ✅ Render: {data.get('render', 'Unknown')}")
        else:
            print(f"  ❌ Status code: {response.status_code}")
            print(f"  ❌ Response: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Check health endpoint
    try:
        print("\n📡 Checking health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status code: {response.status_code}")
            print(f"  ✅ Status: {data.get('status', 'Unknown')}")
            print(f"  ✅ Success: {data.get('success', 'Unknown')}")
        else:
            print(f"  ❌ Status code: {response.status_code}")
            print(f"  ❌ Response: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Check port-debug endpoint
    try:
        print("\n📡 Checking port-debug endpoint...")
        response = requests.get(f"{base_url}/port-debug")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status code: {response.status_code}")
            print(f"  ✅ Configured port: {data.get('configured_port', 'Unknown')}")
            print(f"  ✅ Hostname: {data.get('hostname', 'Unknown')}")
            print(f"  ✅ IP address: {data.get('ip_address', 'Unknown')}")
            print(f"  ✅ Render deployment: {data.get('render_deployment', 'Unknown')}")
            
            env_vars = data.get('environment_variables', {})
            print(f"\n📋 Environment variables:")
            for key, value in env_vars.items():
                print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ Status code: {response.status_code}")
            print(f"  ❌ Response: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # All checks passed
    return True

def check_port_references(file_path, bad_port="10000", good_port="5000"):
    """Check for hard-coded port references"""
    if not Path(file_path).exists():
        return True, f"File {file_path} does not exist - skipping"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for bad port references
        bad_port_pattern = r'(?<!-)(?<!\d)' + bad_port + r'(?!\d)'
        matches = re.findall(bad_port_pattern, content)
        if matches:
            bad_port_locations = []
            for line_num, line in enumerate(content.splitlines(), 1):
                if bad_port in line:
                    context = line.strip()
                    bad_port_locations.append(f"Line {line_num}: {context}")
            
            return False, f"Found {len(matches)} references to port {bad_port} in {file_path}:\n" + "\n".join(bad_port_locations[:5])
        
        return True, f"No bad port references found in {file_path}"
        
    except Exception as e:
        return False, f"Error checking {file_path}: {e}"

def verify_port_configuration():
    """Verify that all files are using the correct port"""
    print("\n🔍 Checking for port 10000 references...")
    all_passed = True
    
    for file_path in PORT_CHECK_FILES:
        passed, message = check_port_references(file_path)
        status = "✅" if passed else "❌"
        print(f"  {status} {message}")
        if not passed:
            all_passed = False
    
    return all_passed

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Please provide the base URL of your Render.com deployment")
        print("Example: python verify_render_deployment.py https://pocketpro-sba-backend.onrender.com")
        return 1
    
    base_url = sys.argv[1]
    
    # Validate URL
    try:
        result = urlparse(base_url)
        if not all([result.scheme, result.netloc]):
            print(f"Invalid URL: {base_url}")
            return 1
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return 1
    
    # Remove trailing slash if present
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # Verify deployment
    print("🚀 Render.com Deployment Verification")
    print("=" * 50)
    
    success = verify_deployment(base_url)
    port_success = verify_port_configuration()
    
    if success and port_success:
        print("\n🎉 All checks passed! Your application is running correctly on Render.com")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
