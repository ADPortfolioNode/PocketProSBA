import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    CHROMADB_HOST = os.environ.get('CHROMADB_HOST', 'localhost')
    CHROMADB_PORT = os.environ.get('CHROMADB_PORT', '8000')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')