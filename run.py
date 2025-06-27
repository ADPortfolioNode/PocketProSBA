#!/usr/bin/env python3
"""
PocketPro:SBA Edition - Main application runner
"""
import os
import sys

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app import app, socketio
from src.utils.config import config

if __name__ == '__main__':
    # Validate configuration
    if not config.validate_config():
        print("Configuration validation failed. Please check your environment variables.")
        sys.exit(1)
    
    # Ensure required directories exist
    config.ensure_directories()
    
    print(f"Starting PocketPro:SBA Edition on {config.HOST}:{config.PORT}")
    print(f"Environment: {config.FLASK_ENV}")
    
    # Run the application
    socketio.run(
        app, 
        host=config.HOST, 
        port=config.PORT, 
        debug=(config.FLASK_ENV == 'development')
    )
