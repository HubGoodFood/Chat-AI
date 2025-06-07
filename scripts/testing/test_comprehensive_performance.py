#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合性能测试脚本
检查所有隐藏的性能问题和超时风险
"""

import sys
import os
import time
import logging

# 设置环境变量
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
os.environ.setdefault('APP_ENV', 'production')  # 测试生产环境行为

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_app_import_performance():
    """测试应用导入性能"""
    print("🚀 测试应用导入性能...")
    start_time = time.time()
    
    try:
        import app
        import_time = time.time() - start_time
        print(f"✅ 应用导入成功，耗时: {import_time:.2f}秒")
        
        if import_time > 15:
            print("⚠️  导入时间较长，可能在生产环境中导致超时")
            return False
        else:
            print("✅ 导入时间正常")
            return True
            
    except Exception as e:
        import_time = time.time() - start_time
        print(f"❌ 应用导入失败 (耗时: {import_time:.2f}秒): {e}")
        return False

def test_intent_classifier_lazy_load():
    """测试IntentClassifier懒加载"""
    print("\n🧠 测试IntentClassifier懒加载...")
    
    try:
        from src.app.intent.classifier import IntentClassifier
        
        # 测试懒加载初始化
        start_time = time.time()
        classifier = IntentClassifier(lazy_load=True)
        init_time = time.time() - start_time
        print(f"✅ IntentClassifier懒加载初始化成功，耗时: {init_time:.2f}秒")
        
        if init_time > 2:
            print("⚠️  懒加载初始化时间仍然较长")
            return False
        
        # 测试第一次预测（会触发模型加载）
        print("   正在测试第一次预测（会加载模型）...")
        start_time = time.time()
        result = classifier.predict("苹果多少钱")
        predict_time = time.time() - start_time
        print(f"✅ 第一次预测完成，耗时: {predict_time:.2f}秒，结果: {result}")
        
        if predict_time > 30:
            print("⚠️  第一次预测时间较长，可能导致请求超时")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ IntentClassifier测试失败: {e}")
        return False

def test_hybrid_classifier_production_safety():
    """测试HybridClassifier生产环境安全性"""
    print("\n🔒 测试HybridClassifier生产环境安全性...")
    
    try:
        from src.app.intent.hybrid_classifier import HybridIntentClassifier
        
        # 删除模型文件以测试生产环境行为
        model_path = "src/models/hybrid_intent_model"
        model_file = os.path.join(model_path, 'ml_model.joblib')
        model_exists = os.path.exists(model_file)
        
        if model_exists:
            # 临时重命名模型文件
            backup_file = model_file + ".backup"
            os.rename(model_file, backup_file)
        
        try:
            # 在生产环境中初始化（应该不会训练）
            start_time = time.time()
            classifier = HybridIntentClassifier(lazy_load=True)
            init_time = time.time() - start_time
            
            # 触发模型加载
            result = classifier.predict("测试查询")
            total_time = time.time() - start_time
            
            print(f"✅ 生产环境初始化成功，耗时: {total_time:.2f}秒")
            print(f"   预测结果: {result}")
            
            if total_time > 10:
                print("⚠️  生产环境初始化时间较长")
                return False
            
            return True
            
        finally:
            # 恢复模型文件
            if model_exists:
                os.rename(backup_file, model_file)
        
    except Exception as e:
        print(f"❌ HybridClassifier生产环境测试失败: {e}")
        return False

def test_policy_manager_lazy_load():
    """测试PolicyManager懒加载"""
    print("\n📋 测试PolicyManager懒加载...")
    
    try:
        from src.app.policy.manager import PolicyManager
        
        # 测试懒加载初始化
        start_time = time.time()
        policy_manager = PolicyManager(lazy_load=True)
        init_time = time.time() - start_time
        print(f"✅ PolicyManager懒加载初始化成功，耗时: {init_time:.2f}秒")
        
        if init_time > 2:
            print("⚠️  懒加载初始化时间仍然较长")
            return False
        
        # 测试第一次语义搜索（会触发模型加载）
        print("   正在测试第一次语义搜索（会加载模型）...")
        start_time = time.time()
        results = policy_manager.find_policy_excerpt_semantic("配送时间")
        search_time = time.time() - start_time
        print(f"✅ 第一次语义搜索完成，耗时: {search_time:.2f}秒")
        print(f"   搜索结果数量: {len(results)}")
        
        if search_time > 30:
            print("⚠️  第一次搜索时间较长，可能导致请求超时")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PolicyManager测试失败: {e}")
        return False

def test_chat_handler_initialization():
    """测试ChatHandler初始化性能"""
    print("\n💬 测试ChatHandler初始化性能...")
    
    try:
        from src.app.products.manager import ProductManager
        from src.app.policy.manager import PolicyManager
        from src.app.chat.handler import ChatHandler
        from src.core.cache import CacheManager
        
        # 初始化依赖
        cache_manager = CacheManager()
        product_manager = ProductManager(cache_manager=cache_manager)
        policy_manager = PolicyManager(lazy_load=True)
        
        # 测试ChatHandler初始化
        start_time = time.time()
        chat_handler = ChatHandler(
            product_manager=product_manager,
            policy_manager=policy_manager,
            cache_manager=cache_manager
        )
        init_time = time.time() - start_time
        print(f"✅ ChatHandler初始化成功，耗时: {init_time:.2f}秒")
        
        if init_time > 5:
            print("⚠️  ChatHandler初始化时间较长")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ChatHandler初始化测试失败: {e}")
        return False

def test_memory_usage():
    """测试内存使用情况"""
    print("\n💾 测试内存使用情况...")
    
    try:
        import psutil
        process = psutil.Process()
        
        # 获取初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"   初始内存使用: {initial_memory:.1f} MB")
        
        # 导入应用
        import app
        
        # 获取导入后内存使用
        after_import_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_import_memory - initial_memory
        print(f"   导入后内存使用: {after_import_memory:.1f} MB")
        print(f"   内存增加: {memory_increase:.1f} MB")
        
        if memory_increase > 500:  # 500MB
            print("⚠️  内存使用较高，可能在资源受限环境中出现问题")
            return False
        
        return True
        
    except ImportError:
        print("   psutil未安装，跳过内存测试")
        return True
    except Exception as e:
        print(f"❌ 内存测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 综合性能测试")
    print("=" * 60)
    
    tests = [
        ("应用导入性能", test_app_import_performance),
        ("IntentClassifier懒加载", test_intent_classifier_lazy_load),
        ("HybridClassifier生产环境安全", test_hybrid_classifier_production_safety),
        ("PolicyManager懒加载", test_policy_manager_lazy_load),
        ("ChatHandler初始化", test_chat_handler_initialization),
        ("内存使用情况", test_memory_usage)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 综合测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有性能测试通过！应用已优化，可以安全部署。")
    else:
        print("⚠️  部分测试失败，请检查上述问题。")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
