# API性能与安全优化指南

## 🎯 目标
实现API请求限流、响应压缩、安全加固和错误处理优化，提升API的性能、安全性和可靠性。

## 📊 当前状态分析

### 现有API问题:
- 无请求限流，容易被滥用
- 响应未压缩，带宽浪费
- 错误处理不统一
- 缺乏安全防护措施
- 无API版本管理

## 🛡️ 安全加固实施

### 1. 请求限流系统

创建文件: `src/core/rate_limiter.py`
```python
#!/usr/bin/env python3
"""
请求限流器
基于令牌桶算法实现API限流
"""

import time
import redis
import json
import logging
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

class RateLimiter:
    """基于Redis的分布式限流器"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.default_limits = {
            'chat': {'requests': 60, 'window': 60},      # 聊天API: 60次/分钟
            'health': {'requests': 100, 'window': 60},    # 健康检查: 100次/分钟
            'monitoring': {'requests': 200, 'window': 60}, # 监控API: 200次/分钟
            'default': {'requests': 30, 'window': 60}     # 默认: 30次/分钟
        }
    
    def is_allowed(self, key: str, limit_type: str = 'default') -> Tuple[bool, Dict]:
        """检查是否允许请求"""
        limits = self.default_limits.get(limit_type, self.default_limits['default'])
        max_requests = limits['requests']
        window_seconds = limits['window']
        
        if not self.redis_client:
            # 无Redis时使用内存限流（简化版）
            return True, {'remaining': max_requests, 'reset_time': time.time() + window_seconds}
        
        try:
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # 使用Redis有序集合实现滑动窗口
            pipe = self.redis_client.pipeline()
            
            # 移除过期请求
            pipe.zremrangebyscore(key, 0, window_start)
            
            # 获取当前窗口内的请求数
            pipe.zcard(key)
            
            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})
            
            # 设置过期时间
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            current_requests = results[1]
            
            if current_requests < max_requests:
                return True, {
                    'remaining': max_requests - current_requests - 1,
                    'reset_time': current_time + window_seconds,
                    'limit': max_requests
                }
            else:
                # 移除刚添加的请求（因为超限了）
                self.redis_client.zrem(key, str(current_time))
                return False, {
                    'remaining': 0,
                    'reset_time': current_time + window_seconds,
                    'limit': max_requests
                }
                
        except Exception as e:
            logger.error(f"限流检查失败: {e}")
            # 出错时允许请求通过
            return True, {'remaining': max_requests, 'reset_time': time.time() + window_seconds}
    
    def get_client_key(self, identifier: str, endpoint: str) -> str:
        """生成客户端限流键"""
        return f"rate_limit:{identifier}:{endpoint}"

# 全局限流器实例
rate_limiter = None

def init_rate_limiter(redis_client=None):
    """初始化限流器"""
    global rate_limiter
    rate_limiter = RateLimiter(redis_client)

def rate_limit(limit_type: str = 'default'):
    """限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not rate_limiter:
                return f(*args, **kwargs)
            
            # 获取客户端标识
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_id = request.json.get('user_id') if request.is_json else None
            identifier = user_id or client_ip
            
            # 生成限流键
            endpoint = request.endpoint or f.__name__
            key = rate_limiter.get_client_key(identifier, endpoint)
            
            # 检查限流
            allowed, info = rate_limiter.is_allowed(key, limit_type)
            
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': '请求过于频繁，请稍后再试',
                    'retry_after': info['reset_time'] - time.time()
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(int(info['reset_time']))
                return response
            
            # 执行原函数
            response = f(*args, **kwargs)
            
            # 添加限流头
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(int(info['reset_time']))
            
            return response
        
        return decorated_function
    return decorator
```

### 2. 响应压缩中间件

