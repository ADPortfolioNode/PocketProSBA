"""
Gunicorn configuration for Render.com deployment
Optimized for Render.com's environment
"""
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count()))
worker_class = "sync"
worker_connections = 1000
timeout = 60  # Increased timeout for Render.com
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "pocketpro-sba"

# Server mechanics
preload_app = True

# SSL (not needed for Render.com)
keyfile = None
certfile = None

# Error handling and reliability
capture_output = True
enable_stdio_inheritance = True

# Startup and shutdown hooks
def on_starting(server):
    """Log when server is starting"""
    server.log.info("Starting Gunicorn server with Render.com optimized configuration")
    server.log.info(f"Binding to {bind}")
    
def on_exit(server):
    """Log when server is exiting"""
    server.log.info("Shutting down Gunicorn server")
    
def post_fork(server, worker):
    """Log when worker is forked"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")
    
def pre_fork(server, worker):
    """Actions to take before forking a worker"""
    pass
    
def pre_exec(server):
    """Actions to take before exec-ing the new process"""
    server.log.info("Forked child, re-executing.")
    
def when_ready(server):
    """Called when server is ready to receive requests"""
    server.log.info(f"Server is ready. Listening on: {bind}")
    
def worker_int(worker):
    """Called when worker gets SIGINT or SIGQUIT"""
    worker.log.info(f"Worker received interrupt (pid: {worker.pid})")
    
def worker_abort(worker):
    """Called when worker receives SIGABRT"""
    worker.log.info(f"Worker aborted (pid: {worker.pid})")
    
def worker_exit(server, worker):
    """Called when worker exits"""
    server.log.info(f"Worker exited (pid: {worker.pid})")
