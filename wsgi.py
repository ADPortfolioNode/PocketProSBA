#!/usr/bin/env python3
"""
Simplified entry point for Render.com deployment
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
    from app import app
    
    # Configure for production
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
        port = int(os.environ.get('PORT', 10000))  # Default to 10000 per Render.com docs
        print(f"🚀 Starting on host=0.0.0.0, port={port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
except Exception as e:
    print(f"❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
