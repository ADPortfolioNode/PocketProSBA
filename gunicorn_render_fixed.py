"""
Gunicorn configuration specifically for Render.com
This file is optimized to ensure proper port binding
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gunicorn.render")

# Force the correct port binding
port = int(os.environ.get('PORT', 5000))
logger.info(f"🔍 PORT environment variable: {port}")

# Server socket binding - CRITICAL for Render.com
bind = f"0.0.0.0:{port}"
logger.info(f"🔧 Binding to: {bind}")

# Worker configuration
workers = 2
worker_class = "sync"
timeout = 60
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Print diagnostics on startup
def on_starting(server):
    """Log detailed information when Gunicorn starts"""
    logger.info("=" * 50)
    logger.info("🚀 Gunicorn starting for Render.com deployment")
    logger.info(f"🔧 Binding to: {bind}")
    logger.info(f"👷 Workers: {workers}")
    logger.info(f"⏱️ Timeout: {timeout}s")
    logger.info(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'production')}")
    
    # Debug environment variables
    logger.info("📊 Environment Variables:")
    for key, value in sorted(os.environ.items()):
        if any(x in key.upper() for x in ['PORT', 'FLASK', 'GUNICORN', 'BIND', 'WORKER']):
            logger.info(f"   {key}: {value}")
    
    logger.info("=" * 50)

def post_fork(server, worker):
    """Log when a worker is forked"""
    logger.info(f"Worker {worker.pid} spawned")

def when_ready(server):
    """Log when Gunicorn is ready to accept connections"""
    logger.info("=" * 50)
    logger.info("✅ Gunicorn ready to accept connections")
    logger.info(f"🔧 Listening on: {bind}")
    logger.info("=" * 50)
