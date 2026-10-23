import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def env_bool(name, default=False):
    """Read a boolean env var ("1", "true", "yes", "on" are truthy)."""
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == '':
        return default
    return str(raw).strip().lower() in ('1', 'true', 'yes', 'on')


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def debug_from_env():
    """DEBUG is off unless explicitly enabled with FLASK_DEBUG or DEBUG."""
    return env_bool('FLASK_DEBUG', False) or env_bool('DEBUG', False)

class Config:
    """Base configuration class"""

    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    # Never on by default, in any environment: set FLASK_DEBUG=1 to enable.
    DEBUG = debug_from_env()
    # Which config class is active ("development", "production", "testing").
    APP_ENV = 'base'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///pocketpro.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS configuration
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:3000'

    # Server configuration
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')

    # ChromaDB configuration
    CHROMADB_HOST = os.environ.get('CHROMADB_HOST', 'localhost')
    CHROMADB_PORT = int(os.environ.get('CHROMADB_PORT', 8000))

    # Gemini API configuration (if used)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')

    # Request size cap (uploads included). Oversized requests get a 413 JSON.
    MAX_CONTENT_LENGTH = env_int('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)

    # Rate limiting (Flask-Limiter). In-memory by default (per process);
    # point RATELIMIT_STORAGE_URI at redis://... to share limits across workers.
    RATELIMIT_ENABLED = env_bool('RATELIMIT_ENABLED', True)
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://'
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_AUTH = os.environ.get('RATELIMIT_AUTH') or '10 per minute;100 per hour'
    RATELIMIT_LLM = os.environ.get('RATELIMIT_LLM') or '30 per minute;500 per hour'
    # Number of reverse proxies in front of the app whose X-Forwarded-For can be
    # trusted (e.g. 1 on Render/Fly/nginx). 0 = use the socket address.
    TRUSTED_PROXY_COUNT = env_int('TRUSTED_PROXY_COUNT', 0)

    # Extra CORS origins for production, comma-separated (FRONTEND_URL is added too).
    CORS_ALLOWED_ORIGINS = [
        o.strip() for o in (os.environ.get('CORS_ALLOWED_ORIGINS') or '').split(',') if o.strip()
    ]

class DevelopmentConfig(Config):
    """Development configuration (DEBUG still requires FLASK_DEBUG=1)."""
    APP_ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'

class ProductionConfig(Config):
    """Production configuration"""
    APP_ENV = 'production'
    DEBUG = False
    # Ensure production uses secure settings
    SECRET_KEY = os.environ.get('SECRET_KEY')

class TestingConfig(Config):
    """Testing configuration"""
    APP_ENV = 'testing'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    if config_name == 'production' and not os.environ.get('SECRET_KEY'):
        # Enforce only when production is actually selected, so importing this
        # module (tests, dev) does not crash.
        raise ValueError("SECRET_KEY environment variable is required in production")
    return config.get(config_name, config['default'])
