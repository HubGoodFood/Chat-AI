#!/usr/bin/env python3
"""
HTTP缓存头配置
优化静态资源的浏览器缓存策略
"""

from flask import make_response
from datetime import datetime, timedelta

def add_cache_headers(response, cache_type='static'):
    """添加缓存头"""
    if cache_type == 'static':
        # 静态资源缓存1年
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        response.headers['Expires'] = (datetime.now() + timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT')
        # 添加ETag支持
        response.headers['ETag'] = f'"{hash(response.data)}"'
    elif cache_type == 'api':
        # API响应缓存5分钟
        response.headers['Cache-Control'] = 'public, max-age=300'
    elif cache_type == 'no-cache':
        # 不缓存
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    elif cache_type == 'short':
        # 短期缓存（1小时）
        response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response

def cache_control(cache_type='static'):
    """装饰器：为路由添加缓存控制"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            return add_cache_headers(response, cache_type)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def get_content_type(filename):
    """获取文件MIME类型"""
    content_types = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject'
    }
    
    # 获取文件扩展名
    ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    return content_types.get(ext, 'application/octet-stream')
