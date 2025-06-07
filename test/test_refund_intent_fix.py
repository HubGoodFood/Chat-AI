#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退货意图识别修复测试
测试"芒果烂了怎么退"等售后服务查询的意图识别修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.chat.handler import ChatHandler
from src.app.intent.lightweight_classifier import LightweightIntentClassifier
from src.app.products.manager import ProductManager

def test_refund_intent_recognition():
    """测试退货意图识别的修复效果"""
    
    # 初始化处理器
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager)
    intent_classifier = LightweightIntentClassifier()
    
    # 测试用例：应该被识别为 refund_request 的查询
    refund_test_cases = [
        "芒果烂了怎么退",
        "苹果坏了如何退", 
        "香蕉变质了怎么退货",
        "这个有问题怎么退",
        "买的东西质量问题怎么办",
        "怎么退货",
        "如何退款",
        "水果烂了怎么办",
        "东西坏了怎么退",
        "质量有问题怎么退",
        "售后服务",
        "联系客服",
        "我要退货",
        "退货流程",
        "申请退款"
    ]
    
    # 测试用例：应该保持原有意图识别的查询
    other_intent_cases = [
        ("有苹果吗", "inquiry_availability"),
        ("苹果多少钱", "inquiry_price_or_buy"), 
        ("你好", "greeting"),
        ("你们的退货政策是什么", "inquiry_policy"),
        ("推荐点好吃的水果", "request_recommendation"),
        ("你是谁", "identity_query")
    ]
    
    print("测试退货意图识别修复效果")
    print("=" * 50)
    
    # 测试退货相关查询
    print("\n测试退货/售后服务相关查询:")
    refund_success = 0
    for test_case in refund_test_cases:
        # 使用ChatHandler的detect_intent方法
        intent = chat_handler.detect_intent(test_case)
        
        # 也测试轻量级分类器
        classifier_intent = intent_classifier.predict(test_case)
        
        status = "PASS" if intent == "refund_request" else "FAIL"
        classifier_status = "PASS" if classifier_intent == "refund_request" else "FAIL"
        
        print(f"{status} \"{test_case}\" → {intent} (分类器: {classifier_status} {classifier_intent})")
        
        if intent == "refund_request":
            refund_success += 1
    
    print(f"\n退货意图识别成功率: {refund_success}/{len(refund_test_cases)} ({refund_success/len(refund_test_cases)*100:.1f}%)")
    
    # 测试其他意图不受影响
    print("\n测试其他意图不受影响:")
    other_success = 0
    for test_case, expected_intent in other_intent_cases:
        intent = chat_handler.detect_intent(test_case)
        classifier_intent = intent_classifier.predict(test_case)
        
        status = "PASS" if intent == expected_intent else "FAIL"
        classifier_status = "PASS" if classifier_intent == expected_intent else "FAIL"
        
        print(f"{status} \"{test_case}\" → {intent} (期望: {expected_intent}, 分类器: {classifier_status} {classifier_intent})")
        
        if intent == expected_intent:
            other_success += 1
    
    print(f"\n其他意图识别成功率: {other_success}/{len(other_intent_cases)} ({other_success/len(other_intent_cases)*100:.1f}%)")
    
    # 总体评估
    total_success = refund_success + other_success
    total_cases = len(refund_test_cases) + len(other_intent_cases)
    
    print("\n" + "=" * 50)
    print(f"总体测试结果: {total_success}/{total_cases} ({total_success/total_cases*100:.1f}%)")

    if refund_success == len(refund_test_cases) and other_success == len(other_intent_cases):
        print("所有测试通过！退货意图识别修复成功！")
        return True
    else:
        print("部分测试失败，需要进一步调整")
        return False

def test_specific_case():
    """专门测试问题案例：芒果烂了怎么退"""
    
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager)
    intent_classifier = LightweightIntentClassifier()
    
    test_input = "芒果烂了怎么退"
    
    print(f"\n专项测试: \"{test_input}\"")
    print("-" * 30)
    
    # ChatHandler 意图识别
    handler_intent = chat_handler.detect_intent(test_input)
    print(f"ChatHandler 识别结果: {handler_intent}")
    
    # 轻量级分类器意图识别
    classifier_intent = intent_classifier.predict(test_input)
    confidence = intent_classifier.get_prediction_confidence(test_input)
    print(f"轻量级分类器识别结果: {classifier_intent} (置信度: {confidence[1]:.3f})")
    
    # 测试完整的聊天处理流程
    try:
        response = chat_handler.handle_chat_message(test_input, "test_user")
        print(f"完整处理结果类型: {type(response)}")
        if isinstance(response, str):
            print(f"回复内容: {response[:100]}...")
        elif isinstance(response, dict):
            print(f"结构化回复: {response.get('response', '')[:100]}...")
    except Exception as e:
        print(f"处理过程出错: {e}")
    
    return handler_intent == "refund_request"

if __name__ == "__main__":
    print("开始测试退货意图识别修复效果")

    # 运行主要测试
    main_test_passed = test_refund_intent_recognition()

    # 运行专项测试
    specific_test_passed = test_specific_case()

    print("\n" + "=" * 60)
    if main_test_passed and specific_test_passed:
        print("所有测试通过！修复成功！")
    else:
        print("测试失败，需要进一步调整")
