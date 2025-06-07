#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退货意图识别边缘情况测试
测试各种复杂的退货相关查询，确保修复的鲁棒性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.chat.handler import ChatHandler
from src.app.intent.lightweight_classifier import LightweightIntentClassifier
from src.app.products.manager import ProductManager

def test_edge_cases():
    """测试边缘情况和复杂查询"""
    
    # 初始化处理器
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager)
    intent_classifier = LightweightIntentClassifier()
    
    # 边缘测试用例
    edge_cases = [
        # 复杂的质量问题描述
        ("这个芒果有点烂了，能退吗", "refund_request"),
        ("买的苹果都坏了，怎么处理", "refund_request"),
        ("香蕉变黑了，可以退货吗", "refund_request"),
        ("水果不新鲜，怎么退", "refund_request"),
        
        # 混合表达
        ("芒果质量有问题，我想退货", "refund_request"),
        ("这批水果烂了，需要退款", "refund_request"),
        ("买的东西有问题，要求退货", "refund_request"),
        
        # 询问流程类
        ("退货的具体流程是什么", "refund_request"),
        ("如何申请退款", "refund_request"),
        ("退货需要什么手续", "refund_request"),
        
        # 售后服务类
        ("有质量问题找谁", "refund_request"),
        ("售后怎么联系", "refund_request"),
        ("客服电话多少", "refund_request"),
        
        # 应该保持为其他意图的查询
        ("退货政策是什么", "inquiry_policy"),
        ("你们的退款规定", "inquiry_policy"),
        ("有芒果吗", "inquiry_availability"),
        ("芒果多少钱", "inquiry_price_or_buy"),
        ("推荐点新鲜水果", "request_recommendation"),
        
        # 容易混淆的查询
        ("芒果", "inquiry_availability"),  # 单独产品名应该是可用性查询
        ("退", "refund_request"),  # 单独"退"字应该是退货请求
        ("怎么办", "unknown"),  # 单独"怎么办"应该是未知意图
    ]
    
    print("测试边缘情况和复杂查询")
    print("=" * 50)
    
    success_count = 0
    total_count = len(edge_cases)
    
    for test_input, expected_intent in edge_cases:
        # 使用ChatHandler的detect_intent方法
        actual_intent = chat_handler.detect_intent(test_input)
        
        # 也测试轻量级分类器
        classifier_intent = intent_classifier.predict(test_input)
        
        # 判断是否成功
        is_success = actual_intent == expected_intent
        status = "PASS" if is_success else "FAIL"
        classifier_status = "PASS" if classifier_intent == expected_intent else "FAIL"
        
        print(f"{status} \"{test_input}\" -> {actual_intent} (期望: {expected_intent}, 分类器: {classifier_status} {classifier_intent})")
        
        if is_success:
            success_count += 1
    
    print(f"\n边缘情况测试成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    return success_count == total_count

def test_real_world_scenarios():
    """测试真实世界场景"""
    
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager)
    
    # 真实用户可能的查询
    real_scenarios = [
        "昨天买的芒果今天发现烂了，怎么退",
        "这个苹果咬了一口发现坏的，能退吗",
        "水果不甜，可以退货不",
        "买错了品种，想换货",
        "收到的香蕉都是青的，怎么办",
        "快递送来的时候就坏了，找谁退",
        "这个质量太差了，要求退款",
        "不满意，全部退掉"
    ]
    
    print("\n测试真实世界场景")
    print("=" * 30)
    
    for scenario in real_scenarios:
        intent = chat_handler.detect_intent(scenario)
        print(f"'{scenario}' -> {intent}")
        
        # 测试完整处理流程
        try:
            response = chat_handler.handle_chat_message(scenario, "test_user")
            response_type = type(response).__name__
            print(f"  处理结果: {response_type}")
            if isinstance(response, str) and len(response) > 100:
                print(f"  回复摘要: {response[:50]}...")
            print()
        except Exception as e:
            print(f"  处理出错: {e}")
            print()

if __name__ == "__main__":
    print("开始测试退货意图识别的边缘情况")
    
    # 运行边缘情况测试
    edge_test_passed = test_edge_cases()
    
    # 运行真实场景测试
    test_real_world_scenarios()
    
    print("\n" + "=" * 60)
    if edge_test_passed:
        print("边缘情况测试全部通过！")
    else:
        print("部分边缘情况测试失败")
    
    print("真实场景测试完成，请检查输出结果")
