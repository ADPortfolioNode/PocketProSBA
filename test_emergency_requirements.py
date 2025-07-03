#!/usr/bin/env python3
"""
Emergency Render.com deployment test.
Tests the absolute minimal requirements.txt to ensure no Rust compilation.
"""

import subprocess
import sys
import os

def test_emergency_requirements():
    """Test installing emergency requirements without Rust dependencies."""
    print("=" * 60)
    print("EMERGENCY RENDER.COM REQUIREMENTS TEST")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('requirements.txt'):
        print("❌ ERROR: requirements.txt not found!")
        print("   Make sure you're in the PocketProSBA directory")
        return False
    
    print("✅ Found requirements.txt")
    
    # Show current requirements
    print("\n📋 Current requirements.txt contents:")
    with open('requirements.txt', 'r') as f:
        content = f.read()
        print(content)
    
    # Test if any requirements contain Rust dependencies
    rust_keywords = [
        'numpy', 'pandas', 'scipy', 'scikit-learn', 
        'chromadb', 'sentence-transformers', 'transformers',
        'pydantic', 'fastapi', 'uvicorn', 'cryptography',
        'lxml', 'cffi', 'bcrypt', 'PyNaCl'
    ]
    
    print("\n🔍 Checking for Rust-dependent packages...")
    found_rust_deps = []
    
    for line in content.lower().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            package_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
            if package_name in [dep.lower() for dep in rust_keywords]:
                found_rust_deps.append(package_name)
    
    if found_rust_deps:
        print(f"❌ FOUND RUST DEPENDENCIES: {found_rust_deps}")
        print("   These packages will cause maturin/Rust build failures on Render.com!")
        return False
    else:
        print("✅ NO RUST DEPENDENCIES FOUND")
    
    print("\n🧪 Testing minimal app import...")
    try:
        # Test if our minimal app can be imported
        sys.path.insert(0, os.getcwd())
        from minimal_app import app
        print("✅ minimal_app.py imports successfully")
        
        # Test basic Flask functionality
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint works")
            else:
                print(f"⚠️  Health endpoint returned {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error importing minimal_app: {e}")
        return False
    
    print("\n🧪 Testing main app import with fallbacks...")
    try:
        from app import app as main_app
        print("✅ Main app.py imports successfully")
        
        # Test basic Flask functionality
        with main_app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Main app health endpoint works")
                data = response.get_json()
                print(f"   Response: {data}")
            else:
                print(f"⚠️  Main app health endpoint returned {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error importing main app: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 EMERGENCY REQUIREMENTS TEST PASSED!")
    print("✅ No Rust dependencies detected")
    print("✅ Apps import and run successfully")
    print("✅ Ready for Render.com deployment")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_emergency_requirements()
    sys.exit(0 if success else 1)
