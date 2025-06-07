#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.app.intent.classifier import IntentClassifier

def test_chat_fix():
    """测试修复后的聊天功能"""
    
    # 初始化组件
    product_manager = ProductManager()
    intent_classifier = IntentClassifier()
    chat_handler = ChatHandler(product_manager, intent_classifier)

    test_queries = [
        "有没有鸭子？",
        "卖不卖月饼？",
        "有蓝莓吗？"
    ]

    for query in test_queries:
        print(f"\n测试查询: {query}")
        print("-" * 50)
        
        try:
            response = chat_handler.handle_chat_message(query, "test_user")
            print(f"回复类型: {type(response)}")
            
            if isinstance(response, dict):
                message = response.get("message", "")
                suggestions = response.get("product_suggestions", [])
                
                print(f"消息长度: {len(message)}")
                print(f"推荐按钮数量: {len(suggestions)}")
                
                if suggestions:
                    print("推荐按钮:")
                    for i, suggestion in enumerate(suggestions):
                        display_text = suggestion.get("display_text", "")
                        payload = suggestion.get("payload", "")
                        print(f"  {i+1}. {display_text} (payload: {payload})")
                
                # 显示消息的前100个字符
                print(f"消息预览: {message[:100]}...")
                
            else:
                print(f"回复: {response}")
                
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_chat_fix()
