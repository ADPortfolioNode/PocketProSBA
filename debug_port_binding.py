#!/usr/bin/env python3
"""
Debug script to diagnose port binding issues on Render.com
This will print all environment variables and port configurations
"""
import os
import sys
import importlib.util
import inspect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_port_configuration():
    """Debug port configuration"""
    # Print environment variables
    logger.info("=== Environment Variables ===")
    for key, value in os.environ.items():
        if key.lower() in ('port', 'flask_port', 'gunicorn_port', 'bind_port'):
            logger.info(f"{key}={value}")
    
    # Check PORT environment variable
    port = os.environ.get('PORT')
    logger.info(f"PORT environment variable: {port}")
    
    # Check for gunicorn configuration files
    config_files = [
        'gunicorn.conf.py',
        'gunicorn.conf.robust.py',
        'gunicorn.render.py',
        'gunicorn.render.conf.py',
        'gunicorn.render-minimal.py'
    ]
    
    logger.info("=== Gunicorn Config Files ===")
    for file in config_files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    content = f.read()
                bind_line = [line for line in content.splitlines() if 'bind =' in line]
                logger.info(f"{file}: {bind_line[0] if bind_line else 'No bind configuration found'}")
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
        else:
            logger.info(f"{file}: Not found")
    
    # Try to identify how Gunicorn is binding
    logger.info("=== Command Line Args ===")
    logger.info(f"sys.argv: {sys.argv}")
    
    # Check if specific modules that might override binding are imported
    logger.info("=== Module Inspection ===")
    for name in list(sys.modules.keys()):
        if 'gunicorn' in name.lower() or 'wsgi' in name.lower():
            logger.info(f"Module loaded: {name}")
    
    return {
        'port_env_var': port,
        'argv': sys.argv,
        'cwd': os.getcwd(),
        'python_path': sys.path,
    }

if __name__ == "__main__":
    logger.info("🔍 Debugging Port Configuration Issues")
    config_info = debug_port_configuration()
    logger.info(f"Debug information gathered: {config_info}")
