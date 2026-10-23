#!/usr/bin/env python3
"""
The single backend entry point for PocketPro:SBA.

Every launcher uses ``wsgi:application``:
  - Procfile / Fly / Render:  gunicorn wsgi:application
  - Dockerfile.production:    gunicorn wsgi:application
  - Dockerfile.dev / compose: gunicorn wsgi:application --reload (FLASK_ENV=development)
  - start.sh, start-dev*.sh:  gunicorn wsgi:application
  - Windows (no gunicorn):    python wsgi.py
FLASK_ENV defaults to production here, so SECRET_KEY must be set unless
FLASK_ENV=development is exported first.
"""
import os
import sys
from pathlib import Path

# Set up the Python path
project_root = Path(__file__).parent.absolute()
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Set environment for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONPATH', f"{project_root}/src:{project_root}")

# Create required directories
required_dirs = ['uploads', 'logs', 'static/js', 'templates']
for dir_name in required_dirs:
    dir_path = project_root / dir_name
    dir_path.mkdir(exist_ok=True)

# Import and configure the Flask app
try:
    from backend.app import create_app

    app = create_app()
    
    # Production never runs with DEBUG on, whatever the config says.
    if os.environ.get('FLASK_ENV', 'production') == 'production':
        app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    # Ensure uploads directory exists
    uploads_dir = project_root / 'uploads'
    uploads_dir.mkdir(exist_ok=True)
    
    print(f"🚀 PocketPro:SBA starting in production mode...")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Python path: {sys.path[:3]}")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'unknown')}")
    
    # Export the app for Gunicorn
    application = app
    
    if __name__ == "__main__":
        # For local testing - ensure proper host/port binding
        port = int(os.environ.get('PORT', 5000))  # hosts (Render/Fly) set PORT
        print(f"🚀 Starting on host=0.0.0.0, port={port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
