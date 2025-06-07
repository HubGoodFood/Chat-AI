# Redis缓存和性能监控配置指南

## 🚀 概述

本指南将帮助您配置Redis分布式缓存和性能监控系统，进一步提升Chat AI应用的性能和可观测性。

## 📋 功能特性

### Redis缓存层
- **分布式缓存**: 支持多实例共享缓存
- **自动故障转移**: Redis不可用时自动回退到本地缓存
- **连接池管理**: 高效的连接复用
- **缓存统计**: 详细的命中率和性能指标

### 性能监控系统
- **实时指标收集**: CPU、内存、响应时间等
- **API性能监控**: 端点级别的性能分析
- **模型性能跟踪**: ML模型推理时间监控
- **自动告警**: 性能阈值超标时自动告警
- **可视化仪表板**: Web界面实时查看性能数据

## 🔧 安装配置

### 1. 安装依赖

```bash
# 使用包含Redis和监控的轻量级依赖
pip install -r requirements_lightweight.txt
```

### 2. Redis安装

#### 本地开发环境

**Windows (使用WSL或Docker):**
```bash
# 使用Docker (推荐)
docker run -d --name redis-cache -p 6379:6379 redis:7-alpine

# 或使用WSL安装
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**macOS:**
```bash
# 使用Homebrew
brew install redis
brew services start redis
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### 生产环境

**云服务推荐:**
- **AWS**: ElastiCache for Redis
- **Azure**: Azure Cache for Redis  
- **Google Cloud**: Memorystore for Redis
- **阿里云**: 云数据库Redis版
- **腾讯云**: 云数据库Redis

### 3. 环境变量配置

在您的环境中设置以下变量：

```bash
# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# 监控配置
MONITORING_ENABLED=true

# 缓存配置
CACHE_ENABLED=true
```

**生产环境示例:**
```bash
# 使用Redis云服务
REDIS_URL=redis://username:password@your-redis-host:6379/0
REDIS_ENABLED=true

# 启用详细监控
MONITORING_ENABLED=true
```

## 📊 使用指南

### 1. 访问监控仪表板

启动应用后，访问监控仪表板：
```
http://localhost:5000/monitoring/dashboard
```

仪表板提供以下信息：
- **系统状态**: 运行时间、总体健康状态
- **请求统计**: 总请求数、响应时间分布
- **资源使用**: CPU、内存使用情况
- **缓存性能**: 命中率、Redis状态
- **API端点**: 各端点性能详情
- **模型性能**: ML模型推理时间

### 2. API接口

#### 获取性能指标
```bash
curl http://localhost:5000/monitoring/api/metrics
```

#### 获取缓存统计
```bash
curl http://localhost:5000/monitoring/api/cache
```

#### 健康检查
```bash
curl http://localhost:5000/monitoring/api/health
```

#### 导出监控数据
```bash
curl http://localhost:5000/monitoring/api/export
```

### 3. 缓存使用示例

```python
from src.core.cache import CacheManager

# 初始化缓存管理器（支持Redis）
cache_manager = CacheManager(enable_redis=True)

# 设置缓存
cache_manager.cache_llm_response("用户问题", "AI回答", ttl_hours=24)

# 获取缓存
response = cache_manager.get_llm_cached_response("用户问题")

# 获取缓存统计
stats = cache_manager.get_cache_stats()
print(f"缓存命中率: {stats.get('redis_hit_rate', 0)}%")
```

### 4. 性能监控使用

```python
from src.core.performance_monitor import get_global_monitor, monitor_performance

# 获取全局监控器
monitor = get_global_monitor()

# 使用装饰器监控函数性能
@monitor_performance(monitor, endpoint='/api/custom')
def my_api_function():
    # 您的API逻辑
    pass

# 手动记录性能指标
monitor.record_model_performance('intent_classifier', 'predict', 15.5)
```

## ⚙️ 高级配置

### 1. Redis连接池配置

