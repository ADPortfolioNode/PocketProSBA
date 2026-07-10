import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.config import get_config
from backend.models.chat import db


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory pattern"""
    config_class = get_config(config_name)
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Log database configuration
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Initialize database
    db.init_app(app)

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    # Configure CORS - allow local dev and Docker service origins
    allowed_origins = [
        'http://localhost',
        'http://localhost:3000',
        'http://127.0.0.1',
        'http://127.0.0.1:3000',
        'http://frontend:80',
    ]
    cors_origins = app.config.get('FRONTEND_URL')
    if cors_origins and cors_origins not in allowed_origins:
        allowed_origins.append(cors_origins)

    # Prebuilt frontend (main.*.js) sends Cache-Control on health fetches.
    # Use broad allow_headers so preflight never fails on browser-added headers.
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            "allow_headers": "*",
            "supports_credentials": False,
            "expose_headers": ["Access-Control-Allow-Origin"],
            "max_age": 86400,
        }
    })

    # Register blueprints
    from backend.routes.api import api_bp
    from backend.routes.chat import chat_bp
    from backend.routes.sba import sba_bp
    from backend.routes.rag import rag_bp
    from backend.routes.orchestrator import orchestrator_bp
    try:
        from backend.routes.documents import documents_bp
    except Exception as docs_import_err:
        documents_bp = None
        logger.warning("Documents blueprint unavailable: %s", docs_import_err)

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(sba_bp, url_prefix='/api/sba')
    app.register_blueprint(rag_bp, url_prefix='/api/rag')
    app.register_blueprint(orchestrator_bp, url_prefix='/api/orchestrator')
    if documents_bp is not None:
        app.register_blueprint(documents_bp, url_prefix='/api/documents')

    # Compat: older/baked frontend uses baseURL .../api + path /api/health → /api/api/health
    @app.route('/api/api/health', methods=['GET', 'OPTIONS', 'HEAD'])
    def health_double_api_prefix():
        return jsonify({
            'status': 'healthy',
            'server': {'self': request.host_url.rstrip('/')},
            'compat': 'api_double_prefix',
        }), 200

    @app.route('/api/api/info', methods=['GET', 'OPTIONS', 'HEAD'])
    def info_double_api_prefix():
        return jsonify({
            'service': 'PocketPro SBA',
            'version': '1.0.0',
            'status': 'operational',
            'compat': 'api_double_prefix',
        }), 200

    # Initialize Gemini RAG service
    try:
        from backend.enhanced_gemini_rag_service import enhanced_rag_service
        with app.app_context():
            success = enhanced_rag_service.initialize_full_service()
            if success:
                logger.info("Enhanced Gemini RAG service initialized successfully")
            else:
                logger.warning("Failed to initialize Enhanced Gemini RAG service")
    except Exception as e:
        logger.error(f"Error initializing Gemini RAG service: {str(e)}")

    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'service': 'PocketPro SBA',
            'version': '1.0.0',
            'status': 'running'
        })

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'PocketPro SBA',
            'version': '1.0.0'
        }), 200

    # Test CORS route
    @app.route('/test-cors')
    def test_cors():
        return jsonify({'message': 'CORS test successful'})

    def _cors_origin_allowed(origin: str) -> bool:
        if not origin:
            return False
        if origin in allowed_origins:
            return True
        # Dev convenience: any localhost / 127.0.0.1 port
        return origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:')

    @app.before_request
    def log_request_info():
        logger.info('Request: %s %s', request.method, request.path)
        # Fast-path OPTIONS so preflight never depends on blueprint 404s
        if request.method == 'OPTIONS':
            resp = app.make_default_options_response()
            origin = request.headers.get('Origin')
            if _cors_origin_allowed(origin):
                resp.headers['Access-Control-Allow-Origin'] = origin
                resp.headers['Access-Control-Allow-Methods'] = (
                    'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
                )
                req_hdrs = request.headers.get('Access-Control-Request-Headers')
                resp.headers['Access-Control-Allow-Headers'] = (
                    req_hdrs
                    or 'Content-Type, Authorization, Cache-Control, Pragma, Expires, Accept, Origin, X-Requested-With'
                )
                resp.headers['Access-Control-Max-Age'] = '86400'
                resp.headers['Vary'] = 'Origin'
            return resp

    @app.after_request
    def log_response_info(response):
        logger.info('Response: %s', response.status)
        # Belt-and-suspenders CORS for all responses (including 404 error handlers)
        origin = request.headers.get('Origin')
        if _cors_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
            req_hdrs = request.headers.get('Access-Control-Request-Headers')
            if req_hdrs:
                response.headers['Access-Control-Allow-Headers'] = req_hdrs
            else:
                response.headers.setdefault(
                    'Access-Control-Allow-Headers',
                    'Content-Type, Authorization, Cache-Control, Pragma, Expires, Accept, Origin, X-Requested-With',
                )
            response.headers.setdefault(
                'Access-Control-Allow-Methods',
                'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD',
            )
            response.headers.setdefault('Vary', 'Origin')
        return response

    @app.errorhandler(400)
    def bad_request(error):
        logger.error('Bad Request: %s', error)
        return jsonify({"error": "Bad Request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        logger.error('Not Found: %s', request.path)
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.exception('Internal Server Error: %s', error)
        return jsonify({"error": "Internal Server Error"}), 500

    return app
