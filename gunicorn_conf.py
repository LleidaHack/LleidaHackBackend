import os
from multiprocessing import cpu_count

# socket path
bind = "0.0.0.0:8000"

# worker options. WEB_CONCURRENCY overrides the default so ops can tune the
# process count to the host without rebuilding the image.
workers = int(os.environ.get("WEB_CONCURRENCY", cpu_count() + 1))
worker_class = "uvicorn.workers.UvicornWorker"

# Request lifetime. A CPU-bound handler can stall the async worker's heartbeat;
# the default 30s arbiter timeout then kills it mid-request (seen under load as
# "WORKER TIMEOUT" plus client "unexpected EOF"). Give real requests more room
# while the app-layer body timeout (10s) still bounds slow uploads. Overridable.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
# Reuse connections from the reverse proxy instead of tearing them down per hit.
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "15"))
# Recycle workers periodically so any per-request leak can't grow unbounded on a
# long-lived process. Jitter avoids all workers recycling at once.
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "2000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "200"))

# Logging options
loglevel = "info"
# Uvicorn request logs include query-string verification/reset credentials.
accesslog = None
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True

# Set only to the actual reverse-proxy addresses; never use "*".
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "")
