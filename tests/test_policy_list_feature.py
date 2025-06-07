#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政策查询功能测试
测试新增的政策列表查询和政策类别选择功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.app.policy.manager import PolicyManager
from src.core.cache import CacheManager

def test_policy_list_feature():
    """测试完整的政策查询功能"""
    print("[测试] 开始测试政策查询功能...")

    # 初始化组件
    try:
        product_manager = ProductManager()
        product_manager.load_product_data()

        policy_manager = PolicyManager()
        cache_manager = CacheManager()

        handler = ChatHandler(
            product_manager=product_manager,
            policy_manager=policy_manager,
            cache_manager=cache_manager
        )

        print("[成功] 组件初始化成功")
    except Exception as e:
        print(f"[错误] 组件初始化失败: {e}")
        return False

    # 测试用例
    test_cases = [
        {
            "name": "政策列表查询1",
            "input": "你们有什么政策？",
            "expected_intent": "inquiry_policy_list",
            "should_have_buttons": True
        },
        {
            "name": "政策列表查询2",
            "input": "政策有哪些",
            "expected_intent": "inquiry_policy_list",
            "should_have_buttons": True
        },
        {
            "name": "政策列表查询3",
            "input": "有什么规定",
            "expected_intent": "inquiry_policy_list",
            "should_have_buttons": True
        },
        {
            "name": "具体政策查询",
            "input": "配送政策是什么",
            "expected_intent": "inquiry_policy",
            "should_have_buttons": False
        }
    ]

    print("\n[测试] 测试意图识别...")
    for case in test_cases:
        try:
            # 测试意图识别
            user_input_processed = case["input"].lower()
            detected_intent = handler.detect_intent(user_input_processed)

            if detected_intent == case["expected_intent"]:
                print(f"[成功] {case['name']}: 意图识别正确 ({detected_intent})")
            else:
                print(f"[错误] {case['name']}: 意图识别错误，期望 {case['expected_intent']}，实际 {detected_intent}")

        except Exception as e:
            print(f"[错误] {case['name']}: 意图识别出错 - {e}")
    
    print("\n[测试] 测试政策列表查询响应...")
    try:
        # 测试政策列表查询
        response = handler.handle_chat_message("你们有什么政策？", "test_user")

        if isinstance(response, dict):
            if "message" in response and "product_suggestions" in response:
                print("[成功] 政策列表查询返回正确的字典格式")
                print(f"[消息] {response['message'][:100]}...")

                suggestions = response["product_suggestions"]
                if suggestions and len(suggestions) > 0:
                    print(f"[成功] 返回了 {len(suggestions)} 个政策类别按钮")
                    for i, suggestion in enumerate(suggestions[:3]):
                        print(f"   {i+1}. {suggestion.get('display_text', 'N/A')} -> {suggestion.get('payload', 'N/A')}")
                else:
                    print("[错误] 没有返回政策类别按钮")
            else:
                print("[错误] 返回格式不正确，缺少必要字段")
        else:
            print(f"[错误] 返回类型错误，期望dict，实际 {type(response)}")

    except Exception as e:
        print(f"[错误] 政策列表查询测试出错: {e}")

    print("\n[测试] 测试政策类别选择...")
    try:
        # 测试政策类别选择
        category_response = handler.handle_chat_message("policy_category:delivery", "test_user")

        if isinstance(category_response, str) and "配送政策" in category_response:
            print("[成功] 政策类别选择功能正常")
            # 避免编码问题，只显示前100个字符
            safe_content = category_response.encode('ascii', 'ignore').decode('ascii')[:100]
            print(f"[内容] 配送政策内容: {safe_content}...")
        else:
            print(f"[错误] 政策类别选择功能异常: {type(category_response)}")

    except Exception as e:
        print(f"[错误] 政策类别选择测试出错: {e}")

    print("\n[测试] 测试政策管理器方法...")
    try:
        # 测试政策管理器的新方法
        categories = policy_manager.get_policy_categories()
        print(f"[成功] 获取到 {len(categories)} 个政策类别")

        for category in categories[:3]:
            print(f"   - {category['display_text']}: {category['payload']}")

        # 测试获取具体政策
        delivery_policy = policy_manager.get_policy_by_category("delivery")
        if "配送政策" in delivery_policy:
            print("[成功] 政策内容获取功能正常")
        else:
            print("[错误] 政策内容获取功能异常")

    except Exception as e:
        print(f"[错误] 政策管理器测试出错: {e}")

    print("\n[完成] 政策查询功能测试完成！")
    return True

if __name__ == "__main__":
    test_policy_list_feature()
