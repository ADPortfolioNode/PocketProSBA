#!/usr/bin/env python3
"""
Render.com specific health check and deployment validation
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} not supported. Need Python 3.9+")
        return False

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'run.py',
        'app.py', 
        'requirements-render.txt',
        'render.yaml',
        'pyproject.toml'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_imports():
    """Test critical imports"""
    critical_imports = [
        'flask',
        'flask_cors', 
        'flask_socketio',
        'gunicorn',
        'gevent'
    ]
    
    failed_imports = []
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module} import successful")
        except ImportError as e:
            print(f"❌ {module} import failed: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def test_flask_app():
    """Test if the Flask app can be created"""
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        # Try to import the run module
        from run import application
        print("✅ Flask application created successfully")
        return True
    except Exception as e:
        print(f"❌ Flask application creation failed: {e}")
        return False

def check_environment_variables():
    """Check environment variables"""
    required_env_vars = ['FLASK_ENV', 'FLASK_APP']
    optional_env_vars = ['GEMINI_API_KEY', 'SECRET_KEY', 'PORT']
    
    print("\n🔍 Environment Variables:")
    for var in required_env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}={value}")
        else:
            print(f"⚠️  {var} not set (will use default)")
    
    for var in optional_env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}=***")
        else:
            print(f"ℹ️  {var} not set (optional)")

def main():
    """Run all health checks"""
    print("🚀 Render.com Deployment Health Check")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files),
        ("Critical Imports", check_imports),
        ("Flask Application", test_flask_app)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {e}")
            all_passed = False
    
    check_environment_variables()
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All health checks passed! Ready for Render deployment.")
        return 0
    else:
        print("❌ Some health checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
