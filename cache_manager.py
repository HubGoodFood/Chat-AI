import os
import time
import json
import hashlib
import logging
from functools import wraps
from datetime import datetime, timedelta

# 配置日志
logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器，提供多种缓存机制"""
    
    def __init__(self, cache_dir="cache"):
        """初始化缓存管理器
        
        Args:
            cache_dir (str): 缓存文件存储目录
        """
        self.cache_dir = cache_dir
        self.memory_cache = {}
        self.ensure_cache_dir()
        self.product_cache_file = os.path.join(cache_dir, "product_cache.json")
        self.llm_cache_file = os.path.join(cache_dir, "llm_responses.json")
        self.session_cache = {}  # 内存中的会话缓存 {user_id: {context_data}}
        self.ttl_cache = {}  # 带过期时间的缓存 {key: (value, expiry_time)}
        
    def ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                logger.info(f"创建缓存目录: {self.cache_dir}")
            except Exception as e:
                logger.error(f"创建缓存目录失败: {e}")
    
    # ----- 产品数据缓存 ----- #
    
    def cache_product_data(self, product_catalog, product_categories, seasonal_products):
        """缓存产品数据到文件
        
        Args:
            product_catalog (dict): 产品目录
            product_categories (dict): 产品分类
            seasonal_products (list): 当季产品列表
        """
        try:
            cache_data = {
                "timestamp": time.time(),
                "product_catalog": product_catalog,
                "product_categories": product_categories,
                "seasonal_products": seasonal_products
            }
            with open(self.product_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"产品数据已缓存至: {self.product_cache_file}")
        except Exception as e:
            logger.error(f"缓存产品数据失败: {e}")
    
    def get_cached_product_data(self, max_age_hours=24):
        """从缓存加载产品数据
        
        Args:
            max_age_hours (int): 缓存最大有效期（小时）
            
        Returns:
            tuple: (product_catalog, product_categories, seasonal_products) 或 
                   None（如果缓存不存在或已过期）
        """
        if not os.path.exists(self.product_cache_file):
            return None
        
        try:
            with open(self.product_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查缓存是否过期
            cache_age_hours = (time.time() - cache_data["timestamp"]) / 3600
            if cache_age_hours > max_age_hours:
                logger.info(f"产品数据缓存已过期 ({cache_age_hours:.1f} 小时)")
                return None
                
            logger.info(f"从缓存加载产品数据 (缓存年龄: {cache_age_hours:.1f} 小时)")
            return (
                cache_data["product_catalog"],
                cache_data["product_categories"],
                cache_data["seasonal_products"]
            )
        except Exception as e:
            logger.error(f"加载产品数据缓存失败: {e}")
            return None
    
    # ----- 会话缓存 ----- #
    
    def set_user_session(self, user_id, context_data, ttl_minutes=60):
        """设置用户会话上下文
        
        Args:
            user_id (str): 用户ID
            context_data (dict): 上下文数据
            ttl_minutes (int): 会话过期时间（分钟）
        """
        expiry = datetime.now() + timedelta(minutes=ttl_minutes)
        self.session_cache[user_id] = {
            "data": context_data,
            "expiry": expiry
        }
        logger.debug(f"用户会话已缓存: {user_id}")
    
    def get_user_session(self, user_id):
        """获取用户会话上下文
        
        Args:
            user_id (str): 用户ID
            
        Returns:
            dict: 会话上下文数据，如果不存在或已过期则返回None
        """
        if user_id not in self.session_cache:
            return None
        
        session = self.session_cache[user_id]
        if datetime.now() > session["expiry"]:
            # 会话已过期
            logger.debug(f"用户会话已过期: {user_id}")
            del self.session_cache[user_id]
            return None
        
        return session["data"]
    
    def update_user_session(self, user_id, update_dict, ttl_minutes=60):
        """更新用户会话数据
        
        Args:
            user_id (str): 用户ID
            update_dict (dict): 要更新的键值对
            ttl_minutes (int): 新的会话过期时间（分钟）
        """
        existing = self.get_user_session(user_id) or {}
        existing.update(update_dict)
        self.set_user_session(user_id, existing, ttl_minutes)
    
    # ----- LLM响应缓存 ----- #
    
    def _generate_cache_key(self, user_input, context=None):
        """为用户输入生成缓存键
        
        Args:
            user_input (str): 用户输入
            context (str, optional): 上下文信息
            
        Returns:
            str: 缓存键
        """
        # 简单规范化输入以提高缓存命中率
        normalized_input = user_input.lower().strip()
        
        if context:
            key_material = f"{normalized_input}||{context}"
        else:
            key_material = normalized_input
            
        return hashlib.md5(key_material.encode('utf-8')).hexdigest()
    
    def get_llm_cached_response(self, user_input, context=None):
        """获取缓存的LLM响应
        
        Args:
            user_input (str): 用户输入
            context (str, optional): 上下文信息
            
        Returns:
            str: 缓存的响应，如果未命中缓存则返回None
        """
        cache_key = self._generate_cache_key(user_input, context)
        
        # 先检查内存缓存
        cache_entry = self.ttl_cache.get(cache_key)
        if cache_entry:
            value, expiry = cache_entry
            if time.time() < expiry:
                logger.debug(f"LLM响应内存缓存命中: {user_input[:30]}...")
                return value
            else:
                # 过期，从内存缓存中移除
                self.ttl_cache.pop(cache_key, None)
        
        # 检查文件缓存
        if not os.path.exists(self.llm_cache_file):
            return None
            
        try:
            with open(self.llm_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            entry = cache_data.get(cache_key)
            if not entry or time.time() > entry.get("expiry", 0):
                return None
                
            # 更新内存缓存
            self.ttl_cache[cache_key] = (entry["response"], entry["expiry"])
            logger.debug(f"LLM响应文件缓存命中: {user_input[:30]}...")
            return entry["response"]
        except Exception as e:
            logger.error(f"读取LLM响应缓存失败: {e}")
            return None
    
    def cache_llm_response(self, user_input, response, context=None, ttl_hours=24):
        """缓存LLM响应
        
        Args:
            user_input (str): 用户输入
            response (str): LLM响应
            context (str, optional): 上下文信息
            ttl_hours (int): 缓存过期时间（小时）
        """
        cache_key = self._generate_cache_key(user_input, context)
        expiry = time.time() + ttl_hours * 3600
        
        # 更新内存缓存
        self.ttl_cache[cache_key] = (response, expiry)
        
        # 更新文件缓存
        try:
            if os.path.exists(self.llm_cache_file):
                with open(self.llm_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            else:
                cache_data = {}
                
            cache_data[cache_key] = {
                "response": response,
                "expiry": expiry,
                "user_input": user_input,
                "timestamp": time.time()
            }
            
            with open(self.llm_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"LLM响应已缓存: {user_input[:30]}...")
        except Exception as e:
            logger.error(f"缓存LLM响应失败: {e}")
    
    # ----- 通用内存缓存 ----- #
    
    def set_cache(self, key, value, ttl_seconds=3600):
        """设置缓存值
        
        Args:
            key (str): 缓存键
            value: 缓存值
            ttl_seconds (int): 过期时间（秒）
        """
        self.memory_cache[key] = (value, time.time() + ttl_seconds)
    
    def get_cache(self, key):
        """获取缓存值
        
        Args:
            key (str): 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if key not in self.memory_cache:
            return None
            
        value, expiry = self.memory_cache[key]
        if time.time() > expiry:
            del self.memory_cache[key]
            return None
            
        return value
    
    def clear_cache(self, key=None):
        """清除缓存
        
        Args:
            key (str, optional): 要清除的特定缓存键，如果不指定则清除所有缓存
        """
        if key:
            if key in self.memory_cache:
                del self.memory_cache[key]
                logger.debug(f"已清除缓存: {key}")
        else:
            self.memory_cache.clear()
            self.ttl_cache.clear()
            logger.info("已清除所有内存缓存")
            
    def clear_expired_entries(self):
        """清除所有过期的缓存条目"""
        now = time.time()
        # 清理内存缓存
        expired_keys = [k for k, (_, exp) in self.memory_cache.items() if now > exp]
        for key in expired_keys:
            del self.memory_cache[key]
            
        # 清理TTL缓存
        expired_keys = [k for k, (_, exp) in self.ttl_cache.items() if now > exp]
        for key in expired_keys:
            del self.ttl_cache[key]
            
        # 清理会话缓存
        current_time = datetime.now()
        expired_sessions = [uid for uid, session in self.session_cache.items() 
                         if current_time > session["expiry"]]
        for uid in expired_sessions:
            del self.session_cache[uid]
            
        if expired_keys or expired_sessions:
            logger.debug(f"已清除 {len(expired_keys) + len(expired_sessions)} 个过期缓存条目")


# 装饰器：函数结果缓存
def cached(ttl_seconds=3600, cache_key_func=None):
    """缓存函数结果的装饰器
    
    Args:
        ttl_seconds (int): 缓存过期时间（秒）
        cache_key_func (callable, optional): 自定义缓存键生成函数，
                                            接收与被装饰函数相同的参数
    
    Returns:
        callable: 装饰器函数
    """
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if cache_key_func:
                key = cache_key_func(*args, **kwargs)
            else:
                # 默认键生成
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                key = func.__name__ + "_" + "_".join(key_parts)
                
            # 尝试从缓存获取结果
            current_time = time.time()
            if key in cache:
                result, expiry = cache[key]
                if current_time < expiry:
                    return result
                    
            # 缓存未命中，执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache[key] = (result, current_time + ttl_seconds)
            
            # 清理过期缓存
            expired_keys = [k for k, (_, exp) in cache.items() if current_time > exp]
            for exp_key in expired_keys:
                del cache[exp_key]
                
            return result
        return wrapper
    return decorator 