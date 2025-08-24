import os
from pathlib import Path

class Config:
    # Base directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR / "app.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    CHROMADB_HOST = os.environ.get('CHROMADB_HOST', 'localhost')
    CHROMADB_PORT = os.environ.get('CHROMADB_PORT', '8000')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    DEBUG = os.environ.get('DEBUG', False)
    TESTING = os.environ.get('TESTING', False)


class TestConfig(Config):
    """Configuration for testing environment"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or f'sqlite:///{Config.BASE_DIR / "test.db"}'
    WTF_CSRF_ENABLED = False
