#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文标点符号意图识别修复效果

这个测试文件专门验证"草莓有？"这类使用中文问号的查询
能否被正确识别为inquiry_availability意图，并正确提取产品名称。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.intent.hybrid_classifier import HybridIntentClassifier
from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager

def test_chinese_punctuation_intent_recognition():
    """测试中文标点符号的意图识别"""
    
    print("测试中文标点符号的意图识别")
    print("=" * 50)
    
    classifier = HybridIntentClassifier()
    
    # 测试用例：使用中文问号的查询
    test_cases = [
        {"query": "草莓有？", "expected_intent": "inquiry_availability"},
        {"query": "苹果有？", "expected_intent": "inquiry_availability"},
        {"query": "西瓜有？", "expected_intent": "inquiry_availability"},
        {"query": "香蕉有？", "expected_intent": "inquiry_availability"},
        {"query": "橙子有？", "expected_intent": "inquiry_availability"},
        {"query": "梨有？", "expected_intent": "inquiry_availability"},
        {"query": "葡萄有？", "expected_intent": "inquiry_availability"},
        {"query": "桃子有？", "expected_intent": "inquiry_availability"},
        {"query": "樱桃有？", "expected_intent": "inquiry_availability"},
        {"query": "芒果有？", "expected_intent": "inquiry_availability"},
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        expected_intent = case["expected_intent"]
        
        predicted_intent, confidence = classifier.get_prediction_confidence(query)
        is_correct = predicted_intent == expected_intent
        status = "[OK]" if is_correct else "[FAIL]"
        
        print(f"{status} 测试 {i}: '{query}' -> {predicted_intent} (置信度: {confidence:.3f})")
        
        if is_correct:
            success_count += 1
        else:
            print(f"      期望: {expected_intent}, 实际: {predicted_intent}")
    
    accuracy = success_count / total_count
    print(f"\n意图识别准确率: {accuracy:.3f} ({success_count}/{total_count})")
    
    return accuracy >= 0.9  # 期望90%以上的准确率

def test_product_name_extraction():
    """测试产品名称提取"""
    
    print("\n测试产品名称提取")
    print("=" * 50)
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试用例：从中文问号查询中提取产品名称
    test_cases = [
        {"query": "草莓有？", "expected_product": "草莓"},
        {"query": "苹果有？", "expected_product": "苹果"},
        {"query": "西瓜有？", "expected_product": "西瓜"},
        {"query": "香蕉有？", "expected_product": "香蕉"},
        {"query": "橙子有？", "expected_product": "橙子"},
        {"query": "梨有？", "expected_product": "梨"},
        {"query": "葡萄有？", "expected_product": "葡萄"},
        {"query": "桃子有？", "expected_product": "桃子"},
        {"query": "樱桃有？", "expected_product": "樱桃"},
        {"query": "芒果有？", "expected_product": "芒果"},
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        expected_product = case["expected_product"]
        
        extracted_product = chat_handler._extract_product_name_from_query(query)
        is_correct = extracted_product == expected_product
        status = "[OK]" if is_correct else "[FAIL]"
        
        print(f"{status} 测试 {i}: '{query}' -> 提取: '{extracted_product}'")
        
        if is_correct:
            success_count += 1
        else:
            print(f"      期望: '{expected_product}', 实际: '{extracted_product}'")
    
    accuracy = success_count / total_count
    print(f"\n产品名称提取准确率: {accuracy:.3f} ({success_count}/{total_count})")
    
    return accuracy >= 0.9  # 期望90%以上的准确率

def test_end_to_end_flow():
    """端到端测试：完整的聊天流程"""
    
    print("\n端到端测试：完整的聊天流程")
    print("=" * 50)
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试用例
    test_queries = [
        "草莓有？",
        "苹果有？",
        "西瓜有？",
        "香蕉有？"
    ]
    
    all_passed = True
    
    for query in test_queries:
        print(f"\n用户输入: '{query}'")
        
        # 预处理
        processed_input, original_input = chat_handler.preprocess_user_input(query, "test_user")
        print(f"预处理后: '{processed_input}'")
        
        # 意图识别
        intent = chat_handler.detect_intent(processed_input)
        print(f"识别意图: {intent}")
        
        # 产品名称提取
        extracted_product = chat_handler._extract_product_name_from_query(processed_input)
        print(f"提取产品: '{extracted_product}'")
        
        # 验证结果
        intent_correct = intent == "inquiry_availability"
        product_correct = extracted_product in query  # 产品名称应该在原查询中
        
        if intent_correct and product_correct:
            print("[OK] 测试通过")
        else:
            print("[FAIL] 测试失败")
            if not intent_correct:
                print(f"  意图识别错误: 期望 inquiry_availability, 实际 {intent}")
            if not product_correct:
                print(f"  产品提取错误: '{extracted_product}' 不在 '{query}' 中")
            all_passed = False
        
        print("-" * 30)
    
    return all_passed

def main():
    """运行所有测试"""
    
    print("中文标点符号意图识别修复验证")
    print("=" * 60)
    
    # 运行测试
    test1_passed = test_chinese_punctuation_intent_recognition()
    test2_passed = test_product_name_extraction()
    test3_passed = test_end_to_end_flow()
    
    # 总结
    print("\n测试总结")
    print("=" * 60)
    print(f"意图识别测试: {'通过' if test1_passed else '失败'}")
    print(f"产品提取测试: {'通过' if test2_passed else '失败'}")
    print(f"端到端测试: {'通过' if test3_passed else '失败'}")
    
    all_tests_passed = test1_passed and test2_passed and test3_passed
    print(f"\n总体结果: {'所有测试通过' if all_tests_passed else '存在测试失败'}")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
