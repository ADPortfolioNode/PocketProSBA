"""
Gunicorn configuration file for Render.com deployment
"""
import os

# Binding configuration
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 1
threads = 4
timeout = 120
keepalive = 65

# Production settings
errorlog = "-"  # stdout
accesslog = "-"  # stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"

# Prevent application startup timeouts
preload_app = False

# Print diagnostics on startup
def on_starting(server):
    print(f"🚀 Gunicorn starting: binding to {bind}")
    print(f"👷 Workers: {workers}, Threads: {threads}")
    print(f"⏱️ Timeout: {timeout}s, Keepalive: {keepalive}s")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    # Debug environment variables
    print("\n📊 Environment Variables:")
    for key in ['PORT', 'PYTHONPATH', 'FLASK_APP', 'FLASK_ENV']:
        print(f"  {key}: {os.environ.get(key, 'not set')}")
