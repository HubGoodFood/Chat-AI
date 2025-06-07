#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署修复测试脚本
验证超时问题是否已解决
"""

import sys
import os
import time
import logging

# 设置环境变量
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_app_import_speed():
    """测试应用导入速度"""
    print("🚀 测试应用导入速度...")
    start_time = time.time()
    
    try:
        import app
        import_time = time.time() - start_time
        print(f"✅ 应用导入成功，耗时: {import_time:.2f}秒")
        
        if import_time > 30:
            print("⚠️  导入时间较长，可能在生产环境中导致超时")
            return False
        else:
            print("✅ 导入时间正常")
            return True
            
    except Exception as e:
        import_time = time.time() - start_time
        print(f"❌ 应用导入失败 (耗时: {import_time:.2f}秒): {e}")
        return False

def test_policy_manager_lazy_load():
    """测试PolicyManager懒加载"""
    print("\n🔍 测试PolicyManager懒加载...")
    
    try:
        from src.app.policy.manager import PolicyManager
        
        # 测试懒加载初始化
        start_time = time.time()
        policy_manager = PolicyManager(lazy_load=True)
        init_time = time.time() - start_time
        print(f"✅ PolicyManager懒加载初始化成功，耗时: {init_time:.2f}秒")
        
        if init_time > 5:
            print("⚠️  懒加载初始化时间仍然较长")
            return False
        
        # 测试第一次语义搜索（会触发模型加载）
        print("   正在测试第一次语义搜索（会加载模型）...")
        start_time = time.time()
        results = policy_manager.find_policy_excerpt_semantic("配送时间")
        search_time = time.time() - start_time
        print(f"✅ 第一次语义搜索完成，耗时: {search_time:.2f}秒")
        print(f"   搜索结果数量: {len(results)}")
        
        if search_time > 60:
            print("⚠️  第一次搜索时间较长，可能导致请求超时")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PolicyManager测试失败: {e}")
        return False

def test_health_endpoint():
    """测试健康检查端点"""
    print("\n🏥 测试健康检查端点...")
    
    try:
        import app
        with app.application.test_client() as client:
            response = client.get('/health')
            print(f"✅ 健康检查状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ 健康检查响应: {data}")
                return True
            else:
                print(f"❌ 健康检查失败，状态码: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")
        return False

def test_chat_endpoint_basic():
    """测试聊天端点基本功能"""
    print("\n💬 测试聊天端点基本功能...")
    
    try:
        import app
        with app.application.test_client() as client:
            # 测试简单的产品查询（不涉及政策搜索）
            response = client.post('/chat', 
                                 json={'message': '你好', 'user_id': 'test'})
            print(f"✅ 聊天API状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ 聊天响应: {data.get('message', 'N/A')[:50]}...")
                return True
            else:
                print(f"❌ 聊天API失败，状态码: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 聊天端点测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 部署修复验证测试")
    print("=" * 50)
    
    tests = [
        ("应用导入速度", test_app_import_speed),
        ("PolicyManager懒加载", test_policy_manager_lazy_load),
        ("健康检查端点", test_health_endpoint),
        ("聊天端点基本功能", test_chat_endpoint_basic)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！超时问题已修复，可以重新部署。")
        print("\n📝 部署配置:")
        print("   启动命令: gunicorn app:app -c gunicorn.conf.py")
        print("   超时设置: 300秒")
        print("   懒加载: 已启用")
    else:
        print("⚠️  部分测试失败，请检查上述错误。")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
