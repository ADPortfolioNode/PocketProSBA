"""
Windows-compatible Gunicorn configuration for Render.com
Modified to work without fcntl module
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gunicorn.render.windows")

# Get the PORT environment variable
port = int(os.environ.get('PORT', 5000))
logger.info(f"PORT environment variable: {port}")

# Server socket binding configuration
bind = f"0.0.0.0:{port}"
logger.info(f"Binding to: {bind}")

# Worker configuration - minimal for Render
workers = 1
worker_class = "sync"
timeout = 60
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

def on_starting(server):
    logger.info("=== PocketPro SBA Server Starting ===")
    logger.info(f"Binding to: {bind}")
    logger.info(f"Worker concurrency: {workers}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")

def on_exit(server):
    logger.info("=== PocketPro SBA Server Shutting Down ===")
