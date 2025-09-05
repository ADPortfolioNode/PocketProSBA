import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class Config:
    # Base directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Server Configuration
    PORT: int = int(os.environ.get('PORT', '5000'))
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'
    TESTING: bool = os.environ.get('TESTING', 'False').lower() == 'true'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR / "app.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Application configuration
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    GEMINI_API_KEY: Optional[str] = os.environ.get('GEMINI_API_KEY')
    CHROMADB_HOST: str = os.environ.get('CHROMADB_HOST', 'localhost')
    CHROMADB_PORT: int = int(os.environ.get('CHROMADB_PORT', '8000'))
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    def validate(self) -> None:
        """Validate configuration and log warnings for missing required settings"""
        if self.SECRET_KEY == 'a_default_secret_key':
            logger.warning("Using default secret key - not recommended for production")
        
        if not self.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set - Gemini features will be disabled")
        
        if self.DEBUG and not self.TESTING:
            logger.warning("Running in DEBUG mode - not recommended for production")

        # Additional validation for CORS origin
        if not self.FRONTEND_URL.startswith("http"):
            logger.warning(f"FRONTEND_URL '{self.FRONTEND_URL}' does not appear to be a valid URL")


class TestConfig(Config):
    """Configuration for testing environment"""
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('TEST_DATABASE_URL') or f'sqlite:///{Config.BASE_DIR / "test.db"}'
    WTF_CSRF_ENABLED: bool = False
