bind = "127.0.0.1:8000"
workers = 2
timeout = 30
graceful_timeout = 30
keepalive = 5

# Recycle workers periodically to avoid memory leaks / stuck states
max_requests = 1000
max_requests_jitter = 100

worker_class = "sync"
loglevel = "info"
errorlog = "-"
accesslog = "-"
capture_output = True

