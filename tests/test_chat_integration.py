#!/usr/bin/env python3
"""
测试聊天集成：验证完整的聊天流程
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.chat.handler import ChatHandler
from app.products.manager import ProductManager
from app.intent.classifier import IntentClassifier
import logging

# 设置日志级别为WARNING以减少输出
logging.basicConfig(level=logging.WARNING)

def test_chat_flow():
    """测试完整的聊天流程"""
    
    print("测试完整聊天流程")
    print("=" * 40)
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试用例
    test_queries = [
        "草莓卖不？",
        "苹果有不？", 
        "西瓜卖不",
        "有没有草莓"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n测试 {i}: 用户输入 '{query}'")
        
        try:
            # 调用聊天处理器
            response = chat_handler.handle_chat_message(query, f"test_user_{i}")
            
            # 检查响应
            if isinstance(response, dict):
                message = response.get('message', '')
                suggestions = response.get('product_suggestions', [])
                
                print(f"  响应消息: {message[:100]}...")
                print(f"  产品建议数量: {len(suggestions)}")
                
                # 检查是否包含产品信息
                has_product_info = any(keyword in message for keyword in ['价格', '售价', '元', '$'])
                print(f"  包含产品信息: {'是' if has_product_info else '否'}")
                
            else:
                print(f"  响应: {response[:100]}...")
                
        except Exception as e:
            print(f"  错误: {str(e)}")
    
    print("\n" + "=" * 40)
    print("聊天流程测试完成")

if __name__ == "__main__":
    test_chat_flow()
