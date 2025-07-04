# Gunicorn configuration for Render.com deployment
import os

# Server socket - Use port 5000 for frontend compatibility, Render.com will override via PORT env var
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"  # Use 5000 to match frontend expectations
backlog = 2048

# Worker processes
workers = 1
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

# Logging configuration for debugging
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")
    server.log.info("Binding to: %s", server.address)

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
