#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政策查询功能修复验证测试

测试修复后的政策查询功能是否能正确返回：
1. "自取" 查询 -> 取货地址信息
2. "怎么付款" 查询 -> Venmo账号信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.chat.handler import ChatHandler
from src.app.policy.manager import PolicyManager
from src.app.policy.lightweight_manager import LightweightPolicyManager
from src.app.products.manager import ProductManager

def test_policy_query_fix():
    """测试政策查询修复效果"""
    
    print("政策查询功能修复验证测试")
    print("=" * 60)
    
    # 初始化组件
    try:
        policy_manager = PolicyManager(policy_file='data/policy.json')
        product_manager = ProductManager()
        chat_handler = ChatHandler(product_manager)

        print("组件初始化成功")
    except Exception as e:
        print(f"组件初始化失败: {e}")
        return
    
    # 测试用例
    test_cases = [
        {
            "query": "自取",
            "expected_keywords": ["取货点", "地址", "malden", "chinatown", "273", "25"],
            "description": "自取地址查询"
        },
        {
            "query": "哪里有自取点",
            "expected_keywords": ["取货点", "地址", "malden", "chinatown"],
            "description": "自取点位置查询"
        },
        {
            "query": "怎么付款",
            "expected_keywords": ["venmo", "账号", "sabrina0861", "付款"],
            "description": "付款方式查询"
        },
        {
            "query": "付款方式",
            "expected_keywords": ["venmo", "账号", "sabrina0861"],
            "description": "付款方式详情查询"
        }
    ]
    
    print("\n开始测试政策查询...")
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_keywords = test_case["expected_keywords"]
        description = test_case["description"]
        
        print(f"\n--- 测试 {i}: {description} ---")
        print(f"查询: '{query}'")
        
        try:
            # 测试轻量级政策管理器
            if policy_manager.lightweight_manager:
                lightweight_results = policy_manager.lightweight_manager.search_policy(query, top_k=3)
                print(f"轻量级搜索结果数量: {len(lightweight_results)}")
                
                if lightweight_results:
                    print("轻量级搜索结果:")
                    for j, result in enumerate(lightweight_results, 1):
                        print(f"  {j}. {result}")
                    
                    # 检查关键词匹配
                    all_results_text = " ".join(lightweight_results).lower()
                    matched_keywords = [kw for kw in expected_keywords if kw.lower() in all_results_text]
                    
                    if matched_keywords:
                        print(f"[OK] 匹配到期望关键词: {matched_keywords}")
                    else:
                        print(f"[FAIL] 未匹配到期望关键词: {expected_keywords}")
                        print(f"   实际内容: {all_results_text[:200]}...")
                else:
                    print("[FAIL] 轻量级搜索无结果")
            
            # 测试完整的政策管理器搜索
            full_results = policy_manager.search_policy(query, top_k=3)
            print(f"完整搜索结果数量: {len(full_results)}")
            
            if full_results:
                print("完整搜索结果:")
                for j, result in enumerate(full_results, 1):
                    print(f"  {j}. {result}")
                
                # 检查关键词匹配
                all_results_text = " ".join(full_results).lower()
                matched_keywords = [kw for kw in expected_keywords if kw.lower() in all_results_text]
                
                if matched_keywords:
                    print(f"[OK] 匹配到期望关键词: {matched_keywords}")
                else:
                    print(f"[FAIL] 未匹配到期望关键词: {expected_keywords}")
                    print(f"   实际内容: {all_results_text[:200]}...")
            else:
                print("[FAIL] 完整搜索无结果")
            
            # 测试聊天处理器
            chat_response = chat_handler.handle_policy_question(query)
            if chat_response:
                print(f"聊天处理器回复长度: {len(chat_response)}")
                response_lower = chat_response.lower()
                matched_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]
                
                if matched_keywords:
                    print(f"[OK] 聊天回复包含期望关键词: {matched_keywords}")
                else:
                    print(f"[FAIL] 聊天回复未包含期望关键词: {expected_keywords}")
                    print(f"   回复内容: {chat_response[:300]}...")
            else:
                print("[FAIL] 聊天处理器无回复")

        except Exception as e:
            print(f"[ERROR] 测试出错: {e}")

    print("\n" + "=" * 60)
    print("政策查询功能修复验证测试完成")

if __name__ == "__main__":
    test_policy_query_fix()
