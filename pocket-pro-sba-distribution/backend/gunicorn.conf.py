import multiprocessing

# Server socket settings
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1
worker_class = "gthread"
threads = 2
worker_tmp_dir = "/dev/shm"

# Timeouts
timeout = 60
keepalive = 5

# Performance settings
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
