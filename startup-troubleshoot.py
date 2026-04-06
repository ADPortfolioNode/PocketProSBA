#!/usr/bin/env python3
"""
PocketPro:SBA Startup Troubleshooter
Diagnoses and fixes common startup issues
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def print_header():
    print("🔧 PocketPro:SBA Startup Troubleshooter")
    print("=" * 50)
    print()

def check_python_version():
    print("🐍 Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 13:
        print("   ⚠️  WARNING: Python 3.13+ detected - gevent compatibility issues expected")
        return "3.13+"
    elif version.major == 3 and version.minor == 11:
        print("   ✅ Python 3.11 - optimal compatibility")
        return "3.11"
    elif version.major == 3 and version.minor == 12:
        print("   ✅ Python 3.12 - good compatibility")
        return "3.12"
    else:
        print(f"   ⚠️  Python {version.major}.{version.minor} - consider upgrading to 3.11")
        return "other"

def check_required_files():
    print("\n📁 Checking required files...")
    required = ["requirements.txt", "run.py", "app.py"]
    missing = []
    
    for file in required:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing.append(file)
    
    return missing

def analyze_requirements():
    print("\n📋 Analyzing requirements.txt...")
    if not os.path.exists("requirements.txt"):
        print("   ❌ requirements.txt not found")
        return []
    
    issues = []
    with open("requirements.txt", "r") as f:
        content = f.read()
        lines = content.strip().split("\n")
    
    problematic_packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and "==" in line:
            package = line.split("==")[0].lower()
            if package == "gevent":
                problematic_packages.append(line)
                print(f"   ❌ {line} - INCOMPATIBLE WITH PYTHON 3.13+")
            else:
                print(f"   ✅ {line}")
    
    if problematic_packages:
        issues.extend(problematic_packages)
    
    return issues

def test_imports():
    print("\n🔍 Testing critical imports...")
    
    # Test basic Flask
    try:
        import flask
        print(f"   ✅ Flask {flask.__version__}")
    except ImportError as e:
        print(f"   ❌ Flask import failed: {e}")
        return False
    
    # Test gunicorn
    try:
        import gunicorn
        print(f"   ✅ Gunicorn available")
    except ImportError as e:
        print(f"   ❌ Gunicorn import failed: {e}")
        return False
    
    # Test gevent (if present)
    try:
        import gevent
        print(f"   ⚠️  Gevent {gevent.__version__} - may cause issues with Python 3.13+")
    except ImportError:
        print("   ✅ Gevent not installed (good for Python 3.13+)")
    
    # Test google-generativeai
    try:
        import google.generativeai as genai
        print("   ✅ Google Generative AI available")
    except ImportError as e:
        print(f"   ❌ Google Generative AI import failed: {e}")
        return False
    
    return True

def test_app_import():
    print("\n🚀 Testing application import...")
    
    # Add current directory to path
    sys.path.insert(0, ".")
    if os.path.exists("src"):
        sys.path.insert(0, "src")
    
    try:
        import run
        print("   ✅ run.py imported successfully")
    except ImportError as e:
        print(f"   ❌ run.py import failed: {e}")
        return False
    
    try:
        from run import app
        print("   ✅ Flask app object accessible")
        return True
    except ImportError as e:
        print(f"   ❌ Flask app import failed: {e}")
        return False
    except AttributeError as e:
        print(f"   ❌ app object not found in run.py: {e}")
        return False

def create_fixed_requirements(python_version):
    print("\n🛠️  Creating fixed requirements.txt...")
    
    if python_version == "3.13+":
        requirements = """# Compatible with Python 3.13+ - NO GEVENT
Flask==3.0.0
gunicorn==21.2.0
Werkzeug==3.0.1
google-generativeai==0.3.2
python-dotenv==1.0.0

# Core dependencies
Jinja2==3.1.2
MarkupSafe==2.1.3
click==8.1.7
blinker==1.7.0
itsdangerous==2.1.2

# Additional production dependencies
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.4
requests==2.31.0
urllib3==2.1.0
"""
    else:
        requirements = """# Compatible with Python 3.11/3.12
