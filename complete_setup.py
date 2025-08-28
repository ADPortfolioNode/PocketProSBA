#!/usr/bin/env python3
"""
Script to complete the final setup steps for PocketProSBA
"""
import os
import subprocess
import sys

def setup_google_cse_id():
    """Set up Google CSE ID configuration"""
    print("🔧 Setting up Google CSE ID...")
    
    # Check if we have the environment file
    env_file = 'backend/.env'
    if not os.path.exists(env_file):
        print("❌ Environment file not found at backend/.env")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check if GOOGLE_CSE_ID needs to be updated
    if 'your_google_custom_search_engine_id_here' in content:
        print("⚠️  GOOGLE_CSE_ID needs to be configured manually")
        print("Please update backend/.env with your actual Google CSE ID")
        print("Format: GOOGLE_CSE_ID=012345678901234567890:abcdefghijk")
        return False
    else:
        print("✅ GOOGLE_CSE_ID appears to be configured")
        return True

def setup_chromadb():
    """Set up ChromaDB configuration"""
    print("🔧 Setting up ChromaDB...")
    
    env_file = 'backend/.env'
    if not os.path.exists(env_file):
        print("❌ Environment file not found")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check ChromaDB configuration
    if 'CHROMADB_HOST=localhost' in content and 'CHROMADB_PORT=8000' in content:
        print("✅ ChromaDB configured for local development")
        print("To start ChromaDB locally, run:")
        print("  pip install chromadb")
        print("  chroma run --host localhost --port 8000")
        return True
    else:
        print("⚠️  ChromaDB configuration needs review")
        print("Please check backend/.env for CHROMADB_HOST and CHROMADB_PORT settings")
        return False

def check_render_config():
    """Check Render deployment configuration"""
    print("🔧 Checking Render configuration...")
    
    if os.path.exists('render.yaml'):
        print("✅ render.yaml found - ready for deployment")
        
        # Check if environment variables are set in render.yaml
        with open('render.yaml', 'r') as f:
            content = f.read()
            
        if 'envVars' in content:
            print("✅ Environment variables configured for Render")
        else:
            print("⚠️  Add environment variables to render.yaml for production")
            
        return True
    else:
        print("❌ render.yaml not found")
        return False

def create_monitoring_script():
    """Create a system monitoring script"""
    print("📊 Creating monitoring script...")
    
    monitor_script = """#!/usr/bin/env python3
import os
import time
import requests
from datetime import datetime

def check_system_health():
    \"\"\"Check system health endpoints\"\"\"
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
"""
    
    with open('monitor_system.py', 'w') as f:
        f.write(monitor_script)
    
    print("✅ Monitoring script created: monitor_system.py")
    print("Run: python monitor_system.py to monitor system health")

def main():
    """Complete the final setup"""
    print("🚀 Completing PocketProSBA Final Setup")
    print("=" * 60)
    
    # Step 1: Google CSE ID
    google_ready = setup_google_cse_id()
    
    # Step 2: ChromaDB
    chroma_ready = setup_chromadb()
    
    # Step 3: Render config
    render_ready = check_render_config()
    
    # Step 4: Monitoring
    create_monitoring_script()
    
    print("\\n" + "=" * 60)
    print("SETUP COMPLETION SUMMARY")
    print("=" * 60)
    
    if google_ready and chroma_ready and render_ready:
        print("🎉 ALL SYSTEMS READY FOR DEPLOYMENT!")
        print("\\nNext steps:")
        print("1. Start ChromaDB: chroma run --host localhost --port 8000")
        print("2. Deploy to Render using render.yaml")
        print("3. Monitor with: python monitor_system.py")
    else:
        print("⚠️  SOME CONFIGURATION NEEDED")
        print("Please complete the manual configuration steps above")
        print("Then run this script again to verify")

if __name__ == "__main__":
    main()
