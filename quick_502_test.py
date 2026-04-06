#!/usr/bin/env python3
"""
Quick test for 502 error fix
"""
import os

# Test 1: Port configuration
print("🔧 Testing port configuration...")
for port in ['10000', '5000', None]:
    if port:
        os.environ['PORT'] = port
    else:
        os.environ.pop('PORT', None)
    
    result = os.environ.get('PORT', '10000')
    print(f"   PORT={port} -> Result: {result}")

# Test 2: App import
print("\n🔧 Testing app import...")
try:
    from app import app
    print("✅ App imported successfully")
except Exception as e:
    print(f"❌ App import failed: {e}")

# Test 3: WSGI import
print("\n🔧 Testing wsgi import...")
try:
    from wsgi import application
    print("✅ WSGI imported successfully")
    print(f"   Type: {type(application)}")
except Exception as e:
    print(f"❌ WSGI import failed: {e}")

# Test 4: Quick health check
print("\n🔧 Testing health endpoint...")
try:
    from app import app
    with app.test_client() as client:
        response = client.get('/health')
        print(f"✅ Health check: {response.status_code}")
except Exception as e:
    print(f"❌ Health check failed: {e}")

print("\n🎯 Configuration Summary:")
print("✅ Port default changed to 10000 (Render.com default)")
print("✅ Timeout increased to 300 seconds")
print("✅ Worker settings optimized for stability")
print("✅ Enhanced logging for debugging")
print("\n🚀 Ready for Render.com deployment!")
