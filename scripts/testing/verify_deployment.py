#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署验证脚本
用于验证应用是否可以正确启动和导入
"""

import sys
import os

def test_app_import():
    """测试应用导入"""
    print("🔍 测试应用导入...")
    try:
        import app
        print("✅ app.py 导入成功")
        print(f"   应用类型: {type(app.application)}")
        print(f"   应用名称: {app.application.name}")
        return True
    except Exception as e:
        print(f"❌ app.py 导入失败: {e}")
        return False

def test_flask_routes():
    """测试Flask路由"""
    print("\n🔍 测试Flask路由...")
    try:
        import app
        with app.application.test_client() as client:
            # 测试主页
            response = client.get('/')
            print(f"   主页状态码: {response.status_code}")
            
            # 测试聊天API
            response = client.post('/chat', 
                                 json={'message': '你好', 'user_id': 'test'})
            print(f"   聊天API状态码: {response.status_code}")
            
        print("✅ Flask路由测试通过")
        return True
    except Exception as e:
        print(f"❌ Flask路由测试失败: {e}")
        return False

def test_dependencies():
    """测试关键依赖"""
    print("\n🔍 测试关键依赖...")
    dependencies = [
        'flask',
        'gunicorn', 
        'openai',
        'pandas',
        'scikit-learn'
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - 未安装")
            all_ok = False
    
    return all_ok

def main():
    """主函数"""
    print("🚀 开始部署验证...\n")
    
    tests = [
        ("依赖检查", test_dependencies),
        ("应用导入", test_app_import),
        ("路由测试", test_flask_routes)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 验证结果汇总:")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有测试通过！应用已准备好部署。")
        print("\n📝 部署命令:")
        print("   gunicorn app:app --bind 0.0.0.0:$PORT")
    else:
        print("⚠️  部分测试失败，请检查上述错误。")
    print("="*50)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
