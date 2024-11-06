bind = '0.0.0.0:80'
workers = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 10
graceful_timeout = 30
threads = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
capture_output = True
enable_stdio_inheritance = True

# Memory management
worker_tmp_dir = '/dev/shm'
preload_app = True
preload = True
