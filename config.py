import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret')
    # Add more as needed
