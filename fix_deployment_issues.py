#!/usr/bin/env python3
"""
修复部署问题的快速脚本
解决Redis连接和LLM客户端配置问题
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """检查环境配置"""
    logger.info("检查环境配置...")
    
    issues = []
    
    # 检查Redis配置
    redis_enabled = os.environ.get('REDIS_ENABLED', 'false').lower()
    if redis_enabled == 'true':
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            issues.append("REDIS_ENABLED=true但未设置REDIS_URL")
        logger.info(f"Redis配置: ENABLED={redis_enabled}, URL={redis_url}")
    else:
        logger.info("Redis已禁用，将使用内存缓存")
    
    # 检查LLM配置
    deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    if deepseek_key:
        logger.info("DEEPSEEK_API_KEY已设置")
    else:
        logger.warning("DEEPSEEK_API_KEY未设置，LLM功能将不可用")
    
    # 检查模型类型
    model_type = os.environ.get('MODEL_TYPE', 'full')
    logger.info(f"模型类型: {model_type}")
    
    return issues

def test_imports():
    """测试关键模块导入"""
    logger.info("测试关键模块导入...")
    
    try:
        # 测试OpenAI导入
        from openai import OpenAI
        logger.info("✓ OpenAI库导入成功")
        
        # 测试配置导入
        from src.config import settings as config
        logger.info("✓ 配置模块导入成功")
        
        # 测试LLM客户端
        if config.llm_client:
            logger.info("✓ LLM客户端已初始化")
        else:
            logger.warning("! LLM客户端未初始化")
        
        # 测试缓存管理器
        from src.core.cache import CacheManager
        cache_manager = CacheManager(enable_redis=False)
        logger.info("✓ 缓存管理器初始化成功")
        
        return True
        
    except Exception as e:
        logger.error(f"模块导入失败: {e}")
        return False

def test_redis_fallback():
    """测试Redis回退机制"""
    logger.info("测试Redis回退机制...")
    
    try:
        from src.core.redis_cache import RedisCacheManager
        
        # 测试无效Redis URL的回退
        cache_manager = RedisCacheManager(
            redis_url="redis://invalid:6379/0",
            fallback_to_memory=True
        )
        
        # 测试缓存操作
        cache_manager.set("test_key", "test_value")
        value = cache_manager.get("test_key")
        
        if value == "test_value":
            logger.info("✓ Redis回退机制工作正常")
            return True
        else:
            logger.error("Redis回退机制测试失败")
            return False
            
    except Exception as e:
        logger.error(f"Redis回退测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始部署问题诊断...")
    logger.info("=" * 50)
    
    # 检查环境
    issues = check_environment()
    if issues:
        logger.warning("发现环境配置问题:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    # 测试导入
    if not test_imports():
        logger.error("模块导入测试失败")
        return False
    
    # 测试Redis回退
    if not test_redis_fallback():
        logger.error("Redis回退测试失败")
        return False
    
    logger.info("=" * 50)
    logger.info("诊断完成！")
    
    # 显示建议
    logger.info("\n建议的环境变量配置:")
    logger.info("REDIS_ENABLED=false")
    logger.info("MODEL_TYPE=lightweight")
    logger.info("CACHE_ENABLED=true")
    logger.info("MONITORING_ENABLED=true")
    
    if not os.environ.get('DEEPSEEK_API_KEY'):
        logger.info("DEEPSEEK_API_KEY=your_api_key_here")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"诊断脚本执行失败: {e}")
        sys.exit(1)
