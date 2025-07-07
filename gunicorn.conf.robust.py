# Robust Gunicorn configuration for Render.com deployment
# Addresses 502 Bad Gateway issues with timeouts and worker management
import os

# Server socket - Render.com expects port 5000 from PORT environment variable
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes - Conservative settings for stability
workers = 1  # Single worker to avoid resource contention
worker_class = "sync"  # Sync workers are more stable
worker_connections = 1000
timeout = 300  # 5 minutes - increased for slow operations
keepalive = 120  # 2 minutes - increased for better connection reuse
graceful_timeout = 120  # 2 minutes for graceful shutdown
max_requests = 1000
max_requests_jitter = 100

# Memory management
worker_tmp_dir = "/dev/shm"  # Use shared memory if available
preload_app = True  # Preload app for better memory usage

# Logging - Enhanced for debugging 502 errors
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

# Connection handling
max_worker_connections = 1000

# Hooks for debugging worker issues
def when_ready(server):
    server.log.info("🚀 Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("⚠️ Worker received INT or QUIT signal (pid: %s)", worker.pid)

def pre_fork(server, worker):
    server.log.info("🔄 Pre-fork worker (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("✅ Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("🎯 Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.error("❌ Worker aborted (pid: %s)", worker.pid)

def on_exit(server):
    server.log.info("👋 Server is shutting down")

def on_reload(server):
    server.log.info("🔄 Server is reloading")
