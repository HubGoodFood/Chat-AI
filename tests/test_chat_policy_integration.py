#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天政策集成测试

测试完整的聊天流程中政策查询是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager

def test_chat_policy_integration():
    """测试聊天中的政策查询集成"""
    
    print("聊天政策集成测试")
    print("=" * 50)
    
    # 初始化聊天处理器
    try:
        product_manager = ProductManager()
        chat_handler = ChatHandler(product_manager)
        print("聊天处理器初始化成功")
    except Exception as e:
        print(f"初始化失败: {e}")
        return
    
    # 测试用例
    test_cases = [
        {
            "user_input": "自取",
            "expected_content": ["取货点", "地址", "Malden", "Chinatown"],
            "description": "自取查询"
        },
        {
            "user_input": "哪里有自取点",
            "expected_content": ["取货点", "地址", "Malden", "Chinatown"],
            "description": "自取点位置查询"
        },
        {
            "user_input": "怎么付款",
            "expected_content": ["Venmo", "账号", "Sabrina0861"],
            "description": "付款方式查询"
        },
        {
            "user_input": "付款方式",
            "expected_content": ["Venmo", "账号", "Sabrina0861"],
            "description": "付款方式详情查询"
        }
    ]
    
    print("\n开始测试聊天政策查询...")
    
    for i, test_case in enumerate(test_cases, 1):
        user_input = test_case["user_input"]
        expected_content = test_case["expected_content"]
        description = test_case["description"]
        
        print(f"\n--- 测试 {i}: {description} ---")
        print(f"用户输入: '{user_input}'")
        
        try:
            # 模拟完整的聊天流程
            response = chat_handler.handle_chat_message(
                user_input=user_input,
                user_id="test_user"
            )
            
            if response:
                print(f"回复类型: {type(response)}")
                
                # 提取回复内容
                if isinstance(response, dict):
                    message = response.get('message', '')
                    suggestions = response.get('product_suggestions', [])
                    print(f"回复消息长度: {len(message)}")
                    print(f"建议数量: {len(suggestions)}")
                elif isinstance(response, str):
                    message = response
                    print(f"回复消息长度: {len(message)}")
                else:
                    message = str(response)
                    print(f"回复内容: {message}")
                
                # 检查期望内容
                message_lower = message.lower()
                matched_content = []
                for content in expected_content:
                    if content.lower() in message_lower:
                        matched_content.append(content)
                
                if matched_content:
                    print(f"[OK] 找到期望内容: {matched_content}")
                    print(f"回复预览: {message[:200]}...")
                else:
                    print(f"[FAIL] 未找到期望内容: {expected_content}")
                    print(f"实际回复: {message[:300]}...")
            else:
                print("[FAIL] 无回复")
                
        except Exception as e:
            print(f"[ERROR] 测试出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("聊天政策集成测试完成")

if __name__ == "__main__":
    test_chat_policy_integration()