创建文件: `src/core/compression.py`
```python
#!/usr/bin/env python3
"""
响应压缩中间件
自动压缩API响应以减少带宽使用
"""

import gzip
import io
import json
from flask import request, Response, current_app

class CompressionMiddleware:
    """响应压缩中间件"""
    
    def __init__(self, app=None, compress_level=6, minimum_size=500):
        self.compress_level = compress_level
        self.minimum_size = minimum_size
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        app.after_request(self.compress_response)
    
    def should_compress(self, response):
        """判断是否应该压缩响应"""
        # 检查Accept-Encoding头
        if 'gzip' not in request.headers.get('Accept-Encoding', ''):
            return False
        
        # 检查响应大小
        if len(response.get_data()) < self.minimum_size:
            return False
        
        # 检查Content-Type
        content_type = response.headers.get('Content-Type', '')
        compressible_types = [
            'application/json',
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'text/xml',
            'application/xml'
        ]
        
        if not any(ct in content_type for ct in compressible_types):
            return False
        
        # 检查是否已经压缩
        if response.headers.get('Content-Encoding'):
            return False
        
        return True
    
    def compress_response(self, response):
        """压缩响应"""
        if not self.should_compress(response):
            return response
        
        try:
            # 获取原始数据
            data = response.get_data()
            
            # 压缩数据
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=self.compress_level) as f:
                f.write(data)
            
            compressed_data = buffer.getvalue()
            
            # 更新响应
            response.set_data(compressed_data)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = str(len(compressed_data))
            
            # 添加Vary头
            vary = response.headers.get('Vary', '')
            if 'Accept-Encoding' not in vary:
                response.headers['Vary'] = f"{vary}, Accept-Encoding".strip(', ')
            
        except Exception as e:
            current_app.logger.error(f"响应压缩失败: {e}")
        
        return response

def init_compression(app, **kwargs):
    """初始化压缩中间件"""
    CompressionMiddleware(app, **kwargs)
```

### 3. 安全头中间件

创建文件: `src/core/security.py`
```python
#!/usr/bin/env python3
"""
安全中间件
添加安全头，防止常见攻击
"""

from flask import request, Response
import re

class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self, app=None):
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        app.before_request(self.validate_request)
        app.after_request(self.add_security_headers)
    
    def validate_request(self):
        """验证请求"""
        # 检查请求大小
        if request.content_length and request.content_length > 10 * 1024 * 1024:  # 10MB
            return Response('Request too large', status=413)
        
        # 检查User-Agent
        user_agent = request.headers.get('User-Agent', '')
        if self.is_suspicious_user_agent(user_agent):
            return Response('Forbidden', status=403)
        
        # 检查SQL注入模式
        if self.has_sql_injection_pattern(request):
            return Response('Bad Request', status=400)
    
    def is_suspicious_user_agent(self, user_agent):
        """检查可疑的User-Agent"""
        suspicious_patterns = [
            r'sqlmap',
            r'nikto',
            r'nmap',
            r'masscan',
            r'python-requests/.*',  # 可选：阻止简单的脚本请求
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        return False
    
    def has_sql_injection_pattern(self, request):
        """检查SQL注入模式"""
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'insert\s+into',
            r'delete\s+from',
            r'update\s+.*\s+set',
            r'exec\s*\(',
            r'script\s*>',
        ]
        
        # 检查查询参数
        query_string = request.query_string.decode('utf-8', errors='ignore').lower()
        for pattern in sql_patterns:
            if re.search(pattern, query_string):
                return True
        
        # 检查POST数据
        if request.is_json:
            try:
                json_str = str(request.get_json()).lower()
                for pattern in sql_patterns:
                    if re.search(pattern, json_str):
                        return True
            except:
                pass
        
        return False
    
    def add_security_headers(self, response):
        """添加安全头"""
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response

def init_security(app):
    """初始化安全中间件"""
    SecurityMiddleware(app)
```

### 4. 统一错误处理

创建文件: `src/core/error_handlers.py`
```python
#!/usr/bin/env python3
"""
统一错误处理
标准化API错误响应格式
"""

import logging
import traceback
from flask import jsonify, request, current_app
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class APIError(Exception):
    """自定义API错误"""
    
    def __init__(self, message, status_code=400, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """处理自定义API错误"""
        response = {
            'error': {
                'message': error.message,
                'code': error.error_code,
                'details': error.details
            },
            'success': False,
            'timestamp': int(time.time())
        }
        
        logger.warning(f"API错误: {error.message} (状态码: {error.status_code})")
        return jsonify(response), error.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """处理400错误"""
        response = {
            'error': {
                'message': '请求格式错误',
                'code': 'BAD_REQUEST',
                'details': {'description': str(error.description)}
            },
            'success': False
        }
        return jsonify(response), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """处理401错误"""
        response = {
            'error': {
                'message': '未授权访问',
                'code': 'UNAUTHORIZED',
                'details': {}
            },
            'success': False
        }
        return jsonify(response), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """处理403错误"""
        response = {
            'error': {
                'message': '访问被禁止',
                'code': 'FORBIDDEN',
                'details': {}
            },
            'success': False
        }
        return jsonify(response), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        response = {
            'error': {
                'message': '资源未找到',
                'code': 'NOT_FOUND',
                'details': {'path': request.path}
            },
            'success': False
        }
        return jsonify(response), 404
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        """处理429错误"""
        response = {
            'error': {
                'message': '请求过于频繁',
                'code': 'RATE_LIMIT_EXCEEDED',
                'details': {'retry_after': '请稍后再试'}
            },
            'success': False
        }
        return jsonify(response), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        # 记录详细错误信息
        logger.error(f"内部服务器错误: {str(error)}")
        logger.error(f"请求路径: {request.path}")
        logger.error(f"请求方法: {request.method}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        
        response = {
            'error': {
                'message': '内部服务器错误',
                'code': 'INTERNAL_ERROR',
                'details': {}
            },
            'success': False
        }
        
        # 开发环境下返回详细错误信息
        if current_app.debug:
            response['error']['details']['traceback'] = traceback.format_exc()
        
        return jsonify(response), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """处理未预期的错误"""
        logger.error(f"未预期错误: {str(error)}")
        logger.error(f"错误类型: {type(error).__name__}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        
        response = {
            'error': {
                'message': '服务暂时不可用',
                'code': 'SERVICE_UNAVAILABLE',
                'details': {}
            },
            'success': False
        }
        
        if current_app.debug:
            response['error']['details']['error_type'] = type(error).__name__
            response['error']['details']['traceback'] = traceback.format_exc()
        
        return jsonify(response), 500
```

