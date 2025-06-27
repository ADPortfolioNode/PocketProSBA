"""
Configuration management for WhiteLabelRAG application.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Application configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # LLM Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-pro')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.2'))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '1024'))
    
    # ChromaDB Configuration
    CHROMA_DB_IMPL = os.getenv('CHROMA_DB_IMPL', 'duckdb+parquet')
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './chromadb_data')
    CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
    CHROMA_PORT = int(os.getenv('CHROMA_PORT', '8000'))
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'documents')
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md', 'csv'}
    
    # Embedding Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '500'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))
    
    # Search Configuration
    DEFAULT_TOP_K = int(os.getenv('DEFAULT_TOP_K', '3'))
    MIN_RELEVANCE_SCORE = float(os.getenv('MIN_RELEVANCE_SCORE', '0.7'))
    
    # Redis Configuration (for session storage)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    USE_REDIS = os.getenv('USE_REDIS', 'false').lower() == 'true'
    
    # WebSocket Configuration
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv('SOCKETIO_CORS_ALLOWED_ORIGINS', '*')
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        required_vars = ['GEMINI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        directories = [cls.UPLOAD_FOLDER, cls.CHROMA_DB_PATH]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


# Global config instance
config = Config()
