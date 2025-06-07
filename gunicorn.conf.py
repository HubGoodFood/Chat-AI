# Gunicorn配置文件
import os
import multiprocessing

# 服务器套接字
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker进程
workers = 1  # 在Render的免费层使用单个worker
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5分钟超时，足够模型加载
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# 预加载应用
preload_app = True

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "chat-ai"

# 安全
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 性能调优
worker_tmp_dir = "/dev/shm"  # 使用内存文件系统

def when_ready(server):
    """服务器准备就绪时的回调"""
    server.log.info("服务器已准备就绪")

def worker_int(worker):
    """Worker被中断时的回调"""
    worker.log.info("Worker被中断，正在清理...")

def pre_fork(server, worker):
    """Fork worker之前的回调"""
    server.log.info("正在启动worker...")

def post_fork(server, worker):
    """Fork worker之后的回调"""
    server.log.info(f"Worker {worker.pid} 已启动")
    
def worker_abort(worker):
    """Worker异常终止时的回调"""
    worker.log.error(f"Worker {worker.pid} 异常终止")
