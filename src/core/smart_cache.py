#!/usr/bin/env python3
"""
智能缓存管理器：根据查询频率和内容类型动态调整TTL
"""

import time
import hashlib
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SmartCacheManager:
    """
    智能缓存管理器
    
    特性：
    - 动态TTL调整
    - 查询频率统计
    - 智能缓存预热
    - 分层缓存策略
    """
    
    def __init__(self, base_cache_manager):
        """
        初始化智能缓存管理器
        
        Args:
            base_cache_manager: 基础缓存管理器实例
        """
        self.base_cache = base_cache_manager
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 查询统计
        self.query_frequency = defaultdict(int)
        self.last_access = defaultdict(float)
        self.query_categories = {}
        
        # 缓存策略配置
        self.ttl_strategy = {
            'hot_queries': 7 * 24 * 3600,    # 热门查询：7天
            'normal_queries': 24 * 3600,     # 普通查询：1天
            'rare_queries': 6 * 3600,        # 冷门查询：6小时
            'policy_queries': 48 * 3600,     # 政策查询：2天
            'product_queries': 12 * 3600,    # 产品查询：12小时
            'chat_queries': 8 * 3600,        # 聊天查询：8小时
        }
        
        # 预热查询列表
        self.preheat_queries = {
            'policy': [
                "配送时间", "付款方式", "取货地点", "质量保证", 
                "群规", "退款政策", "运费标准", "起送金额",
                "配送范围", "免费配送", "取货时间", "质量问题"
            ],
            'product': [
                "鸡", "蔬菜", "水果", "海鲜", "蛋类",
                "时令水果", "新鲜蔬菜", "禽类", "干货"
            ]
        }
        
        logger.info("智能缓存管理器初始化完成")
    
    def get_cache_key(self, query: str, context: str = None) -> str:
        """生成智能缓存键"""
        # 标准化查询
        normalized_query = self._normalize_query(query)
        
        # 生成基础键
        if context:
            key_material = f"{normalized_query}||{context}"
        else:
            key_material = normalized_query
            
        # 添加查询类型前缀
        query_type = self._classify_query(normalized_query)
        cache_key = f"{query_type}:{hashlib.md5(key_material.encode('utf-8')).hexdigest()}"
        
        return cache_key
    
    def get_dynamic_ttl(self, query: str, query_type: str = None) -> int:
        """根据查询频率和类型动态计算TTL"""
        cache_key = self.get_cache_key(query)
        
        with self._lock:
            frequency = self.query_frequency[cache_key]
        
        # 基于查询类型的基础TTL
        if query_type:
            base_ttl = self.ttl_strategy.get(f"{query_type}_queries", self.ttl_strategy['normal_queries'])
        else:
            base_ttl = self.ttl_strategy['normal_queries']
        
        # 基于频率调整TTL
        if frequency > 100:  # 热门查询
            return max(base_ttl, self.ttl_strategy['hot_queries'])
        elif frequency > 10:  # 普通查询
            return base_ttl
        else:  # 冷门查询
            return min(base_ttl, self.ttl_strategy['rare_queries'])
    
    def get_cached_response(self, query: str, context: str = None, query_type: str = None) -> Optional[Any]:
        """获取缓存响应并更新统计"""
        cache_key = self.get_cache_key(query, context)
        
        # 更新访问统计（线程安全）
        with self._lock:
            self.query_frequency[cache_key] += 1
            self.last_access[cache_key] = time.time()
            
            # 记录查询类型
            if query_type:
                self.query_categories[cache_key] = query_type
        
        # 从缓存获取
        if self.base_cache.redis_cache:
            try:
                cached_response = self.base_cache.redis_cache.get(cache_key, prefix="smart")
                if cached_response:
                    logger.debug(f"智能缓存Redis命中: {query[:30]}...")
                    return cached_response
            except Exception as e:
                logger.error(f"Redis缓存获取失败: {e}")
        
        # 检查内存缓存
        cached_response = self.base_cache.get_cache(cache_key)
        if cached_response:
            logger.debug(f"智能缓存内存命中: {query[:30]}...")
        
        return cached_response
    
    def cache_response(self, query: str, response: Any, context: str = None, query_type: str = None):
        """缓存响应并使用动态TTL"""
        cache_key = self.get_cache_key(query, context)
        ttl_seconds = self.get_dynamic_ttl(query, query_type)

        # 更新查询统计（线程安全）
        with self._lock:
            # 记录查询类型
            if query_type:
                self.query_categories[cache_key] = query_type

            # 更新访问统计
            self.query_frequency[cache_key] += 1
            self.last_access[cache_key] = time.time()

        # 缓存到Redis
        if self.base_cache.redis_cache:
            try:
                self.base_cache.redis_cache.set(
                    cache_key, response,
                    ttl=ttl_seconds,
                    prefix="smart"
                )
                logger.debug(f"智能缓存Redis设置: {query[:30]}..., TTL: {ttl_seconds}s")
            except Exception as e:
                logger.error(f"Redis缓存设置失败: {e}")

        # 缓存到内存
        self.base_cache.set_cache(cache_key, response, ttl_seconds)
        logger.debug(f"智能缓存内存设置: {query[:30]}..., TTL: {ttl_seconds}s")
    
    def invalidate_cache_by_type(self, cache_type: str):
        """按类型清除缓存"""
        if self.base_cache.redis_cache:
            try:
                self.base_cache.redis_cache.clear_prefix(f"smart:{cache_type}")
                logger.info(f"已清除 {cache_type} 类型的Redis缓存")
            except Exception as e:
                logger.error(f"清除Redis缓存失败: {e}")
        
        # 清除内存缓存中的相关条目
        keys_to_remove = [
            key for key in self.base_cache.memory_cache.keys() 
            if key.startswith(f"{cache_type}:")
        ]
        
        for key in keys_to_remove:
            self.base_cache.memory_cache.pop(key, None)
        
        logger.info(f"已清除 {cache_type} 类型的内存缓存，共 {len(keys_to_remove)} 条")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        now = time.time()
        
        with self._lock:
            # 计算热门查询
            hot_queries = [
                (key, freq) for key, freq in self.query_frequency.items() 
                if freq > 10
            ]
            hot_queries.sort(key=lambda x: x[1], reverse=True)
            
            # 计算最近活跃查询
            recent_queries = [
                key for key, last_time in self.last_access.items()
                if now - last_time < 3600  # 最近1小时
            ]
            
            # 按类型统计
            type_stats = defaultdict(int)
            for key, query_type in self.query_categories.items():
                type_stats[query_type] += self.query_frequency[key]
            
            total_queries = len(self.query_frequency)
            total_accesses = sum(self.query_frequency.values())
        
        return {
            'total_queries': total_queries,
            'total_accesses': total_accesses,
            'hot_queries_count': len(hot_queries),
            'recent_queries_count': len(recent_queries),
            'top_hot_queries': hot_queries[:10],
            'query_type_distribution': dict(type_stats),
            'cache_hit_rate': self._calculate_hit_rate()
        }
    
    def _normalize_query(self, query: str) -> str:
        """标准化查询字符串"""
        # 转小写，去除多余空格
        normalized = query.lower().strip()

        # 移除常见的无意义词汇
        stop_words = {'的', '了', '吗', '呢', '啊', '呀', '吧', '是', '多少'}

        # 分词处理（简单按字符分割中文，按空格分割英文）
        words = []
        current_word = ""

        for char in normalized:
            if char.isspace():
                if current_word:
                    words.append(current_word)
                    current_word = ""
            elif char.isalpha() and ord(char) < 128:  # 英文字符
                current_word += char
            else:  # 中文字符或其他
                if current_word:
                    words.append(current_word)
                    current_word = ""
                if char not in stop_words:
                    words.append(char)

        if current_word:
            words.append(current_word)

        # 过滤停用词
        filtered_words = [word for word in words if word not in stop_words and word.strip()]

        return ' '.join(filtered_words) if filtered_words else normalized
    
    def _classify_query(self, query: str) -> str:
        """分类查询类型"""
        policy_keywords = {
            '配送', '送货', '运费', '付款', '支付', '取货', '群规',
            '质量', '退款', '保证', '时间', '地点', '范围', '配'
        }

        product_keywords = {
            '鸡', '蔬菜', '水果', '海鲜', '蛋', '肉', '菜', '果',
            '新鲜', '农场', '有机', '时令'
        }

        query_lower = query.lower()

        # 检查政策关键词（包含任一关键词即可）
        for keyword in policy_keywords:
            if keyword in query_lower:
                return 'policy'

        # 检查产品关键词（包含任一关键词即可）
        for keyword in product_keywords:
            if keyword in query_lower:
                return 'product'

        return 'general'
    
    def _calculate_hit_rate(self) -> float:
        """计算缓存命中率（简化版）"""
        with self._lock:
            total_queries = sum(self.query_frequency.values())
            if total_queries == 0:
                return 0.0
            
            # 假设频率大于1的查询都有缓存命中
            cached_queries = sum(freq - 1 for freq in self.query_frequency.values() if freq > 1)
        
        return cached_queries / total_queries if total_queries > 0 else 0.0

    def preheat_cache(self, cache_type: str = 'all'):
        """预热缓存"""
        logger.info(f"开始预热缓存: {cache_type}")

        if cache_type in ['all', 'policy']:
            self._preheat_policy_cache()

        if cache_type in ['all', 'product']:
            self._preheat_product_cache()

        logger.info("缓存预热完成")

    def _preheat_policy_cache(self):
        """预热政策查询缓存"""
        try:
            # 动态导入避免循环依赖
            from src.app.policy.lightweight_manager import LightweightPolicyManager
            policy_manager = LightweightPolicyManager()

            for query in self.preheat_queries['policy']:
                try:
                    results = policy_manager.search_policy(query, top_k=3)
                    if results:
                        self.cache_response(query, results, query_type='policy')
                        logger.debug(f"预热政策查询: {query}")
                except Exception as e:
                    logger.warning(f"预热政策查询失败 {query}: {e}")

        except Exception as e:
            logger.error(f"政策缓存预热失败: {e}")

    def _preheat_product_cache(self):
        """预热产品查询缓存"""
        try:
            # 动态导入避免循环依赖
            from src.app.products.manager import ProductManager
            product_manager = ProductManager()

            for query in self.preheat_queries['product']:
                try:
                    # 模拟产品查询
                    results = product_manager.fuzzy_match_product(query, threshold=0.3)
                    if results:
                        self.cache_response(query, results, query_type='product')
                        logger.debug(f"预热产品查询: {query}")
                except Exception as e:
                    logger.warning(f"预热产品查询失败 {query}: {e}")

        except Exception as e:
            logger.error(f"产品缓存预热失败: {e}")


