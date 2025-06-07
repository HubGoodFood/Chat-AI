#!/usr/bin/env python3
"""
测试单独产品名称的意图识别
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.app.intent.hybrid_classifier import HybridIntentClassifier

def test_single_product_names():
    """测试单独产品名称的识别"""
    
    classifier = HybridIntentClassifier()
    
    # 测试各种单独产品名称
    test_products = [
        "草莓",
        "苹果", 
        "西瓜",
        "香蕉",
        "橙子",
        "梨",
        "葡萄",
        "桃子",
        "樱桃",
        "芒果",
        "山楂",
        "芭乐",
        "柠檬",
        "火龙果",
        "猕猴桃",
        "荔枝",
        "龙眼",
        "榴莲",
        "菠萝",
        "椰子"
    ]
    
    print("单独产品名称意图识别测试:")
    print("=" * 50)
    
    correct_count = 0
    total_count = len(test_products)
    
    for product in test_products:
        intent, confidence = classifier.get_prediction_confidence(product)
        is_correct = intent == 'inquiry_availability'
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"{status} '{product}' -> {intent} (置信度: {confidence:.3f})")
        if is_correct:
            correct_count += 1
    
    accuracy = correct_count / total_count
    print(f"\n准确率: {accuracy:.3f} ({correct_count}/{total_count})")
    
    if accuracy >= 0.9:
        print("[OK] 单独产品名称识别效果良好")
        return True
    else:
        print("[WARNING] 单独产品名称识别需要改进")
        return False

def test_mixed_cases():
    """测试混合情况"""
    
    classifier = HybridIntentClassifier()
    
    mixed_cases = [
        ("草莓", "inquiry_availability"),
        ("草莓多少钱", "inquiry_price_or_buy"),
        ("有草莓吗", "inquiry_availability"),
        ("我要买草莓", "inquiry_price_or_buy"),
        ("苹果", "inquiry_availability"),
        ("苹果价格", "inquiry_price_or_buy"),
        ("你好", "greeting"),
        ("推荐点水果", "request_recommendation"),
        ("你们卖什么", "what_do_you_sell")
    ]
    
    print("\n混合情况测试:")
    print("=" * 50)
    
    correct_count = 0
    total_count = len(mixed_cases)
    
    for text, expected in mixed_cases:
        intent, confidence = classifier.get_prediction_confidence(text)
        is_correct = intent == expected
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"{status} '{text}' -> 预测: {intent}, 期望: {expected} (置信度: {confidence:.3f})")
        if is_correct:
            correct_count += 1
    
    accuracy = correct_count / total_count
    print(f"\n混合情况准确率: {accuracy:.3f} ({correct_count}/{total_count})")
    
    return accuracy >= 0.8

if __name__ == "__main__":
    success1 = test_single_product_names()
    success2 = test_mixed_cases()
    
    if success1 and success2:
        print("\n[OK] 所有测试通过，修复成功！")
        sys.exit(0)
    else:
        print("\n[FAIL] 部分测试失败，需要进一步调整")
        sys.exit(1)
