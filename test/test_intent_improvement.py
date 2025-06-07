#!/usr/bin/env python3
"""
测试中文意图识别改进效果
验证不同语序的推荐意图是否能被正确识别
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app.intent.lightweight_classifier import LightweightIntentClassifier
from src.app.intent.hybrid_classifier import HybridIntentClassifier

def test_recommendation_intent_recognition():
    """测试推荐意图识别的改进效果"""
    
    # 初始化分类器
    lightweight_classifier = LightweightIntentClassifier(lazy_load=False)
    hybrid_classifier = HybridIntentClassifier(lazy_load=False)
    
    # 测试用例：各种语序的推荐意图表达
    test_cases = [
        # 原问题：这些应该被识别为 request_recommendation
        ("你有什么水果最好吃", "request_recommendation"),
        ("什么水果最好吃", "request_recommendation"),
        ("有什么最好吃的水果", "request_recommendation"),
        ("最好吃的水果是什么", "request_recommendation"),
        ("哪种水果最好吃", "request_recommendation"),
        ("什么水果比较好吃", "request_recommendation"),
        ("有什么比较好的水果", "request_recommendation"),
        ("什么水果最值得买", "request_recommendation"),
        ("最值得买的水果是什么", "request_recommendation"),
        ("什么水果最新鲜", "request_recommendation"),
        ("最新鲜的水果有什么", "request_recommendation"),
        ("什么水果最棒", "request_recommendation"),
        ("最棒的水果是什么", "request_recommendation"),
        ("哪个水果最好", "request_recommendation"),
        ("什么水果不错", "request_recommendation"),
        ("有什么不错的水果", "request_recommendation"),
        ("给我推荐点水果", "request_recommendation"),
        ("帮我推荐些水果", "request_recommendation"),
        ("介绍点好吃的水果", "request_recommendation"),
        ("来点好吃的水果", "request_recommendation"),
        
        # 原本能正确识别的（确保不受影响）
        ("你有什么好吃的水果", "request_recommendation"),
        ("推荐点好吃的", "request_recommendation"),
        ("有什么推荐的吗", "request_recommendation"),
        ("什么比较好", "request_recommendation"),
        ("有什么特色", "request_recommendation"),
        ("当季有什么好的", "request_recommendation"),
        
        # 其他意图（确保不受影响）
        ("有苹果吗", "inquiry_availability"),
        ("苹果多少钱", "inquiry_price_or_buy"),
        ("你好", "greeting"),
        ("你们的退货政策是什么", "inquiry_policy"),
        ("我要退货", "refund_request"),
    ]
    
    print("测试中文意图识别改进效果")
    print("=" * 60)
    
    # 测试轻量级分类器
    print("\n轻量级分类器测试结果：")
    print("-" * 40)
    lightweight_correct = 0
    lightweight_total = len(test_cases)
    
    for text, expected in test_cases:
        predicted = lightweight_classifier.predict(text)
        confidence = lightweight_classifier.get_prediction_confidence(text)[1]
        is_correct = predicted == expected
        
        if is_correct:
            lightweight_correct += 1
            status = "[OK]"
        else:
            status = "[FAIL]"
        
        print(f"{status} '{text}' -> {predicted} (期望: {expected}) [置信度: {confidence:.3f}]")
    
    lightweight_accuracy = lightweight_correct / lightweight_total
    print(f"\n轻量级分类器准确率: {lightweight_accuracy:.2%} ({lightweight_correct}/{lightweight_total})")
    
    # 测试混合分类器
    print("\n混合分类器测试结果：")
    print("-" * 40)
    hybrid_correct = 0
    hybrid_total = len(test_cases)
    
    for text, expected in test_cases:
        predicted = hybrid_classifier.predict(text)
        confidence = hybrid_classifier.get_prediction_confidence(text)[1]
        is_correct = predicted == expected
        
        if is_correct:
            hybrid_correct += 1
            status = "[OK]"
        else:
            status = "[FAIL]"
        
        print(f"{status} '{text}' -> {predicted} (期望: {expected}) [置信度: {confidence:.3f}]")
    
    hybrid_accuracy = hybrid_correct / hybrid_total
    print(f"\n混合分类器准确率: {hybrid_accuracy:.2%} ({hybrid_correct}/{hybrid_total})")
    
    # 总结
    print("\n测试总结：")
    print("=" * 60)
    print(f"轻量级分类器准确率: {lightweight_accuracy:.2%}")
    print(f"混合分类器准确率: {hybrid_accuracy:.2%}")
    
    if lightweight_accuracy >= 0.9 and hybrid_accuracy >= 0.9:
        print("改进效果良好！意图识别准确率达到预期目标。")
    elif lightweight_accuracy >= 0.8 or hybrid_accuracy >= 0.8:
        print("改进有效果，但仍有优化空间。")
    else:
        print("改进效果不理想，需要进一步调整。")

def test_specific_problem_case():
    """专门测试原问题中的具体案例"""
    
    print("\n专项测试：原问题案例")
    print("=" * 40)
    
    lightweight_classifier = LightweightIntentClassifier(lazy_load=False)
    
    # 原问题中的具体案例
    problem_cases = [
        ("你有什么水果最好吃", "request_recommendation"),
        ("你有什么好吃的水果", "request_recommendation"),  # 这个原本能识别
    ]
    
    for text, expected in problem_cases:
        predicted = lightweight_classifier.predict(text)
        confidence = lightweight_classifier.get_prediction_confidence(text)[1]
        is_correct = predicted == expected
        
        if is_correct:
            status = "[OK] 修复成功"
        else:
            status = "[FAIL] 仍有问题"
        
        print(f"{status}: '{text}' -> {predicted} (期望: {expected}) [置信度: {confidence:.3f}]")

if __name__ == "__main__":
    try:
        test_recommendation_intent_recognition()
        test_specific_problem_case()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
