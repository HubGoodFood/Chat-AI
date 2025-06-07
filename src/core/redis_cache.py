#!/usr/bin/env python3
"""
Redis缓存管理器
提供高性能的分布式缓存功能，支持集群部署和数据持久化
"""

import json
import time
import hashlib
import logging
import os
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """
    Redis缓存管理器
    
    功能特性：
    - 分布式缓存支持
    - 自动过期管理
    - 数据序列化/反序列化
    - 连接池管理
    - 故障转移到本地缓存
    - 缓存统计和监控
    """
    
    def __init__(self, redis_url: str = None, fallback_to_memory: bool = True):
        """
        初始化Redis缓存管理器
        
        Args:
            redis_url: Redis连接URL
            fallback_to_memory: 是否在Redis不可用时回退到内存缓存
        """
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.fallback_to_memory = fallback_to_memory
        self.redis_client = None
        self.memory_cache = {}  # 备用内存缓存
        self.connection_pool = None
        self.is_redis_available = False
        
        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'redis_hits': 0,
            'memory_hits': 0
        }
        
        # 初始化Redis连接
        self._init_redis_connection()
    
    def _init_redis_connection(self):
        """初始化Redis连接"""
        try:
            import redis
            from redis.connection import ConnectionPool
            
            # 创建连接池
            self.connection_pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            
            # 创建Redis客户端
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True
            )
            
            # 测试连接
            self.redis_client.ping()
            self.is_redis_available = True
            logger.info(f"Redis缓存已连接: {self.redis_url}")
            
        except ImportError:
            logger.warning("Redis库未安装，将使用内存缓存")
            self.is_redis_available = False
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.is_redis_available = False
            if not self.fallback_to_memory:
                raise
    
    def _generate_key(self, key: str, prefix: str = "chatai") -> str:
        """生成缓存键"""
        return f"{prefix}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值"""
        try:
            return json.dumps({
                'data': value,
                'timestamp': time.time(),
                'type': type(value).__name__
            }, ensure_ascii=False)
        except Exception as e:
            logger.error(f"序列化失败: {e}")
            return json.dumps({'data': str(value), 'timestamp': time.time(), 'type': 'str'})
    
    def _deserialize_value(self, serialized: str) -> Any:
        """反序列化值"""
        try:
            data = json.loads(serialized)
            return data.get('data')
        except Exception as e:
            logger.error(f"反序列化失败: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600, prefix: str = "chatai") -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            prefix: 键前缀
            
        Returns:
            bool: 是否设置成功
        """
        cache_key = self._generate_key(key, prefix)
        serialized_value = self._serialize_value(value)
        
        self.stats['sets'] += 1
        
        # 优先使用Redis
        if self.is_redis_available and self.redis_client:
            try:
                result = self.redis_client.setex(cache_key, ttl, serialized_value)
                if result:
                    logger.debug(f"Redis缓存设置成功: {cache_key}")
                    return True
            except Exception as e:
                logger.error(f"Redis设置失败: {e}")
                self.stats['errors'] += 1
                self._handle_redis_error()
        
        # 回退到内存缓存
        if self.fallback_to_memory:
            expiry_time = time.time() + ttl
            self.memory_cache[cache_key] = {
                'value': serialized_value,
                'expiry': expiry_time
            }
            logger.debug(f"内存缓存设置成功: {cache_key}")
            return True
        
        return False
    
    def get(self, key: str, prefix: str = "chatai") -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            缓存值或None
        """
        cache_key = self._generate_key(key, prefix)
        
        # 优先从Redis获取
        if self.is_redis_available and self.redis_client:
            try:
                serialized_value = self.redis_client.get(cache_key)
                if serialized_value:
                    self.stats['hits'] += 1
                    self.stats['redis_hits'] += 1
                    value = self._deserialize_value(serialized_value)
                    logger.debug(f"Redis缓存命中: {cache_key}")
                    return value
            except Exception as e:
                logger.error(f"Redis获取失败: {e}")
                self.stats['errors'] += 1
                self._handle_redis_error()
        
        # 从内存缓存获取
        if self.fallback_to_memory and cache_key in self.memory_cache:
            cache_entry = self.memory_cache[cache_key]
            if time.time() < cache_entry['expiry']:
                self.stats['hits'] += 1
                self.stats['memory_hits'] += 1
                value = self._deserialize_value(cache_entry['value'])
                logger.debug(f"内存缓存命中: {cache_key}")
                return value
            else:
                # 过期，删除
                del self.memory_cache[cache_key]
        
        self.stats['misses'] += 1
        return None
    
    def delete(self, key: str, prefix: str = "chatai") -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            bool: 是否删除成功
        """
        cache_key = self._generate_key(key, prefix)
        self.stats['deletes'] += 1
        
        success = False
        
        # 从Redis删除
        if self.is_redis_available and self.redis_client:
            try:
                result = self.redis_client.delete(cache_key)
                if result:
                    success = True
                    logger.debug(f"Redis缓存删除成功: {cache_key}")
            except Exception as e:
                logger.error(f"Redis删除失败: {e}")
                self.stats['errors'] += 1
        
        # 从内存缓存删除
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
            success = True
            logger.debug(f"内存缓存删除成功: {cache_key}")
        
        return success
    
    def exists(self, key: str, prefix: str = "chatai") -> bool:
        """检查缓存键是否存在"""
        cache_key = self._generate_key(key, prefix)
        
        # 检查Redis
        if self.is_redis_available and self.redis_client:
            try:
                return bool(self.redis_client.exists(cache_key))
            except Exception as e:
                logger.error(f"Redis检查存在失败: {e}")
        
        # 检查内存缓存
        if cache_key in self.memory_cache:
            cache_entry = self.memory_cache[cache_key]
            return time.time() < cache_entry['expiry']
        
        return False
    
    def clear_prefix(self, prefix: str = "chatai") -> int:
        """清除指定前缀的所有缓存"""
        cleared_count = 0
        
        # 清除Redis中的键
        if self.is_redis_available and self.redis_client:
            try:
                pattern = f"{prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    cleared_count += self.redis_client.delete(*keys)
                    logger.info(f"Redis清除了 {len(keys)} 个键")
            except Exception as e:
                logger.error(f"Redis清除失败: {e}")
        
        # 清除内存缓存中的键
        memory_keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"{prefix}:")]
        for key in memory_keys_to_delete:
            del self.memory_cache[key]
            cleared_count += 1
        
        if memory_keys_to_delete:
            logger.info(f"内存缓存清除了 {len(memory_keys_to_delete)} 个键")
        
        return cleared_count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = self.stats.copy()
        stats.update({
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'redis_available': self.is_redis_available,
            'memory_cache_size': len(self.memory_cache)
        })
        
        # 获取Redis信息
        if self.is_redis_available and self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats['redis_memory_usage'] = redis_info.get('used_memory_human', 'N/A')
                stats['redis_connected_clients'] = redis_info.get('connected_clients', 0)
            except Exception:
                pass
        
        return stats
    
    def _handle_redis_error(self):
        """处理Redis错误"""
        # 可以在这里实现重连逻辑
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            'redis_available': False,
            'memory_cache_available': True,
            'total_errors': self.stats['errors'],
            'last_check': datetime.now().isoformat()
        }
        
        # 检查Redis连接
        if self.redis_client:
            try:
                self.redis_client.ping()
                health['redis_available'] = True
            except Exception as e:
                health['redis_error'] = str(e)
        
        return health
    
    def cleanup_expired(self):
        """清理过期的内存缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if current_time > entry['expiry']
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期的内存缓存项")
        
        return len(expired_keys)