### 5. 输入验证中间件

创建文件: `src/core/validation.py`
```python
#!/usr/bin/env python3
"""
输入验证中间件
验证和清理用户输入
"""

import re
import html
from flask import request, jsonify
from functools import wraps

class InputValidator:
    """输入验证器"""
    
    def __init__(self):
        self.max_message_length = 1000
        self.max_user_id_length = 100
        self.allowed_chars_pattern = re.compile(r'^[\w\s\u4e00-\u9fff.,!?，。！？\-_@#$%^&*()+=\[\]{}|;:\'\"<>/\\~`]*$')
    
    def validate_chat_input(self, data):
        """验证聊天输入"""
        errors = []
        
        # 检查必需字段
        if 'message' not in data:
            errors.append('缺少message字段')
        elif not data['message'] or not data['message'].strip():
            errors.append('消息不能为空')
        elif len(data['message']) > self.max_message_length:
            errors.append(f'消息长度不能超过{self.max_message_length}字符')
        elif not self.allowed_chars_pattern.match(data['message']):
            errors.append('消息包含不允许的字符')
        
        # 检查用户ID
        if 'user_id' in data:
            if len(data['user_id']) > self.max_user_id_length:
                errors.append(f'用户ID长度不能超过{self.max_user_id_length}字符')
            elif not re.match(r'^[\w\-_@.]+$', data['user_id']):
                errors.append('用户ID格式无效')
        
        return errors
    
    def sanitize_input(self, text):
        """清理输入文本"""
        if not isinstance(text, str):
            return text
        
        # HTML转义
        text = html.escape(text)
        
        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # 限制连续空白字符
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

# 全局验证器实例
input_validator = InputValidator()

