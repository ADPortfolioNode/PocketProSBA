import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'production')
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        }
    })
    
    # Register blueprints
    try:
        from backend.blueprints.health import health_bp
        from backend.blueprints.rag import rag_bp
    except ImportError:
        # Fallback for local development
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from blueprints.health import health_bp
        from blueprints.rag import rag_bp
    
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(rag_bp, url_prefix='/api')
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'service': 'PocketPro SBA',
            'version': '1.0.0',
            'status': 'running'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
