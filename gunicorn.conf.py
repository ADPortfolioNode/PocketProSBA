import multiprocessing

# Server socket settings
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'pocketpro-backend'

# SSL/TLS settings (if needed)
# keyfile = '/etc/certs/privkey.pem'
# certfile = '/etc/certs/fullchain.pem'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Load application
wsgi_app = 'app:app'