#!/usr/bin/env python3
"""
Entry point for PocketPro:SBA self-hosted distribution
"""
import os
import sys
from pathlib import Path

# Set up the Python path
project_root = Path(__file__).parent.absolute()
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

# Set environment defaults
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_APP', 'run.py')

# Create required directories
required_dirs = ['uploads', 'logs', 'chromadb_data']
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
    from backend.app import create_app
    app = create_app()
    print("✅ Application imported successfully")

    # Wrap with WSGI for Gunicorn compatibility
    application = app

except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()
    print("🔄 Creating fallback application...")
    application = create_fallback_app()
    app = application
    print("✅ Fallback application created")

if __name__ == '__main__':
    import logging
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Use environment variables for configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

    logger.info(f"🚀 Starting PocketPro SBA via run.py on port {PORT}")

    # For production, use gunicorn. For development, use Flask dev server
    if FLASK_ENV == 'production':
        import gunicorn.app.wsgiapp as wsgi
        wsgi.run()
    else:
        app.run(
            host=HOST,
            port=PORT,
            debug=(FLASK_ENV == 'development'),
            threaded=True
        )