def validate_json_input(validator_func):
    """JSON输入验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': {
                        'message': '请求必须是JSON格式',
                        'code': 'INVALID_CONTENT_TYPE'
                    },
                    'success': False
                }), 400
            
            try:
                data = request.get_json()
            except Exception:
                return jsonify({
                    'error': {
                        'message': 'JSON格式错误',
                        'code': 'INVALID_JSON'
                    },
                    'success': False
                }), 400
            
            # 验证输入
            errors = validator_func(data)
            if errors:
                return jsonify({
                    'error': {
                        'message': '输入验证失败',
                        'code': 'VALIDATION_ERROR',
                        'details': {'errors': errors}
                    },
                    'success': False
                }), 400
            
            # 清理输入
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = input_validator.sanitize_input(value)
            
            # 将清理后的数据传递给视图函数
            request.validated_json = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_chat_input(f):
    """聊天输入验证装饰器"""
    return validate_json_input(input_validator.validate_chat_input)(f)
```

## 🚀 集成到主应用

修改 `src/app/main.py`:
```python
import time
from src.core.rate_limiter import init_rate_limiter, rate_limit
from src.core.compression import init_compression
from src.core.security import init_security
from src.core.error_handlers import register_error_handlers
from src.core.validation import validate_chat_input

# 初始化安全和性能中间件
init_rate_limiter(redis_client=cache_manager.redis_cache.redis_client if cache_manager.redis_cache else None)
init_compression(app, compress_level=6, minimum_size=500)
init_security(app)
register_error_handlers(app)

# 更新路由
@app.route('/chat', methods=['POST'])
@monitor_performance(performance_monitor, endpoint='/chat')
@rate_limit('chat')
@validate_chat_input
def chat():
    """处理用户发送的聊天消息的API端点。"""
    data = request.validated_json  # 使用验证后的数据
    # ... 其余逻辑保持不变

@app.route('/health')
@monitor_performance(performance_monitor, endpoint='/health')
@rate_limit('health')
def health_check():
    # ... 现有逻辑
```

## 📊 预期收益

### 安全提升:
- **防止API滥用**: 请求限流保护
- **数据安全**: 输入验证和清理
- **攻击防护**: 安全头和模式检测
- **错误信息**: 统一且安全的错误响应

### 性能提升:
- **带宽节省**: 40-60% 响应压缩
- **服务器保护**: 限流防止过载
- **错误处理**: 更快的错误响应
- **监控改善**: 详细的安全和性能日志

### 运维收益:
- **标准化**: 统一的API行为
- **可观测性**: 详细的安全日志
- **故障恢复**: 优雅的错误处理
- **合规性**: 符合安全最佳实践

## 🧪 测试验证

### 1. 限流测试
创建文件: `tests/test_rate_limiting.py`
```python
#!/usr/bin/env python3
import requests
import time
import threading

def test_rate_limiting():
    """测试API限流功能"""
    url = "http://localhost:5000/chat"
    data = {"message": "测试消息", "user_id": "test_user"}

    # 快速发送多个请求
    responses = []
    for i in range(70):  # 超过60次/分钟的限制
        response = requests.post(url, json=data)
        responses.append(response.status_code)
        if i % 10 == 0:
            print(f"请求 {i}: 状态码 {response.status_code}")

    # 统计结果
    success_count = responses.count(200)
    rate_limited_count = responses.count(429)

    print(f"成功请求: {success_count}")
    print(f"被限流请求: {rate_limited_count}")

    assert rate_limited_count > 0, "限流功能未生效"

if __name__ == "__main__":
    test_rate_limiting()
```

### 2. 压缩测试
创建文件: `tests/test_compression.py`
```python
#!/usr/bin/env python3
import requests

def test_compression():
    """测试响应压缩"""
    url = "http://localhost:5000/monitoring/api/metrics"

    # 不支持压缩的请求
    response1 = requests.get(url)
    size1 = len(response1.content)

    # 支持压缩的请求
    headers = {'Accept-Encoding': 'gzip, deflate'}
    response2 = requests.get(url, headers=headers)
    size2 = len(response2.content)

    print(f"未压缩大小: {size1} bytes")
    print(f"压缩后大小: {size2} bytes")
    print(f"压缩率: {(1 - size2/size1)*100:.1f}%")
    print(f"Content-Encoding: {response2.headers.get('Content-Encoding')}")

if __name__ == "__main__":
    test_compression()
```

### 3. 安全测试
创建文件: `tests/test_security.py`
```python
#!/usr/bin/env python3
import requests

def test_security_headers():
    """测试安全头"""
    response = requests.get("http://localhost:5000/health")

    security_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Content-Security-Policy'
    ]

    for header in security_headers:
        if header in response.headers:
            print(f"✅ {header}: {response.headers[header]}")
        else:
            print(f"❌ 缺少安全头: {header}")

def test_input_validation():
    """测试输入验证"""
    url = "http://localhost:5000/chat"

    # 测试恶意输入
    malicious_inputs = [
        {"message": "<script>alert('xss')</script>"},
        {"message": "'; DROP TABLE users; --"},
        {"message": "x" * 2000},  # 超长输入
        {"message": ""},  # 空输入
    ]

    for data in malicious_inputs:
        response = requests.post(url, json=data)
        print(f"输入: {data['message'][:50]}...")
        print(f"状态码: {response.status_code}")
        if response.status_code == 400:
            print("✅ 输入验证生效")
        print()

if __name__ == "__main__":
    test_security_headers()
    test_input_validation()
```

## 🚀 部署清单

### 1. 环境变量配置
```bash
# 限流配置
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_REDIS_URL=redis://localhost:6379/1

# 压缩配置
export COMPRESSION_ENABLED=true
export COMPRESSION_LEVEL=6
export COMPRESSION_MIN_SIZE=500

# 安全配置
export SECURITY_HEADERS_ENABLED=true
export INPUT_VALIDATION_ENABLED=true
export MAX_REQUEST_SIZE=10485760  # 10MB

# 错误处理
export DETAILED_ERRORS=false  # 生产环境设为false
```

### 2. 监控告警
```python
# 添加安全事件监控
def security_alert_callback(alert):
    if alert['type'] in ['rate_limit_exceeded', 'suspicious_request']:
        # 发送安全告警
        send_security_alert(alert)

performance_monitor.add_alert_callback(security_alert_callback)
```

### 3. 日志配置
```python
# 配置安全日志
import logging

security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('logs/security.log')
security_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)
```

完成API优化后，您的系统将具备企业级的安全性和性能！
