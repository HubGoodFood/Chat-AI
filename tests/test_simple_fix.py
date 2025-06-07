#!/usr/bin/env python3
"""
简化测试：验证口语化表达的修复效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.intent.hybrid_classifier import HybridIntentClassifier
from app.chat.handler import ChatHandler
from app.products.manager import ProductManager
import logging

# 设置日志级别为WARNING以减少输出
logging.basicConfig(level=logging.WARNING)

def test_key_cases():
    """测试关键用例"""
    
    print("测试关键用例修复效果")
    print("=" * 40)
    
    # 初始化组件
    classifier = HybridIntentClassifier()
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 关键测试用例
    test_cases = [
        {
            "query": "草莓卖不？",
            "expected_intent": "inquiry_availability",
            "expected_product": "草莓"
        },
        {
            "query": "苹果有不？", 
            "expected_intent": "inquiry_availability",
            "expected_product": "苹果"
        },
        {
            "query": "西瓜卖不",
            "expected_intent": "inquiry_availability", 
            "expected_product": "西瓜"
        }
    ]
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        expected_intent = case["expected_intent"]
        expected_product = case["expected_product"]
        
        print(f"\n测试 {i}: '{query}'")
        
        # 测试意图识别
        predicted_intent = classifier.predict(query)
        intent_correct = predicted_intent == expected_intent
        print(f"  意图识别: {predicted_intent} {'OK' if intent_correct else 'FAIL'}")

        # 测试产品提取
        extracted_product = chat_handler._extract_product_name_from_query(query)
        product_correct = extracted_product == expected_product
        print(f"  产品提取: '{extracted_product}' {'OK' if product_correct else 'FAIL'}")

        case_passed = intent_correct and product_correct
        print(f"  结果: {'通过' if case_passed else '失败'}")
        
        if not case_passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    print(f"总体结果: {'所有测试通过' if all_passed else '部分测试失败'}")
    
    return all_passed

if __name__ == "__main__":
    success = test_key_cases()
    
    if success:
        print("\n[SUCCESS] 修复成功！口语化表达现在可以正确识别了。")
    else:
        print("\n[FAIL] 修复未完全成功，需要进一步调试。")