```python
# 在src/core/redis_cache.py中自定义连接池
self.connection_pool = ConnectionPool.from_url(
    self.redis_url,
    max_connections=50,        # 最大连接数
    retry_on_timeout=True,     # 超时重试
    socket_connect_timeout=10, # 连接超时
    socket_timeout=10,         # 读写超时
    health_check_interval=30   # 健康检查间隔
)
```

### 2. 监控告警配置

```python
from src.core.performance_monitor import get_global_monitor

monitor = get_global_monitor()

# 自定义告警阈值
monitor.alert_thresholds.update({
    'response_time_ms': 1000,    # 1秒
    'error_rate_percent': 2,     # 2%
    'memory_usage_percent': 70,  # 70%
    'cpu_usage_percent': 70      # 70%
})

# 添加告警回调
def alert_callback(alert):
    print(f"🚨 告警: {alert['type']} - {alert['value']}")
    # 发送邮件、短信或Slack通知

monitor.add_alert_callback(alert_callback)
```

### 3. 缓存策略优化

```python
# 不同类型数据使用不同的TTL
cache_manager.cache_llm_response(query, response, ttl_hours=24)  # LLM响应
cache_manager.set_cache("product_data", data, ttl_seconds=3600)  # 产品数据
cache_manager.set_user_session(user_id, session, ttl_minutes=30) # 用户会话
```

## 📈 性能优化建议

### 1. Redis优化
- **内存优化**: 设置合适的maxmemory和淘汰策略
- **持久化**: 根据需求选择RDB或AOF
- **网络优化**: 使用pipeline批量操作
- **监控**: 定期检查Redis性能指标

### 2. 监控优化
- **采样率**: 高流量时降低监控采样率
- **数据保留**: 设置合适的历史数据保留期
- **告警策略**: 避免告警风暴，设置合理阈值

### 3. 应用优化
- **缓存预热**: 应用启动时预加载热点数据
- **缓存穿透**: 对空结果也进行缓存
- **缓存雪崩**: 设置随机TTL避免同时过期

## 🔍 故障排除

### 1. Redis连接问题
```bash
# 检查Redis服务状态
redis-cli ping

# 检查连接
redis-cli -h your-host -p 6379 ping

# 查看Redis日志
tail -f /var/log/redis/redis-server.log
```

### 2. 监控数据异常
```bash
# 检查监控进程
ps aux | grep python

# 查看应用日志
tail -f logs/app.log

# 检查系统资源
htop
```

### 3. 性能问题诊断
```python
# 运行性能测试
python test_optimization.py

# 检查缓存状态
curl http://localhost:5000/monitoring/api/cache

# 导出详细指标
curl http://localhost:5000/monitoring/api/export
```

## 📊 监控指标说明

### 系统指标
- **CPU使用率**: 系统和进程CPU占用
- **内存使用**: 系统和进程内存占用
- **运行时间**: 应用启动后的运行时间

### 应用指标
- **请求总数**: 处理的HTTP请求总数
- **响应时间**: 各端点的平均/最大/最小响应时间
- **错误率**: HTTP错误响应的比例
- **并发数**: 当前处理的并发请求数

### 缓存指标
- **命中率**: 缓存命中的百分比
- **命中数/未命中数**: 具体的命中和未命中次数
- **缓存大小**: 当前缓存中的条目数量
- **Redis状态**: Redis服务的可用性

### 模型指标
- **推理时间**: ML模型的平均推理时间
- **调用次数**: 模型被调用的总次数
- **错误次数**: 模型推理失败的次数

## 🎯 最佳实践

1. **监控告警**: 设置合理的告警阈值，避免误报
2. **缓存策略**: 根据数据特性选择合适的TTL
3. **性能基线**: 建立性能基线，便于异常检测
4. **定期检查**: 定期查看监控数据，优化性能瓶颈
5. **容量规划**: 根据监控数据进行容量规划

通过Redis缓存和性能监控，您的Chat AI应用将具备：
- **更高的性能**: 分布式缓存减少重复计算
- **更好的可观测性**: 实时了解应用运行状态
- **更强的稳定性**: 及时发现和解决性能问题
- **更易的运维**: 可视化监控简化运维工作
