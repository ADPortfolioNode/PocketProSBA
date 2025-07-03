#!/usr/bin/env python3
"""
Quick startup fixer for PocketPro:SBA
Run this if the PowerShell script isn't working
"""

import os
import sys

def create_working_app():
    """Create a minimal working Flask app"""
    
    app_content = '''"""
PocketPro:SBA - Flask Application Factory
Minimal working version
"""

import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-2024')
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "🚀 PocketPro:SBA is running!",
            "status": "success",
            "version": "1.0.0"
        })
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "service": "PocketPro:SBA"})
    
    @app.route('/api/test')
    def api_test():
        return jsonify({"message": "API is working", "status": "ok"})
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
'''
    
    with open('app.py', 'w') as f:
        f.write(app_content)
    
    run_content = '''#!/usr/bin/env python3
"""
PocketPro:SBA - Main runner
"""

import os
from app import create_app

# Create app for gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting PocketPro:SBA on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
'''
    
    with open('run.py', 'w') as f:
        f.write(run_content)

def main():
    print("🔧 PocketPro:SBA Startup Fixer")
    print("=" * 40)
    
    # Create working files
    create_working_app()
    print("✅ Created working app.py and run.py")
    
    # Test import
    try:
        from app import create_app
        app = create_app()
        print("✅ App imports successfully")
        
        # Test route
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Basic route works")
                print("🚀 Application is ready to start!")
                print()
                print("To start: python run.py")
                print("Then visit: http://localhost:5000")
            else:
                print(f"❌ Route test failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print("Check that Flask is installed: pip install flask")

if __name__ == "__main__":
    main()
