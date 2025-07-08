"""
Minimal Gunicorn configuration for memory-constrained environments
"""
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 1024

# Worker processes - Just 1 for memory constraints
workers = 1
worker_class = "sync"
worker_connections = 500
timeout = 60
keepalive = 5

# No threading to reduce memory usage
threads = 1

# Do not use preload to avoid memory duplication
preload_app = False

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "pocketpro-sba-minimal"

# Error handling
capture_output = True

# Memory optimizations
max_requests = 500
max_requests_jitter = 50
