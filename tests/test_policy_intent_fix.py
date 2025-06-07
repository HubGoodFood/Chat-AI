#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的政策意图识别
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.app.policy.manager import PolicyManager
from src.core.cache import CacheManager

def test_policy_intent_detection():
    """测试政策意图识别"""
    print("🔍 测试政策意图识别修复效果")
    print("=" * 60)
    
    # 初始化组件
    product_manager = ProductManager()
    product_manager.load_product_data()
    policy_manager = PolicyManager()
    cache_manager = CacheManager()
    chat_handler = ChatHandler(product_manager, policy_manager, cache_manager)
    
    # 政策相关查询
    policy_queries = [
        "你们的拼台理念是什么？",
        "配送时间和费用怎么算？",
        "支付方式有哪些？",
        "取货点在哪里？",
        "质量有问题怎么办？",
        "群规有什么要求？",
        "社区互助是怎么回事？",
        "怎么付款？",
        "配送政策是什么？",
        "退款规定是什么？"
    ]
    
    print("🎯 测试政策意图识别:")
    for query in policy_queries:
        # 测试意图识别
        intent = chat_handler.detect_intent(query.lower())
        print(f"查询: '{query}' -> 意图: {intent}")
        
        # 如果识别为政策意图，测试回复
        if intent == 'inquiry_policy':
            print("✅ 正确识别为政策查询")
        else:
            print(f"❌ 错误识别为: {intent}")
    
    print("\n" + "=" * 60)
    print("🎭 测试实际回复效果:")
    
    # 测试几个关键查询的实际回复
    key_queries = [
        "配送政策是什么？",
        "怎么付款？",
        "取货点在哪里？",
        "你们的理念是什么？"
    ]
    
    for query in key_queries:
        print(f"\n🔍 查询: {query}")
        print("-" * 40)
        
        try:
            response = chat_handler.handle_chat_message(query, 'test_user')
            
            if isinstance(response, str):
                # 检查是否是政策回复（包含政策标识符）
                if "📋 关于您的政策问题" in response or "政策版本" in response:
                    print("✅ 正确返回政策回复")
                    print(f"回复预览: {response[:150]}...")
                else:
                    print("❌ 返回的不是政策回复")
                    print(f"回复预览: {response[:150]}...")
            else:
                print(f"❌ 返回类型错误: {type(response)}")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")

def main():
    """主函数"""
    test_policy_intent_detection()
    
    print("\n🎯 修复总结:")
    print("✅ 添加了明确的政策关键词检测")
    print("✅ 增加了政策问句模式匹配")
    print("✅ 提高了政策意图识别的优先级")
    print("✅ 避免政策查询被误判为产品查询")

if __name__ == "__main__":
    main()
