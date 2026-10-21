#!/usr/bin/env python3
"""
Render.com optimized entry point for PocketPro:SBA Edition
"""
import os
import sys
from pathlib import Path

# Set up the Python path for deployment
project_root = Path(__file__).parent.absolute()
backend_path = project_root / "backend"
src_path = project_root / "src"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

# Set environment defaults for Render
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_APP', 'run.py')

# Create required directories
required_dirs = ['uploads', 'logs', 'chromadb_data', 'static/js', 'templates']
for dir_path in required_dirs:
    (project_root / dir_path).mkdir(parents=True, exist_ok=True)

try:
    # Import the main application. There is deliberately no fallback app:
    # if the real app cannot be built, startup must fail loudly instead of
    # serving a stub whose /health says "healthy" while /api/* is missing.
    print("🔄 Importing PocketPro:SBA application...")
    from backend.app import create_app
    app = create_app()
    socketio = None  # SocketIO not currently implemented
    print("✅ Application imported successfully")
    
    # Wrap with WSGI for Gunicorn compatibility
    application = app
    
except Exception:
    import logging
    import traceback
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).critical(
        "PocketPro:SBA failed to start: the backend app could not be imported or created.\n%s",
        traceback.format_exc(),
    )
    sys.exit(1)

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
        app.run(
            host=HOST,
            port=PORT,
            debug=(FLASK_ENV == 'development'),
            threaded=True
        )