class CacheMaintenanceScheduler:
    """缓存维护调度器"""

    def __init__(self, smart_cache):
        """
        初始化缓存维护调度器

        Args:
            smart_cache: SmartCacheManager实例
        """
        self.smart_cache = smart_cache
        self.is_running = False
        self.maintenance_thread = None

        logger.info("缓存维护调度器初始化完成")

    def start_maintenance(self):
        """启动定期维护"""
        if not self.is_running:
            self.is_running = True
            self.maintenance_thread = threading.Thread(
                target=self._maintenance_loop,
                daemon=True
            )
            self.maintenance_thread.start()
            logger.info("缓存维护调度器已启动")

    def stop_maintenance(self):
        """停止定期维护"""
        self.is_running = False
        if self.maintenance_thread and self.maintenance_thread.is_alive():
            logger.info("正在停止缓存维护调度器...")

    def _maintenance_loop(self):
        """维护循环"""
        while self.is_running:
            try:
                # 每小时执行一次维护
                time.sleep(3600)

                if not self.is_running:
                    break

                # 清理过期统计数据
                self._cleanup_old_statistics()

                # 重新预热热门查询
                self._refresh_hot_cache()

                # 生成统计报告
                self._generate_cache_report()

            except Exception as e:
                logger.error(f"缓存维护失败: {e}")
                time.sleep(300)  # 错误时等待5分钟

    def _cleanup_old_statistics(self):
        """清理过期的统计数据"""
        cutoff_time = time.time() - 7 * 24 * 3600  # 7天前

        with self.smart_cache._lock:
            old_keys = [
                key for key, last_time in self.smart_cache.last_access.items()
                if last_time < cutoff_time
            ]

            for key in old_keys:
                self.smart_cache.query_frequency.pop(key, None)
                self.smart_cache.last_access.pop(key, None)
                self.smart_cache.query_categories.pop(key, None)

        if old_keys:
            logger.info(f"清理了 {len(old_keys)} 条过期统计数据")

    def _refresh_hot_cache(self):
        """刷新热门查询缓存"""
        with self.smart_cache._lock:
            # 获取热门查询
            hot_queries = [
                key for key, freq in self.smart_cache.query_frequency.items()
                if freq > 50  # 访问超过50次的查询
            ]

        # 重新缓存热门查询（这里可以根据需要实现具体的刷新逻辑）
        logger.info(f"识别到 {len(hot_queries)} 个热门查询")

    def _generate_cache_report(self):
        """生成缓存统计报告"""
        stats = self.smart_cache.get_cache_statistics()

        logger.info("=== 智能缓存统计报告 ===")
        logger.info(f"总查询数: {stats['total_queries']}")
        logger.info(f"总访问次数: {stats['total_accesses']}")
        logger.info(f"热门查询数: {stats['hot_queries_count']}")
        logger.info(f"缓存命中率: {stats['cache_hit_rate']:.2%}")
        logger.info(f"查询类型分布: {stats['query_type_distribution']}")


def initialize_smart_cache(app, cache_manager):
    """在应用启动时初始化智能缓存"""

    smart_cache = SmartCacheManager(cache_manager)

    # 注册到应用上下文
    app.smart_cache = smart_cache

    # 启动缓存维护调度器
    cache_scheduler = CacheMaintenanceScheduler(smart_cache)
    cache_scheduler.start_maintenance()
    app.cache_scheduler = cache_scheduler

    # 启动后台预热任务
    def preheat_task():
        time.sleep(5)  # 等待应用完全启动
        try:
            smart_cache.preheat_cache('all')
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")

    preheat_thread = threading.Thread(target=preheat_task, daemon=True)
    preheat_thread.start()

    logger.info("智能缓存系统已初始化")

    return smart_cache
