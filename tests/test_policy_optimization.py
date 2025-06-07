#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的政策功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.policy.manager import PolicyManager
from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def test_policy_manager():
    """测试PolicyManager的基本功能"""
    print("🔍 测试PolicyManager基本功能...")
    
    try:
        policy_manager = PolicyManager()
        
        # 测试版本信息
        version = policy_manager.get_policy_version()
        last_updated = policy_manager.get_policy_last_updated()
        print(f"✅ 政策版本: {version}")
        print(f"✅ 最后更新: {last_updated}")
        
        # 测试获取所有分类
        sections = policy_manager.get_all_sections()
        print(f"✅ 政策分类数量: {len(sections)}")
        print(f"✅ 政策分类: {sections}")
        
        # 测试获取特定分类
        mission = policy_manager.get_policy_section('mission')
        print(f"✅ 拼台宗旨条目数: {len(mission)}")
        
        pickup = policy_manager.get_policy_section('pickup')
        print(f"✅ 取货信息条目数: {len(pickup)}")
        
        community = policy_manager.get_policy_section('community')
        print(f"✅ 社区互助条目数: {len(community)}")
        
        return True
        
    except Exception as e:
        print(f"❌ PolicyManager测试失败: {e}")
        return False

def test_semantic_search():
    """测试语义搜索功能"""
    print("\n🔍 测试语义搜索功能...")
    
    try:
        policy_manager = PolicyManager()
        
        # 测试不同类型的查询
        test_queries = [
            "配送时间是什么时候",
            "怎么付款",
            "取货地址在哪里",
            "质量有问题怎么办",
            "群规是什么",
            "你们的理念是什么"
        ]
        
        for query in test_queries:
            results = policy_manager.find_policy_excerpt_semantic(query, top_k=2)
            print(f"✅ 查询: '{query}' -> 找到 {len(results)} 条相关政策")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 语义搜索测试失败: {e}")
        return False

def test_chat_handler_policy():
    """测试ChatHandler的政策处理功能"""
    print("\n🔍 测试ChatHandler政策处理功能...")
    
    try:
        # 初始化组件
        product_manager = ProductManager()
        product_manager.load_product_data()
        policy_manager = PolicyManager()
        cache_manager = CacheManager()
        chat_handler = ChatHandler(product_manager, policy_manager, cache_manager)
        
        # 测试政策查询
        test_queries = [
            "配送政策是什么",
            "怎么付款",
            "取货点在哪里",
            "质量问题怎么处理",
            "群规有哪些"
        ]
        
        for query in test_queries:
            response = chat_handler.handle_chat_message(query, 'test_user')
            print(f"✅ 查询: '{query}'")
            if isinstance(response, str):
                print(f"   回复长度: {len(response)} 字符")
                print(f"   回复预览: {response[:100]}...")
            else:
                print(f"   回复类型: {type(response)}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ ChatHandler政策测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试优化后的政策功能\n")
    
    results = []
    
    # 运行各项测试
    results.append(test_policy_manager())
    results.append(test_semantic_search())
    results.append(test_chat_handler_policy())
    
    # 总结测试结果
    print("\n📊 测试结果总结:")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有测试通过! ({passed}/{total})")
        print("✅ 政策优化成功!")
    else:
        print(f"⚠️  部分测试失败: {passed}/{total}")
        print("❌ 需要进一步检查和修复")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
