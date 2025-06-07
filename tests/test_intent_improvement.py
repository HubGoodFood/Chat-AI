#!/usr/bin/env python3
"""
测试意图识别改进效果
验证口语化表达的识别准确性
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.intent.hybrid_classifier import HybridIntentClassifier
from app.chat.handler import ChatHandler
from app.products.manager import ProductManager
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_intent_recognition():
    """测试意图识别改进效果"""
    
    print("测试意图识别改进效果")
    print("=" * 50)
    
    # 初始化分类器
    classifier = HybridIntentClassifier()
    
    # 测试用例：口语化询问可用性的表达
    test_cases = [
        # 原始问题
        ("草莓卖不？", "inquiry_availability"),
        ("苹果有不？", "inquiry_availability"),
        
        # 其他口语化变体
        ("西瓜卖不", "inquiry_availability"),
        ("香蕉有不", "inquiry_availability"),
        ("草莓卖吗", "inquiry_availability"),
        ("苹果有吗", "inquiry_availability"),
        ("西瓜卖不卖", "inquiry_availability"),
        ("香蕉有没有", "inquiry_availability"),
        ("草莓有不有", "inquiry_availability"),
        
        # 确保原有功能不受影响
        ("有草莓吗", "inquiry_availability"),
        ("有没有苹果", "inquiry_availability"),
        ("草莓", "inquiry_availability"),
        ("苹果多少钱", "inquiry_price_or_buy"),
        ("你好", "greeting"),
        ("你是谁", "identity_query"),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for query, expected_intent in test_cases:
        predicted_intent = classifier.predict(query)
        is_correct = predicted_intent == expected_intent
        status = "[OK]" if is_correct else "[FAIL]"
        
        print(f"{status} '{query}' -> 预测: {predicted_intent} (期望: {expected_intent})")
        
        if is_correct:
            success_count += 1
        else:
            # 获取详细信息
            confidence = classifier.get_prediction_confidence(query)
            print(f"      详细: 置信度={confidence[1]:.3f}")
    
    accuracy = success_count / total_count
    print(f"\n意图识别准确率: {accuracy:.3f} ({success_count}/{total_count})")
    
    return accuracy >= 0.9

def test_product_extraction():
    """测试产品名称提取改进效果"""
    
    print("\n测试产品名称提取改进效果")
    print("=" * 50)
    
    # 初始化ChatHandler
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试用例：从口语化查询中提取产品名称
    test_cases = [
        ("草莓卖不？", "草莓"),
        ("苹果有不？", "苹果"),
        ("西瓜卖不", "西瓜"),
        ("香蕉有不", "香蕉"),
        ("草莓卖吗", "草莓"),
        ("苹果有吗", "苹果"),
        ("西瓜卖不卖", "西瓜"),
        ("香蕉有没有", "香蕉"),
        ("草莓有不有", "草莓"),
        ("卖不草莓", "草莓"),  # 测试前置模式
        ("有不苹果", "苹果"),  # 测试前置模式
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for query, expected_product in test_cases:
        extracted_product = chat_handler._extract_product_name_from_query(query)
        is_correct = extracted_product == expected_product
        status = "[OK]" if is_correct else "[FAIL]"
        
        print(f"{status} '{query}' -> 提取: '{extracted_product}' (期望: '{expected_product}')")
        
        if is_correct:
            success_count += 1
    
    accuracy = success_count / total_count
    print(f"\n产品名称提取准确率: {accuracy:.3f} ({success_count}/{total_count})")
    
    return accuracy >= 0.8

def test_end_to_end():
    """端到端测试：模拟完整的聊天流程"""
    
    print("\n端到端测试")
    print("=" * 50)
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试用例
    test_queries = [
        "草莓卖不？",
        "苹果有不？",
        "西瓜卖不",
        "有没有草莓",
    ]
    
    for query in test_queries:
        print(f"\n用户输入: '{query}'")
        
        # 预处理
        processed_input, original_input = chat_handler.preprocess_user_input(query, "test_user")
        print(f"预处理后: '{processed_input}'")
        
        # 意图识别
        intent = chat_handler.detect_intent(processed_input)
        print(f"识别意图: {intent}")
        
        # 产品名称提取
        if intent in ['inquiry_availability', 'inquiry_price_or_buy']:
            extracted_product = chat_handler._extract_product_name_from_query(processed_input)
            print(f"提取产品: '{extracted_product}'")
        
        print("-" * 30)

if __name__ == "__main__":
    print("开始测试意图识别改进效果...\n")
    
    # 运行测试
    intent_success = test_intent_recognition()
    extraction_success = test_product_extraction()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"意图识别测试: {'通过' if intent_success else '失败'}")
    print(f"产品提取测试: {'通过' if extraction_success else '失败'}")
    
    if intent_success and extraction_success:
        print("\n✅ 所有测试通过！口语化表达识别改进成功。")
        
        # 运行端到端测试
        test_end_to_end()
    else:
        print("\n❌ 部分测试失败，需要进一步调试。")
    
    print("\n测试完成。")
