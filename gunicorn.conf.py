# Gunicorn configuration for Render.com deployment
import os

# Server socket - Use port 10000 for Render.com compatibility and frontend expectations
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"  # Use 10000 to match frontend and Render.com
backlog = 2048

# Worker processes - optimized for production
workers = int(os.environ.get('WEB_CONCURRENCY', 1))  # Allow scaling via environment variable
worker_class = "sync"  # Added missing worker_class
worker_connections = 1000
timeout = 300  # Increased timeout for slow operations
keepalive = 120  # Increased keepalive
max_requests = 1000
max_requests_jitter = 100
graceful_timeout = 120  # Graceful shutdown timeout

# Use shared memory for worker temp files if available
worker_tmp_dir = "/dev/shm"

# Restart workers after this many requests, with up to jitter requests variation
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "pocketpro-sba"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (not needed for Render.com)
keyfile = None
certfile = None

# Error handling and reliability
capture_output = True
enable_stdio_inheritance = True

# Process management
reuse_port = True
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Preload and memory management
max_worker_connections = 1000

# Logging configuration for debugging - optimized startup sequence
def when_ready(server):
    server.log.info("=== PocketPro SBA Server Starting ===")
    server.log.info("Server is ready. Spawning workers")
    server.log.info("Binding to: %s", server.address)
    server.log.info("Environment: %s", os.environ.get('ENVIRONMENT', 'development'))
    server.log.info("Worker concurrency: %s", os.environ.get('WEB_CONCURRENCY', 1))
    server.log.info("Expected API endpoints:")
    server.log.info("  - /api/info (system info)")
    server.log.info("  - /api/models (available models)")
    server.log.info("  - /api/documents (document management)")
    server.log.info("  - /api/collections/stats (collection statistics)")
    server.log.info("  - /api/search/filters (search filters)")
    server.log.info("  - /api/assistants (AI assistants)")
    server.log.info("  - /health (health check)")
    server.log.info("=== Startup Complete ===")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal - shutting down gracefully")

def pre_fork(server, worker):
    server.log.info("Pre-fork: Preparing worker (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Post-fork: Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker fully initialized and ready (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.error("Worker aborted unexpectedly (pid: %s)", worker.pid)

def on_exit(server):
    server.log.info("=== PocketPro SBA Server Shutting Down ===")

def on_reload(server):
    server.log.info("=== PocketPro SBA Server Reloading ===")
