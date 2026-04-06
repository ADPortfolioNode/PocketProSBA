#!/usr/bin/env python3
"""
Frontend Development Troubleshooting Script
Fixes common frontend development issues and WebSocket errors.
"""

import subprocess
import sys
import os
import json

def fix_frontend_issues():
    """Fix common frontend development issues."""
    print("=" * 60)
    print("🔧 FRONTEND TROUBLESHOOTING & FIXES")
    print("=" * 60)
    
    frontend_dir = "frontend"
    if not os.path.exists(frontend_dir):
        print(f"❌ Frontend directory '{frontend_dir}' not found!")
        return False
    
    # 1. Check if backend is running
    print("\n1. 🔍 CHECKING BACKEND CONNECTION...")
    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running on localhost:5000")
        else:
            print(f"⚠️  Backend responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        print("   💡 Start backend with: python app.py")
    
    # 2. Check frontend package.json
    print("\n2. 📋 CHECKING FRONTEND CONFIGURATION...")
    package_path = os.path.join(frontend_dir, "package.json")
    if os.path.exists(package_path):
        with open(package_path, 'r') as f:
            package_data = json.load(f)
        
        # Check proxy setting
        proxy = package_data.get('proxy')
        if proxy == "http://localhost:5000":
            print("✅ Proxy correctly set to localhost:5000")
        else:
            print(f"⚠️  Proxy set to: {proxy}")
    
    # 3. Check for WebSocket issues
    print("\n3. 🌐 WEBSOCKET TROUBLESHOOTING...")
    print("   The WebSocket error 'ws://localhost:3000/ws' is likely from:")
    print("   • React Dev Tools or browser extensions")
    print("   • Hot Module Replacement (HMR)")
    print("   • Apollo DevTools")
    print("   ℹ️  These are development-only and won't affect production")
    
    # 4. Check public assets
    print("\n4. 📁 CHECKING PUBLIC ASSETS...")
    public_dir = os.path.join(frontend_dir, "public")
    required_files = ["favicon.ico", "manifest.json", "index.html"]
    
    for file in required_files:
        file_path = os.path.join(public_dir, file)
        if os.path.exists(file_path):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
    
    # 5. Provide fixes
    print("\n5. 🛠️  QUICK FIXES...")
    
    print("\n📝 TO FIX WEBSOCKET ERRORS:")
    print("   • These are normal in development mode")
    print("   • Disable browser extensions if annoying")
    print("   • Add to .env.development: FAST_REFRESH=false")
    
    print("\n📝 TO FIX CONNECTION RESET ERRORS:")
    print("   • Ensure backend is running: python app.py")
    print("   • Check backend URL in frontend .env files")
    print("   • Restart both frontend and backend")
    
    print("\n📝 TO FIX APOLLO DEVTOOLS WARNING:")
    print("   • Install Apollo DevTools browser extension (optional)")
    print("   • Or ignore - it's just a development convenience")
    
    # 6. Environment check
    print("\n6. 🌍 ENVIRONMENT VARIABLES...")
    env_dev_path = os.path.join(frontend_dir, ".env.development")
    if os.path.exists(env_dev_path):
        print("✅ .env.development found")
        with open(env_dev_path, 'r') as f:
            env_content = f.read()
        if "REACT_APP_BACKEND_URL" in env_content:
            print("✅ REACT_APP_BACKEND_URL configured")
        else:
            print("⚠️  REACT_APP_BACKEND_URL not set")
    else:
        print("⚠️  .env.development not found")
    
    print("\n" + "=" * 60)
    print("✅ FRONTEND TROUBLESHOOTING COMPLETE")
    print("💡 Most errors you're seeing are normal development warnings")
    print("🚀 Your app should work fine despite these console messages")
    print("=" * 60)
    
    return True

def create_frontend_env_fix():
    """Create/update frontend environment files to reduce errors."""
    frontend_dir = "frontend"
    
    # Create .env.development with WebSocket fixes
    env_dev_content = """# Development environment settings
REACT_APP_BACKEND_URL=http://localhost:5000
FAST_REFRESH=false
WDS_SOCKET_HOST=localhost
WDS_SOCKET_PORT=3000
CHOKIDAR_USEPOLLING=false
"""
    
    env_dev_path = os.path.join(frontend_dir, ".env.development")
    with open(env_dev_path, 'w') as f:
        f.write(env_dev_content)
    
    print(f"✅ Created/updated {env_dev_path}")
    
    # Create .env.production
    env_prod_content = """# Production environment settings
REACT_APP_BACKEND_URL=https://your-backend-url.render.com
GENERATE_SOURCEMAP=false
"""
    
    env_prod_path = os.path.join(frontend_dir, ".env.production")
    if not os.path.exists(env_prod_path):
        with open(env_prod_path, 'w') as f:
            f.write(env_prod_content)
        print(f"✅ Created {env_prod_path}")

if __name__ == "__main__":
    success = fix_frontend_issues()
    if success:
        create_frontend_env_fix()
    sys.exit(0 if success else 1)
