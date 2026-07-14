#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys
from pathlib import Path

# Set up the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Set environment for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONPATH', str(project_root))

# Create required directories
required_dirs = ['uploads', 'logs', 'chromadb_data']
for dir_name in required_dirs:
    dir_path = project_root / dir_name
    dir_path.mkdir(parents=True, exist_ok=True)

# Import and configure the Flask app
try:
    from backend.app import create_app

    app = create_app()

    # Configure for production
    app.config['DEBUG'] = False
    app.config['TESTING'] = False

    # Ensure uploads directory exists
    uploads_dir = project_root / 'uploads'
    uploads_dir.mkdir(exist_ok=True)

    print(f"🚀 PocketPro:SBA starting in production mode...")
    print(f"📁 Project root: {project_root}")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'unknown')}")

    # Export the app for Gunicorn
    application = app

    if __name__ == "__main__":
        # For local testing
        port = int(os.environ.get('PORT', 5000))
        print(f"🚀 Starting on host=0.0.0.0, port={port}")
        app.run(host='0.0.0.0', port=port, debug=False)

except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
