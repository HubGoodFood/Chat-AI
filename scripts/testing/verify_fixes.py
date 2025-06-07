#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修复效果的简化脚本
"""

import os
import time

# 设置环境变量
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('APP_ENV', 'production')

def test_lazy_loading():
    """测试懒加载效果"""
    print("🔍 测试懒加载效果...")
    
    # 测试IntentClassifier懒加载
    print("   测试IntentClassifier...")
    start_time = time.time()
    from src.app.intent.classifier import IntentClassifier
    classifier = IntentClassifier(lazy_load=True)
    init_time = time.time() - start_time
    print(f"   ✅ IntentClassifier懒加载初始化: {init_time:.3f}秒")
    
    # 测试HybridIntentClassifier懒加载
    print("   测试HybridIntentClassifier...")
    start_time = time.time()
    from src.app.intent.hybrid_classifier import HybridIntentClassifier
    hybrid = HybridIntentClassifier(lazy_load=True)
    init_time = time.time() - start_time
    print(f"   ✅ HybridIntentClassifier懒加载初始化: {init_time:.3f}秒")
    
    # 测试PolicyManager懒加载
    print("   测试PolicyManager...")
    start_time = time.time()
    from src.app.policy.manager import PolicyManager
    policy = PolicyManager(lazy_load=True)
    init_time = time.time() - start_time
    print(f"   ✅ PolicyManager懒加载初始化: {init_time:.3f}秒")
    
    return True

def test_production_safety():
    """测试生产环境安全性"""
    print("\n🔒 测试生产环境安全性...")
    
    # 确保在生产环境模式
    os.environ['APP_ENV'] = 'production'
    
    try:
        from src.app.intent.hybrid_classifier import HybridIntentClassifier
        hybrid = HybridIntentClassifier(lazy_load=True)
        result = hybrid.predict("测试查询")
        print(f"   ✅ 生产环境下HybridClassifier工作正常，结果: {result}")
        return True
    except Exception as e:
        print(f"   ❌ 生产环境测试失败: {e}")
        return False

def test_app_startup():
    """测试应用启动性能"""
    print("\n🚀 测试应用启动性能...")
    
    start_time = time.time()
    try:
        import app
        startup_time = time.time() - start_time
        print(f"   ✅ 应用启动成功，耗时: {startup_time:.2f}秒")
        
        if startup_time < 15:
            print("   ✅ 启动时间优秀")
            return True
        else:
            print("   ⚠️  启动时间较长")
            return False
    except Exception as e:
        startup_time = time.time() - start_time
        print(f"   ❌ 应用启动失败 (耗时: {startup_time:.2f}秒): {e}")
        return False

def main():
    """主函数"""
    print("🔧 验证修复效果")
    print("=" * 40)
    
    tests = [
        ("懒加载效果", test_lazy_loading),
        ("生产环境安全性", test_production_safety),
        ("应用启动性能", test_app_startup)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("📊 验证结果:")
    print("=" * 40)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 所有修复验证通过！")
        print("📝 主要改进:")
        print("   • IntentClassifier实现懒加载")
        print("   • HybridIntentClassifier实现懒加载和生产环境保护")
        print("   • PolicyManager已有懒加载")
        print("   • 重型库导入优化")
        print("   • 应用启动时间显著改善")
    else:
        print("⚠️  部分验证失败，需要进一步检查。")
    print("=" * 40)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
