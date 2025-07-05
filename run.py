#!/usr/bin/env python3
"""
Render.com optimized entry point for PocketPro:SBA Edition
"""
import os
import sys
from pathlib import Path

# Set up the Python path for Render deployment
project_root = Path(__file__).parent.absolute()
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Set environment defaults for Render
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_APP', 'run.py')

# Create required directories
required_dirs = ['uploads', 'logs', 'chromadb_data', 'static/js', 'templates']
for dir_path in required_dirs:
    (project_root / dir_path).mkdir(parents=True, exist_ok=True)

def create_fallback_app():
    """Create a minimal Flask app if imports fail"""
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "PocketPro:SBA Backend",
            "version": "1.0.0",
            "environment": os.environ.get('FLASK_ENV', 'production')
        })
    
    @app.route('/')
    def index():
        return jsonify({
            "name": "PocketPro:SBA Edition",
            "description": "RAG-powered SBA business assistant",
            "status": "running",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "api": "/api/*"
            }
        })
    
    return app

try:
    # Try to import the main application
    print("🔄 Importing PocketPro:SBA application...")
    from app import app, socketio
    print("✅ Application imported successfully")
    
    # Wrap with WSGI for Gunicorn compatibility
    application = app
    
except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    print("🔄 Creating fallback application...")
    application = create_fallback_app()
    app = application
    socketio = None
    print("✅ Fallback application created")

if __name__ == '__main__':
    import logging
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Try to import config, fallback to environment variables
    try:
        from src.utils.config import config
        # Validate configuration
        if not config.validate_config():
            print("Configuration validation failed. Please check your environment variables.")
            sys.exit(1)
        
        # Ensure required directories exist
        config.ensure_directories()
        
        HOST = config.HOST
        PORT = config.PORT
        FLASK_ENV = config.FLASK_ENV
    except ImportError:
        print("⚠️  Config module not available, using environment variables")
        HOST = os.environ.get('HOST', '0.0.0.0')
        PORT = int(os.environ.get('PORT', 5000))
        FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    
    logger.info(f"🚀 Starting PocketPro SBA via run.py on port {PORT}")
    
    # For production, use gunicorn. For development, use Flask dev server
    if FLASK_ENV == 'production':
        import gunicorn.app.wsgiapp as wsgi
        wsgi.run()
    else:
        app.run(host='0.0.0.0', port=PORT, debug=(FLASK_ENV == 'development'), threaded=True)
        app.run(
            host=HOST,
            port=PORT,
            debug=(FLASK_ENV == 'development')
        )
