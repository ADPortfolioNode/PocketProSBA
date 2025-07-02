#!/usr/bin/env python3
"""
Render.com health check script for PocketPro:SBA
"""
import os
import sys
import urllib.request
import urllib.error
import json
import time

def check_health_endpoint(url="http://localhost:10000/health", timeout=30):
    """Check if the health endpoint is responding"""
    try:
        print(f"🔍 Checking health endpoint: {url}")
        
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'PocketPro-SBA-HealthCheck/1.0')
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ Health check passed")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Service: {data.get('service', 'unknown')}")
                print(f"   Version: {data.get('version', 'unknown')}")
                return True
            else:
                print(f"❌ Health check failed: HTTP {response.getcode()}")
                return False
                
    except urllib.error.URLError as e:
        print(f"❌ Health check failed: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def check_imports():
    """Check if critical imports work"""
    try:
        print("🔍 Checking critical imports...")
        
        # Test Flask import
        import flask
        print(f"✅ Flask {flask.__version__}")
        
        # Test other critical imports
        import flask_cors
        print(f"✅ Flask-CORS {flask_cors.__version__}")
        
        import gunicorn
        print(f"✅ Gunicorn {gunicorn.__version__}")
        
        # Test application import
        sys.path.insert(0, os.path.dirname(__file__))
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        try:
            import run
            print("✅ Application module imports successfully")
        except ImportError as e:
            print(f"⚠️  Application import failed: {e}")
            print("   Fallback mode will be used")
        
        return True
        
    except ImportError as e:
        print(f"❌ Critical import failed: {e}")
        return False

def check_environment():
    """Check environment configuration"""
    print("🔍 Checking environment configuration...")
    
    required_vars = ['PORT']
    optional_vars = ['GEMINI_API_KEY', 'SECRET_KEY', 'FLASK_ENV']
    
    all_good = True
    
    for var in required_vars:
        if os.environ.get(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is not set (required)")
            all_good = False
    
    for var in optional_vars:
        if os.environ.get(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is not set")
    
    return all_good

def main():
    """Run all health checks"""
    print("🏥 PocketPro:SBA Health Check for Render.com")
    print("=" * 50)
    
    checks = [
        ("Environment Configuration", check_environment),
        ("Python Imports", check_imports),
    ]
    
    # Only check health endpoint if PORT is set (running in Render)
    if os.environ.get('PORT'):
        port = os.environ.get('PORT', '10000')
        url = f"http://localhost:{port}/health"
        checks.append(("Health Endpoint", lambda: check_health_endpoint(url)))
    
    results = []
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Health Check Summary:")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All health checks passed!")
        return 0
    else:
        print("\n⚠️  Some health checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
