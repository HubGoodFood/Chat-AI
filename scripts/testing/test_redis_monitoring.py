#!/usr/bin/env python3
"""
Redis缓存和性能监控测试脚本
验证Redis缓存功能和性能监控系统的正常工作
"""

import time
import sys
import os
import logging
import requests
import json
from typing import Dict, Any

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_redis_cache():
    """测试Redis缓存功能"""
    logger.info("=== 测试Redis缓存功能 ===")
    
    try:
        from src.core.redis_cache import RedisCacheManager
        
        # 初始化Redis缓存管理器
        redis_cache = RedisCacheManager()
        
        # 测试基本缓存操作
        test_key = "test_key"
        test_value = {"message": "Hello Redis!", "timestamp": time.time()}
        
        # 设置缓存
        logger.info("设置缓存...")
        success = redis_cache.set(test_key, test_value, ttl=60)
        logger.info(f"缓存设置结果: {success}")
        
        # 获取缓存
        logger.info("获取缓存...")
        cached_value = redis_cache.get(test_key)
        logger.info(f"缓存获取结果: {cached_value}")
        
        # 验证缓存内容
        if cached_value == test_value:
            logger.info("✅ Redis缓存功能正常")
        else:
            logger.error("❌ Redis缓存内容不匹配")
        
        # 测试缓存存在性
        exists = redis_cache.exists(test_key)
        logger.info(f"缓存存在性检查: {exists}")
        
        # 获取缓存统计
        stats = redis_cache.get_stats()
        logger.info(f"缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        # 健康检查
        health = redis_cache.health_check()
        logger.info(f"健康检查: {json.dumps(health, indent=2, ensure_ascii=False)}")
        
        # 清理测试数据
        redis_cache.delete(test_key)
        logger.info("测试数据已清理")
        
        return True
        
    except ImportError:
        logger.error("Redis库未安装，跳过Redis测试")
        return False
    except Exception as e:
        logger.error(f"Redis缓存测试失败: {e}")
        return False

def test_integrated_cache():
    """测试集成缓存系统"""
    logger.info("=== 测试集成缓存系统 ===")
    
    try:
        from src.core.cache import CacheManager
        
        # 初始化缓存管理器（启用Redis）
        cache_manager = CacheManager(enable_redis=True)
        
        # 测试LLM响应缓存
        test_input = "测试用户输入"
        test_response = "测试AI响应"
        
        logger.info("缓存LLM响应...")
        cache_manager.cache_llm_response(test_input, test_response, ttl_hours=1)
        
        logger.info("获取LLM响应缓存...")
        cached_response = cache_manager.get_llm_cached_response(test_input)
        
        if cached_response == test_response:
            logger.info("✅ 集成缓存系统正常")
        else:
            logger.error("❌ 集成缓存系统异常")
        
        # 获取缓存统计
        stats = cache_manager.get_cache_stats()
        logger.info(f"集成缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        # 健康检查
        health = cache_manager.health_check()
        logger.info(f"集成缓存健康检查: {json.dumps(health, indent=2, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"集成缓存测试失败: {e}")
        return False

def test_performance_monitor():
    """测试性能监控系统"""
    logger.info("=== 测试性能监控系统 ===")
    
    try:
        from src.core.performance_monitor import PerformanceMonitor, monitor_performance
        
        # 初始化性能监控器
        monitor = PerformanceMonitor(enable_detailed_monitoring=True)
        
        # 测试基本监控功能
        logger.info("记录测试请求...")
        monitor.record_request('/test', 'GET')
        monitor.record_response_time('/test', 150.5, 'GET')
        
        logger.info("记录模型性能...")
        monitor.record_model_performance('test_model', 'predict', 25.3, accuracy=0.95)
        
        # 模拟一些错误
        monitor.record_error('/test', 'ValidationError', 'POST')
        
        # 等待一下让监控系统收集数据
        time.sleep(2)
        
        # 获取性能摘要
        summary = monitor.get_performance_summary(time_window_minutes=5)
        logger.info(f"性能摘要: {json.dumps(summary, indent=2, ensure_ascii=False)}")
        
        # 测试装饰器
        @monitor_performance(monitor, endpoint='/test_decorator')
        def test_function():
            time.sleep(0.1)  # 模拟处理时间
            return "测试结果"
        
        logger.info("测试性能监控装饰器...")
        result = test_function()
        logger.info(f"装饰器测试结果: {result}")
        
        # 再次获取摘要查看装饰器效果
        summary_after = monitor.get_performance_summary(time_window_minutes=5)
        logger.info(f"装饰器后性能摘要: {json.dumps(summary_after, indent=2, ensure_ascii=False)}")
        
        logger.info("✅ 性能监控系统正常")
        
        # 停止监控
        monitor.stop_monitoring()
        
        return True
        
    except Exception as e:
        logger.error(f"性能监控测试失败: {e}")
        return False

def test_monitoring_api(base_url="http://localhost:5000"):
    """测试监控API接口"""
    logger.info("=== 测试监控API接口 ===")
    
    try:
        # 测试健康检查
        logger.info("测试健康检查API...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"健康检查响应: {json.dumps(health_data, indent=2, ensure_ascii=False)}")
            logger.info("✅ 健康检查API正常")
        else:
            logger.error(f"❌ 健康检查API异常: {response.status_code}")
        
        # 测试监控指标API
        logger.info("测试监控指标API...")
        response = requests.get(f"{base_url}/monitoring/api/metrics", timeout=10)
        if response.status_code == 200:
            metrics_data = response.json()
            logger.info(f"监控指标响应: {json.dumps(metrics_data, indent=2, ensure_ascii=False)}")
            logger.info("✅ 监控指标API正常")
        else:
            logger.error(f"❌ 监控指标API异常: {response.status_code}")
        
        # 测试缓存统计API
        logger.info("测试缓存统计API...")
        response = requests.get(f"{base_url}/monitoring/api/cache", timeout=10)
        if response.status_code == 200:
            cache_data = response.json()
            logger.info(f"缓存统计响应: {json.dumps(cache_data, indent=2, ensure_ascii=False)}")
            logger.info("✅ 缓存统计API正常")
        else:
            logger.error(f"❌ 缓存统计API异常: {response.status_code}")
        
        # 测试监控健康API
        logger.info("测试监控健康API...")
        response = requests.get(f"{base_url}/monitoring/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"监控健康响应: {json.dumps(health_data, indent=2, ensure_ascii=False)}")
            logger.info("✅ 监控健康API正常")
        else:
            logger.error(f"❌ 监控健康API异常: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ 无法连接到应用服务器，跳过API测试")
        logger.info("请确保应用正在运行: python src/app/main.py")
        return False
    except Exception as e:
        logger.error(f"监控API测试失败: {e}")
        return False

def test_chat_with_monitoring(base_url="http://localhost:5000"):
    """测试聊天功能并验证监控"""
    logger.info("=== 测试聊天功能监控 ===")
    
    try:
        test_messages = [
            "你好",
            "苹果多少钱",
            "有没有香蕉",
            "怎么付款"
        ]
        
        for message in test_messages:
            logger.info(f"发送测试消息: {message}")
            
            response = requests.post(
                f"{base_url}/chat",
                json={"message": message, "user_id": "test_user"},
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                logger.info(f"聊天响应: {chat_response.get('message', 'N/A')[:50]}...")
            else:
                logger.error(f"聊天请求失败: {response.status_code}")
            
            time.sleep(1)  # 避免请求过快
        
        # 等待监控数据更新
        time.sleep(2)
        
        # 检查监控数据是否记录了这些请求
        response = requests.get(f"{base_url}/monitoring/api/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.json()
            chat_endpoint_stats = metrics.get('endpoints', {}).get('POST:/chat', {})
            if chat_endpoint_stats:
                logger.info(f"聊天端点统计: {json.dumps(chat_endpoint_stats, indent=2)}")
                logger.info("✅ 聊天功能监控正常")
            else:
                logger.warning("⚠️ 未找到聊天端点监控数据")
        
        return True
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ 无法连接到应用服务器，跳过聊天测试")
        return False
    except Exception as e:
        logger.error(f"聊天功能监控测试失败: {e}")
        return False

def generate_test_report(results: Dict[str, bool]):
    """生成测试报告"""
    logger.info("=== 测试报告 ===")
    
    print("\n" + "="*60)
    print("Redis缓存和性能监控测试报告")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n建议:")
    if not results.get('redis_cache', False):
        print("  - 安装并启动Redis服务器")
        print("  - 检查Redis连接配置")
    
    if not results.get('monitoring_api', False):
        print("  - 启动Chat AI应用服务器")
        print("  - 检查监控蓝图是否正确注册")
    
    if passed_tests == total_tests:
        print(f"\n🎉 所有测试通过！Redis缓存和性能监控系统工作正常。")
        print(f"访问监控仪表板: http://localhost:5000/monitoring/dashboard")
    else:
        print(f"\n⚠️ 部分测试失败，请检查相关配置。")
    
    print("="*60)

def main():
    """主测试函数"""
    logger.info("开始Redis缓存和性能监控测试...")
    
    results = {}
    
    # 测试Redis缓存
    results['redis_cache'] = test_redis_cache()
    
    # 测试集成缓存
    results['integrated_cache'] = test_integrated_cache()
    
    # 测试性能监控
    results['performance_monitor'] = test_performance_monitor()
    
    # 测试监控API
    results['monitoring_api'] = test_monitoring_api()
    
    # 测试聊天功能监控
    results['chat_monitoring'] = test_chat_with_monitoring()
    
    # 生成测试报告
    generate_test_report(results)

if __name__ == "__main__":
    main()