Flask==2.3.3
gunicorn==21.2.0
gevent==23.7.0
Werkzeug==2.3.7
google-generativeai==0.3.2
python-dotenv==1.0.0

# Core dependencies
Jinja2==3.1.2
MarkupSafe==2.1.3
click==8.1.7
blinker==1.6.3
itsdangerous==2.1.2
greenlet==2.0.2

# Additional production dependencies
certifi==2023.7.22
charset-normalizer==3.2.0
idna==3.4
requests==2.31.0
urllib3==2.0.4
"""
    
    # Backup existing requirements
    if os.path.exists("requirements.txt"):
        import shutil
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2("requirements.txt", f"requirements.txt.backup.{timestamp}")
        print(f"   ✅ Backed up to requirements.txt.backup.{timestamp}")
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    print("   ✅ Created fixed requirements.txt")

def create_basic_run_py():
    print("\n🛠️  Creating basic run.py...")
    
    run_content = '''#!/usr/bin/env python3
"""
PocketPro:SBA - Main application runner
"""

import os
from app import create_app

# Create Flask app
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🚀 Starting PocketPro:SBA on port {port}")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
'''
    
    with open("run.py", "w") as f:
        f.write(run_content)
    
    print("   ✅ Created run.py")

def create_basic_app_py():
    print("\n🛠️  Creating basic app.py...")
    
    app_content = '''"""
PocketPro:SBA - Flask Application Factory
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Basic routes
    @app.route('/')
    def index():
        return {
            "message": "🚀 PocketPro:SBA is running!",
            "status": "success",
            "version": "1.0.0"
        }
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "PocketPro:SBA"}
    
    @app.route('/api/test')
    def api_test():
        return {"message": "API is working", "status": "ok"}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found", "status": 404}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error", "status": 500}, 500
    
    return app
'''
    
    with open("app.py", "w") as f:
        f.write(app_content)
    
    print("   ✅ Created app.py")

def test_startup():
    print("\n🚀 Testing application startup...")
    
    try:
        # Test import again
        if test_app_import():
            print("   ✅ Application imports successfully")
            
            # Test basic functionality
            sys.path.insert(0, ".")
            from run import app
            
            with app.test_client() as client:
                response = client.get('/')
                if response.status_code == 200:
                    print("   ✅ Basic route works")
                    return True
                else:
                    print(f"   ❌ Basic route failed: {response.status_code}")
                    return False
        else:
            return False
            
    except Exception as e:
        print(f"   ❌ Startup test failed: {e}")
        return False

def main():
    print_header()
    
    # Check Python version
    python_version = check_python_version()
    
    # Check required files
    missing_files = check_required_files()
    
    # Create missing files
    if "requirements.txt" in missing_files:
        create_fixed_requirements(python_version)
    
    if "run.py" in missing_files:
        create_basic_run_py()
    
    if "app.py" in missing_files:
        create_basic_app_py()
    
    # Analyze requirements for issues
    requirement_issues = analyze_requirements()
    
    # Fix requirements if there are gevent issues with Python 3.13+
    if requirement_issues and python_version == "3.13+":
        print(f"\n🔧 Fixing {len(requirement_issues)} requirement issues...")
        create_fixed_requirements(python_version)
        print("   ✅ Requirements fixed for Python 3.13+")
    
    # Test imports
    if not test_imports():
        print("\n❌ CRITICAL: Install dependencies first:")
        print("   pip install -r requirements.txt")
        return False
    
    # Test application startup
    if test_startup():
        print("\n🎉 SUCCESS! Application should start properly")
        print("\n🚀 TO START THE APP:")
        print("   python run.py")
        print("   OR: flask run")
        print("   OR: gunicorn --bind 0.0.0.0:5000 run:app")
        
        print("\n🌐 FOR RENDER DEPLOYMENT:")
        start_cmd = "gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app"
        if python_version != "3.13+" and "gevent" in str(requirement_issues):
            start_cmd = "gunicorn --bind 0.0.0.0:$PORT --worker-class gevent --workers 1 --timeout 120 run:app"
        print(f"   {start_cmd}")
        
        return True
    else:
        print("\n❌ STARTUP FAILED - Check the errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
