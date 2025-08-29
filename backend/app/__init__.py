import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models.chat import db


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Application factory pattern"""
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
    
    # Configure CORS - allow all origins for development
    CORS(app, resources={
    
    # Register blueprints
    from routes.api import api_bp
    from routes.chat import chat_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'service': 'PocketPro SBA',
            'version': '1.0.0',
            'status': 'running'
        })

    @app.before_request
    def log_request_info():
        logger.info('Request: %s %s', request.method, request.path)

    @app.after_request
    def log_response_info(response):
        logger.info('Response: %s', response.status)
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
