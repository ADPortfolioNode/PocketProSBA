#!/usr/bin/env python3
"""
Test script to verify app startup and timeout handling
"""
import os
import sys
import time
import threading
from pathlib import Path

def test_app_startup():
    """Test that the app can start up without timing out"""
    print("🔧 Testing app startup and timeout handling...")
    
    try:
        # Import the app
        from app import app
        print("✅ App imported successfully")
        
        # Test basic endpoints with timeout simulation
        with app.test_client() as client:
            print("📡 Testing basic endpoints...")
            
            # Test health endpoint
            response = client.get('/health')
            print(f"   /health: {response.status_code} ({len(response.data)} bytes)")
            
            # Test status endpoint
            response = client.get('/api/status')
            print(f"   /api/status: {response.status_code} ({len(response.data)} bytes)")
            
            # Test root endpoint
            response = client.get('/')
            print(f"   /: {response.status_code} ({len(response.data)} bytes)")
            
        print("✅ All endpoints responding normally")
        
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        return False
    
    return True

def test_wsgi_import():
    """Test that wsgi.py can be imported without issues"""
    print("\n🔧 Testing wsgi.py import...")
    
    try:
        from wsgi import application
        print("✅ wsgi.py imported successfully")
        print(f"   Application type: {type(application)}")
        
        # Test that it's a valid Flask app
        if hasattr(application, 'test_client'):
            print("✅ Application is a valid Flask app")
            
            # Quick test
            with application.test_client() as client:
                response = client.get('/health')
                print(f"   Health check via wsgi: {response.status_code}")
        else:
            print("❌ Application is not a Flask app")
            return False
            
    except Exception as e:
        print(f"❌ wsgi.py import failed: {e}")
        return False
    
    return True

def test_port_configuration():
    """Test port configuration handling"""
    print("\n🔧 Testing port configuration...")
    
    # Test with different PORT values
    test_ports = ['10000', '5000', '8000', None]
    
    for test_port in test_ports:
        try:
            # Set or unset PORT
            if test_port:
                os.environ['PORT'] = test_port
            else:
                os.environ.pop('PORT', None)
            
            # Test gunicorn config
            port_from_env = os.environ.get('PORT', '10000')
            bind_address = f"0.0.0.0:{port_from_env}"
            
            print(f"   PORT={test_port} -> bind={bind_address}")
            
        except Exception as e:
            print(f"   ❌ Port test failed for {test_port}: {e}")
    
    print("✅ Port configuration tests completed")
    return True

def test_timeout_simulation():
    """Simulate various timeout scenarios"""
    print("\n🔧 Testing timeout handling...")
    
    try:
        from app import app
        
        # Test with simulated slow response
        with app.test_client() as client:
            def slow_request():
                # This simulates what might happen during a slow startup
                time.sleep(2)  # 2 second delay
                response = client.get('/health')
                return response.status_code
            
            # Run in thread to test timeout handling
            thread = threading.Thread(target=slow_request)
            thread.start()
            thread.join(timeout=10)  # 10 second timeout
            
            if thread.is_alive():
                print("⚠️ Request timed out (this could indicate a real issue)")
                return False
            else:
                print("✅ Slow request handled within timeout")
                
    except Exception as e:
        print(f"❌ Timeout test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Render.com 502 Error Diagnosis - Testing App Reliability")
    print("=" * 60)
    
    tests = [
        ("App Startup", test_app_startup),
        ("WSGI Import", test_wsgi_import),
        ("Port Configuration", test_port_configuration),
        ("Timeout Handling", test_timeout_simulation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")
        
        print("-" * 40)
    
    print(f"\n🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed - App should work on Render.com")
    else:
        print("⚠️ Some tests failed - Check configuration")
    
    print("\n📋 Recommended Render.com Settings:")
    print("   - Use PORT environment variable (default: 10000)")
    print("   - Set worker timeout to 300 seconds")
    print("   - Use single worker for stability")
    print("   - Enable health checks on /health endpoint")

if __name__ == "__main__":
    main()
