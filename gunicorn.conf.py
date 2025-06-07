# 优化的Gunicorn配置 - 针对轻量级Chat AI项目
import os
import multiprocessing

# 服务器套接字
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# 工作进程配置 - 针对轻量级应用优化
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)  # 限制最大工作进程数
worker_class = "sync"  # 同步工作器，适合CPU密集型任务
worker_connections = 1000
max_requests = 1000  # 防止内存泄漏
max_requests_jitter = 50
timeout = 30  # 减少超时时间，因为轻量级模型响应更快
keepalive = 2

# 内存优化
preload_app = True  # 预加载应用，节省内存
worker_tmp_dir = "/dev/shm"  # 使用内存文件系统

# 日志配置
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "chat-ai-optimized"

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 性能优化
sendfile = True
reuse_port = True

# 优雅重启
graceful_timeout = 30
worker_tmp_dir = "/dev/shm"

# 环境变量优化
raw_env = [
    "TOKENIZERS_PARALLELISM=false",
    "PYTHONUNBUFFERED=1",
    "PYTHONDONTWRITEBYTECODE=1",
    "MODEL_TYPE=lightweight",
    "LAZY_LOADING=true"
]

def when_ready(server):
    """服务器准备就绪时的回调"""
    server.log.info("Chat AI 轻量级服务器已启动并准备接收请求")

def worker_int(worker):
    """工作进程中断时的回调"""
    worker.log.info("工作进程 %s 正在优雅关闭", worker.pid)

def pre_fork(server, worker):
    """工作进程fork前的回调"""
    server.log.info("工作进程 %s 即将启动", worker.pid)

def post_fork(server, worker):
    """工作进程fork后的回调"""
    server.log.info("工作进程 %s 已启动", worker.pid)
    
    # 在每个工作进程中设置优化
    import gc
    gc.set_threshold(700, 10, 10)  # 优化垃圾回收

def worker_abort(worker):
    """工作进程异常终止时的回调"""
    worker.log.error("工作进程 %s 异常终止", worker.pid)
