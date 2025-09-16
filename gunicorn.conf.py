import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = 'sync'
worker_connections = 1000
timeout = 60  # Increased from default 30s
keepalive = 2

# Memory management
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'briefme-api'

# Graceful timeout
graceful_timeout = 30