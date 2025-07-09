#!/usr/bin/env python3
"""
Render.com Compatibility Check Script
This script checks your PocketPro SBA application for Render.com compatibility
"""

import os
import sys
import importlib.util
import platform
import subprocess
import re

def print_header(text):
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️ {message}")

def print_error(message):
    print(f"❌ {message}")

def check_port_configuration():
    """Check that the app correctly uses the PORT environment variable"""
    print_header("Checking PORT configuration")
    
    # Check minimal_app.py
    try:
        with open('minimal_app.py', 'r') as f:
            content = f.read()
            if "PORT = int(os.environ.get('PORT', 5000))" in content:
                print_success("minimal_app.py correctly uses PORT environment variable")
            else:
                print_error("minimal_app.py may not be using PORT environment variable correctly")
    except FileNotFoundError:
        print_error("minimal_app.py not found")
    
    # Check docker-compose.render.yml
    try:
        with open('docker-compose.render.yml', 'r') as f:
            content = f.read()
            if "${PORT:-5000}" in content:
                print_success("docker-compose.render.yml correctly uses PORT environment variable")
            else:
                print_error("docker-compose.render.yml may not be using PORT correctly")
    except FileNotFoundError:
        print_warning("docker-compose.render.yml not found")
        
    # Check gunicorn config
    try:
        with open('gunicorn.render.conf.py', 'r') as f:
            content = f.read()
            if "bind = f\"0.0.0.0:{os.environ.get('PORT', 5000)}" in content:
                print_success("gunicorn.render.conf.py correctly uses PORT environment variable")
            else:
                print_error("gunicorn.render.conf.py may not be using PORT correctly")
    except FileNotFoundError:
        print_warning("gunicorn.render.conf.py not found")

def check_health_endpoints():
    """Check that the health endpoints are present"""
    print_header("Checking health endpoints")
    
    # Check minimal_app.py for health endpoints
    try:
        with open('minimal_app.py', 'r') as f:
            content = f.read()
            if "@app.route('/health')" in content:
                print_success("Root health endpoint present")
            else:
                print_error("Root health endpoint not found - required by Render.com")
                
            if "@app.route('/api/health')" in content:
                print_success("API health endpoint present")
            else:
                print_warning("API health endpoint not found - useful for frontend status checks")
    except FileNotFoundError:
        print_error("minimal_app.py not found")

def check_cors_configuration():
    """Check CORS configuration"""
    print_header("Checking CORS configuration")
    
    # Check minimal_app.py for CORS
    try:
        with open('minimal_app.py', 'r') as f:
            content = f.read()
            if "CORS(app" in content:
                print_success("CORS is configured")
                if '"*"' in content:
                    print_warning("Wildcard CORS origin is used - secure but may need tightening for production")
                else:
                    print_success("CORS origins are restricted - good for security")
            else:
                print_error("CORS may not be properly configured")
    except FileNotFoundError:
        print_error("minimal_app.py not found")

def check_dependencies():
    """Check dependencies for Render compatibility"""
    print_header("Checking dependencies")
    
    # Check for Rust dependencies
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            rust_deps = ["cryptography>", "pydantic>", "hnswlib"]
            found_rust = [dep for dep in rust_deps if dep in content]
            
            if found_rust:
                print_warning(f"Main requirements.txt contains potential Rust dependencies: {', '.join(found_rust)}")
                print_warning("These may cause build issues on Render.com - use requirements-render-minimal.txt instead")
            else:
                print_success("No obvious Rust dependencies found in requirements.txt")
    except FileNotFoundError:
        print_warning("requirements.txt not found")
    
    # Check for Render-specific requirements
    if os.path.exists('requirements-render-minimal.txt'):
        print_success("requirements-render-minimal.txt found - good for Render.com deployment")
    else:
        print_warning("requirements-render-minimal.txt not found - consider creating this for Render.com")

def check_render_yaml():
    """Check render.yaml configuration"""
    print_header("Checking render.yaml")
    
    if not os.path.exists('render.yaml'):
        print_warning("render.yaml not found - this is useful for Blueprint deployment")
        return
        
    try:
        with open('render.yaml', 'r') as f:
            content = f.read()
            if "<your-backend-service-name>" in content:
                print_error("render.yaml contains placeholder values that need to be replaced")
            else:
                print_success("render.yaml appears to be properly configured")
                
            if "gunicorn app:app" in content:
                print_warning("render.yaml may be using app.py instead of minimal_app.py")
            
            if "PYTHON_VERSION" in content:
                print_success("Python version is specified in render.yaml")
            else:
                print_warning("Python version not specified in render.yaml")
    except FileNotFoundError:
        print_error("render.yaml not found")

def check_frontend_config():
    """Check frontend configuration"""
    print_header("Checking frontend configuration")
    
    # Check for .env files
    if os.path.exists('frontend/.env.production'):
        print_success("frontend/.env.production found")
        
        # Check for API URL
        try:
            with open('frontend/.env.production', 'r') as f:
                content = f.read()
                if "REACT_APP_API_URL" in content:
                    print_success("REACT_APP_API_URL is configured in .env.production")
                else:
                    print_warning("REACT_APP_API_URL may not be configured in .env.production")
        except:
            print_warning("Could not read frontend/.env.production")
    else:
        print_warning("frontend/.env.production not found - this helps with API URLs")
    
    # Check for relative API URLs in code
    try:
        app_js_path = 'frontend/src/App.js'
        if os.path.exists(app_js_path):
            with open(app_js_path, 'r') as f:
                content = f.read()
                if "fetch('/api/" in content:
                    print_success("App.js uses relative API paths - good for deployment")
                elif "fetch('" in content and "/api/" not in content:
                    print_warning("App.js may not be using relative API paths with /api/ prefix")
                else:
                    print_success("No direct fetch calls found in App.js")
        else:
            print_warning(f"Could not find {app_js_path}")
    except:
        print_warning("Error checking frontend code")

def main():
    print_header("🔍 RENDER.COM COMPATIBILITY CHECK")
    print(f"Checking PocketPro SBA application in: {os.getcwd()}")
    
    check_port_configuration()
    check_health_endpoints()
    check_cors_configuration()
    check_dependencies()
    check_render_yaml()
    check_frontend_config()
    
    print("\n" + "=" * 80)
    print(" 🏁 COMPATIBILITY CHECK COMPLETE")
    print("=" * 80)
    print("\nFor more information about deploying to Render.com, see DEPLOYMENT.md")
    print("Remember to test your deployment with a small instance first!")

if __name__ == "__main__":
    main()
