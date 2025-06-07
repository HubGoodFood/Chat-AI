#!/usr/bin/env python3
"""
性能监控系统
实时监控应用性能指标，提供详细的性能分析和告警功能
"""

import time
import psutil
import threading
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from functools import wraps
import gc

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    性能监控器
    
    功能特性：
    - 实时性能指标收集
    - 内存使用监控
    - API响应时间统计
    - 错误率监控
    - 自动告警
    - 性能报告生成
    """
    
    def __init__(self, enable_detailed_monitoring: bool = True):
        """
        初始化性能监控器
        
        Args:
            enable_detailed_monitoring: 是否启用详细监控
        """
        self.enable_detailed_monitoring = enable_detailed_monitoring
        self.start_time = time.time()
        
        # 性能指标存储
        self.metrics = {
            'requests': defaultdict(int),
            'response_times': defaultdict(list),
            'errors': defaultdict(int),
            'memory_usage': deque(maxlen=100),
            'cpu_usage': deque(maxlen=100),
            'cache_stats': deque(maxlen=100),
            'model_performance': defaultdict(list)
        }
        
        # 告警配置
        self.alert_thresholds = {
            'response_time_ms': 2000,  # 2秒
            'error_rate_percent': 5,   # 5%
            'memory_usage_percent': 80, # 80%
            'cpu_usage_percent': 80    # 80%
        }
        
        # 告警回调
        self.alert_callbacks = []
        
        # 监控线程
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # 性能统计
        self.stats_lock = threading.Lock()
        
        # 启动监控
        if enable_detailed_monitoring:
            self.start_monitoring()
    
    def start_monitoring(self):
        """启动后台监控线程"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("性能监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                self._collect_system_metrics()
                
                # 检查告警条件
                self._check_alerts()
                
                # 清理过期数据
                self._cleanup_old_data()
                
                time.sleep(10)  # 每10秒收集一次
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                time.sleep(30)  # 错误时等待更长时间
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 当前进程信息
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            timestamp = time.time()
            
            with self.stats_lock:
                self.metrics['cpu_usage'].append({
                    'timestamp': timestamp,
                    'value': cpu_percent
                })
                
                self.metrics['memory_usage'].append({
                    'timestamp': timestamp,
                    'system_percent': memory_percent,
                    'process_mb': process_memory
                })
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def record_request(self, endpoint: str, method: str = "GET"):
        """记录请求"""
        key = f"{method}:{endpoint}"
        with self.stats_lock:
            self.metrics['requests'][key] += 1
    
    def record_response_time(self, endpoint: str, response_time_ms: float, method: str = "GET"):
        """记录响应时间"""
        key = f"{method}:{endpoint}"
        with self.stats_lock:
            self.metrics['response_times'][key].append({
                'timestamp': time.time(),
                'value': response_time_ms
            })
            
            # 只保留最近1000条记录
            if len(self.metrics['response_times'][key]) > 1000:
                self.metrics['response_times'][key] = self.metrics['response_times'][key][-1000:]
    
    def record_error(self, endpoint: str, error_type: str = "unknown", method: str = "GET"):
        """记录错误"""
        key = f"{method}:{endpoint}:{error_type}"
        with self.stats_lock:
            self.metrics['errors'][key] += 1
    
    def record_model_performance(self, model_name: str, operation: str, duration_ms: float, **kwargs):
        """记录模型性能"""
        key = f"{model_name}:{operation}"
        with self.stats_lock:
            self.metrics['model_performance'][key].append({
                'timestamp': time.time(),
                'duration_ms': duration_ms,
                'metadata': kwargs
            })
            
            # 只保留最近500条记录
            if len(self.metrics['model_performance'][key]) > 500:
                self.metrics['model_performance'][key] = self.metrics['model_performance'][key][-500:]
    
    def record_cache_stats(self, cache_stats: Dict[str, Any]):
        """记录缓存统计"""
        with self.stats_lock:
            self.metrics['cache_stats'].append({
                'timestamp': time.time(),
                **cache_stats
            })
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            cutoff_time = time.time() - (time_window_minutes * 60)
        except (TypeError, ValueError):
            cutoff_time = time.time() - 3600  # 默认1小时
        
        with self.stats_lock:
            summary = {
                'time_window_minutes': time_window_minutes,
                'uptime_seconds': time.time() - self.start_time,
                'total_requests': sum(self.metrics['requests'].values()),
                'endpoints': {},
                'system': {},
                'models': {},
                'cache': {},
                'alerts': []
            }
            
            # 端点统计
            for endpoint_key, count in self.metrics['requests'].items():
                if endpoint_key in self.metrics['response_times']:
                    recent_times = [
                        rt['value'] for rt in self.metrics['response_times'][endpoint_key]
                        if rt['timestamp'] > cutoff_time
                    ]
                    
                    if recent_times:
                        summary['endpoints'][endpoint_key] = {
                            'total_requests': count,
                            'recent_requests': len(recent_times),
                            'avg_response_time_ms': sum(recent_times) / len(recent_times),
                            'max_response_time_ms': max(recent_times),
                            'min_response_time_ms': min(recent_times)
                        }
            
            # 系统统计
            recent_cpu = [m['value'] for m in self.metrics['cpu_usage'] if m['timestamp'] > cutoff_time]
            recent_memory = [m for m in self.metrics['memory_usage'] if m['timestamp'] > cutoff_time]
            
            if recent_cpu:
                summary['system']['avg_cpu_percent'] = sum(recent_cpu) / len(recent_cpu)
                summary['system']['max_cpu_percent'] = max(recent_cpu)
            
            if recent_memory:
                avg_memory = sum(m['system_percent'] for m in recent_memory) / len(recent_memory)
                avg_process_memory = sum(m['process_mb'] for m in recent_memory) / len(recent_memory)
                summary['system']['avg_memory_percent'] = avg_memory
                summary['system']['avg_process_memory_mb'] = avg_process_memory
            
            # 模型性能统计
            for model_key, performances in self.metrics['model_performance'].items():
                recent_performances = [p for p in performances if p['timestamp'] > cutoff_time]
                if recent_performances:
                    durations = [p['duration_ms'] for p in recent_performances]
                    summary['models'][model_key] = {
                        'total_calls': len(recent_performances),
                        'avg_duration_ms': sum(durations) / len(durations),
                        'max_duration_ms': max(durations),
                        'min_duration_ms': min(durations)
                    }
            
            # 缓存统计
            recent_cache = [c for c in self.metrics['cache_stats'] if c['timestamp'] > cutoff_time]
            if recent_cache:
                latest_cache = recent_cache[-1]
                summary['cache'] = {k: v for k, v in latest_cache.items() if k != 'timestamp'}
            
            return summary
    
    def _check_alerts(self):
        """检查告警条件"""
        try:
            alerts = []
            
            # 检查响应时间
            for endpoint_key, times in self.metrics['response_times'].items():
                if times:
                    recent_times = [t['value'] for t in times[-10:]]  # 最近10次请求
                    avg_time = sum(recent_times) / len(recent_times)
                    if avg_time > self.alert_thresholds['response_time_ms']:
                        alerts.append({
                            'type': 'high_response_time',
                            'endpoint': endpoint_key,
                            'value': avg_time,
                            'threshold': self.alert_thresholds['response_time_ms']
                        })
            
            # 检查内存使用
            if self.metrics['memory_usage']:
                latest_memory = self.metrics['memory_usage'][-1]
                if latest_memory['system_percent'] > self.alert_thresholds['memory_usage_percent']:
                    alerts.append({
                        'type': 'high_memory_usage',
                        'value': latest_memory['system_percent'],
                        'threshold': self.alert_thresholds['memory_usage_percent']
                    })
            
            # 检查CPU使用
            if self.metrics['cpu_usage']:
                latest_cpu = self.metrics['cpu_usage'][-1]
                if latest_cpu['value'] > self.alert_thresholds['cpu_usage_percent']:
                    alerts.append({
                        'type': 'high_cpu_usage',
                        'value': latest_cpu['value'],
                        'threshold': self.alert_thresholds['cpu_usage_percent']
                    })
            
            # 触发告警回调
            for alert in alerts:
                self._trigger_alert(alert)
                
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
    
    def _trigger_alert(self, alert: Dict[str, Any]):
        """触发告警"""
        logger.warning(f"性能告警: {alert}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff_time = time.time() - 3600  # 保留1小时数据
        
        with self.stats_lock:
            # 清理响应时间数据
            for endpoint_key in self.metrics['response_times']:
                self.metrics['response_times'][endpoint_key] = [
                    rt for rt in self.metrics['response_times'][endpoint_key]
                    if rt['timestamp'] > cutoff_time
                ]
            
            # 清理模型性能数据
            for model_key in self.metrics['model_performance']:
                self.metrics['model_performance'][model_key] = [
                    mp for mp in self.metrics['model_performance'][model_key]
                    if mp['timestamp'] > cutoff_time
                ]
    
    def export_metrics(self, filepath: str):
        """导出指标到文件"""
        try:
            with self.stats_lock:
                metrics_data = {
                    'export_time': datetime.now().isoformat(),
                    'uptime_seconds': time.time() - self.start_time,
                    'metrics': {
                        'requests': dict(self.metrics['requests']),
                        'response_times': {k: list(v) for k, v in self.metrics['response_times'].items()},
                        'errors': dict(self.metrics['errors']),
                        'memory_usage': list(self.metrics['memory_usage']),
                        'cpu_usage': list(self.metrics['cpu_usage']),
                        'cache_stats': list(self.metrics['cache_stats']),
                        'model_performance': {k: list(v) for k, v in self.metrics['model_performance'].items()}
                    }
                }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"性能指标已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"导出指标失败: {e}")


def monitor_performance(monitor: PerformanceMonitor, endpoint: str = None, model_name: str = None):
    """
    性能监控装饰器
    
    Args:
        monitor: 性能监控器实例
        endpoint: API端点名称
        model_name: 模型名称
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # 记录请求
                if endpoint:
                    monitor.record_request(endpoint)
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录成功的响应时间
                duration_ms = (time.time() - start_time) * 1000
                
                if endpoint:
                    monitor.record_response_time(endpoint, duration_ms)
                
                if model_name:
                    monitor.record_model_performance(model_name, func.__name__, duration_ms)
                
                return result
                
            except Exception as e:
                # 记录错误
                duration_ms = (time.time() - start_time) * 1000
                
                if endpoint:
                    monitor.record_error(endpoint, type(e).__name__)
                    monitor.record_response_time(endpoint, duration_ms)
                
                if model_name:
                    monitor.record_model_performance(
                        model_name, func.__name__, duration_ms, 
                        error=type(e).__name__
                    )
                
                raise
        
        return wrapper
    return decorator


# 全局监控器实例
global_monitor = None

def get_global_monitor() -> Optional[PerformanceMonitor]:
    """获取全局监控器实例"""
    return global_monitor

def init_global_monitor(enable_detailed_monitoring: bool = True) -> PerformanceMonitor:
    """初始化全局监控器"""
    global global_monitor
    if global_monitor is None:
        global_monitor = PerformanceMonitor(enable_detailed_monitoring)
    return global_monitor
