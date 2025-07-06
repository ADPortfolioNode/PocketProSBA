"""
Minimal Gunicorn configuration file for Render.com
"""
import os

# Force the port binding to use environment variable
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Simple worker configuration
workers = 1
threads = 2
timeout = 120

# Debug output
accesslog = "-"
errorlog = "-"
loglevel = "info"

def on_starting(server):
    """Print diagnostic information when starting"""
    print(f"🚀 Gunicorn starting - binding to {bind}")
    print(f"🌐 PORT environment variable: {os.environ.get('PORT', 'not set')}")
    print(f"📂 Current directory: {os.getcwd()}")
