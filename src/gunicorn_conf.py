from multiprocessing import cpu_count

#socket path
bind = "unix:/backend/gunicorn.sock"

#worker options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

#Logging options
loglevel = 'debug'
accesslog = '/backend/gunicorn_access.log'
errorlog = '/backend/gunicorn_error.log'
