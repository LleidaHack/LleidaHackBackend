from multiprocessing import cpu_count

#socket path
bind = "0.0.0.0:8000"

# worker options
workers = cpu_count() + 1
worker_class = "uvicorn.workers.UvicornWorker"

#Logging options
loglevel = 'debug'
accesslog = '-'
errorlog = '-'
capture_output = True
enable_stdio_inheritance = True

# Set only to the actual reverse-proxy addresses; never use "*".
import os
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "")
