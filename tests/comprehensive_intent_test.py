#!/usr/bin/env python3
"""
全面的意图识别测试脚本
测试改进后的混合意图分类器
"""

import sys
import os
# Add the project root directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from src.app.intent.classifier import IntentClassifier
from src.app.intent.hybrid_classifier import HybridIntentClassifier
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_comprehensive_intent_classification():
    """全面测试意图分类器"""
    
    print("=" * 80)
    print("全面意图分类器测试")
    print("=" * 80)
    
    # 1. 测试混合分类器
    print("\n1. 测试混合分类器...")
    try:
        hybrid_classifier = HybridIntentClassifier()
        print("[OK] 混合分类器初始化成功")
    except Exception as e:
        print(f"[FAIL] 混合分类器初始化失败: {e}")
        return False
    
    # 2. 测试主分类器
    print("\n2. 测试主分类器...")
    try:
        main_classifier = IntentClassifier()
        print("[OK] 主分类器初始化成功")
    except Exception as e:
        print(f"[FAIL] 主分类器初始化失败: {e}")
        return False
    
    # 3. 扩展测试用例
    test_cases = [
        # 问候类
        ("你好", "greeting"),
        ("您好", "greeting"),
        ("hi", "greeting"),
        ("在吗", "greeting"),
        ("早上好", "greeting"),
        
        # 身份查询类
        ("你是谁", "identity_query"),
        ("你叫什么名字", "identity_query"),
        ("你是机器人吗", "identity_query"),
        ("介绍一下你自己", "identity_query"),
        
        # 产品查询类
        ("你们卖什么", "what_do_you_sell"),
        ("有什么产品", "what_do_you_sell"),
        ("商品列表", "what_do_you_sell"),
        ("都有哪些东西", "what_do_you_sell"),
        
        # 推荐类
        ("有什么推荐的", "request_recommendation"),
        ("推荐点好吃的", "request_recommendation"),
        ("什么比较好", "request_recommendation"),
        ("当季有什么好的", "request_recommendation"),
        
        # 库存查询类
        ("有苹果吗", "inquiry_availability"),
        ("有没有草莓", "inquiry_availability"),
        ("还有别的水果吗", "inquiry_availability"),
        ("西瓜还有吗", "inquiry_availability"),
        
        # 价格/购买类
        ("苹果多少钱", "inquiry_price_or_buy"),
        ("这个怎么卖", "inquiry_price_or_buy"),
        ("我要买草莓", "inquiry_price_or_buy"),
        ("来一斤苹果", "inquiry_price_or_buy"),
        ("价格是多少", "inquiry_price_or_buy"),
        
        # 政策查询类
        ("退货政策", "inquiry_policy"),
        ("怎么退款", "inquiry_policy"),
        ("配送时间", "inquiry_policy"),
        ("运费怎么算", "inquiry_policy"),
        
        # 未知类
        ("今天天气真好", "unknown"),
        ("我想聊天", "unknown"),
        ("测试一下", "unknown"),
        ("随便说说", "unknown"),
    ]
    
    print(f"\n3. 执行 {len(test_cases)} 个测试用例...")
    
    # 测试混合分类器
    print("\n--- 混合分类器结果 ---")
    hybrid_correct = 0
    hybrid_total = len(test_cases)
    
    for text, expected in test_cases:
        predicted, confidence = hybrid_classifier.get_prediction_confidence(text)
        is_correct = predicted == expected
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"{status} '{text}' -> 预测: {predicted}, 期望: {expected}, 置信度: {confidence:.3f}")
        if is_correct:
            hybrid_correct += 1
    
    hybrid_accuracy = hybrid_correct / hybrid_total
    print(f"\n混合分类器准确率: {hybrid_accuracy:.3f} ({hybrid_correct}/{hybrid_total})")
    
    # 测试主分类器
    print("\n--- 主分类器结果 ---")
    main_correct = 0
    main_total = len(test_cases)
    
    for text, expected in test_cases:
        predicted, confidence = main_classifier.get_prediction_confidence(text)
        is_correct = predicted == expected
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"{status} '{text}' -> 预测: {predicted}, 期望: {expected}, 置信度: {confidence:.3f}")
        if is_correct:
            main_correct += 1
    
    main_accuracy = main_correct / main_total
    print(f"\n主分类器准确率: {main_accuracy:.3f} ({main_correct}/{main_total})")
    
    # 4. 性能分析
    print("\n4. 性能分析...")
    
    # 按意图类别分析
    intent_stats = {}
    for text, expected in test_cases:
        if expected not in intent_stats:
            intent_stats[expected] = {'total': 0, 'correct': 0}
        intent_stats[expected]['total'] += 1
        
        predicted, _ = main_classifier.get_prediction_confidence(text)
        if predicted == expected:
            intent_stats[expected]['correct'] += 1
    
    print("\n各意图类别准确率:")
    for intent, stats in intent_stats.items():
        accuracy = stats['correct'] / stats['total']
        print(f"  {intent}: {accuracy:.3f} ({stats['correct']}/{stats['total']})")
    
    # 5. 错误分析
    print("\n5. 错误分析...")
    errors = []
    for text, expected in test_cases:
        predicted, confidence = main_classifier.get_prediction_confidence(text)
        if predicted != expected:
            errors.append({
                'text': text,
                'expected': expected,
                'predicted': predicted,
                'confidence': confidence
            })
    
    if errors:
        print(f"发现 {len(errors)} 个错误:")
        for error in errors[:5]:  # 只显示前5个错误
            print(f"  '{error['text']}' -> 预测: {error['predicted']}, 期望: {error['expected']}")
        
        # 分析错误模式
        error_patterns = {}
        for error in errors:
            pattern = f"{error['expected']} -> {error['predicted']}"
            error_patterns[pattern] = error_patterns.get(pattern, 0) + 1
        
        print("\n错误模式分析:")
        for pattern, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pattern}: {count} 次")
    
    # 6. 建议
    print("\n6. 改进建议...")
    if main_accuracy >= 0.8:
        print("[OK] 意图分类器性能良好")
    elif main_accuracy >= 0.6:
        print("[WARNING] 意图分类器性能一般，建议:")
        print("  - 增加训练数据")
        print("  - 优化规则匹配")
        print("  - 调整关键词模式")
    else:
        print("[FAIL] 意图分类器性能较差，建议:")
        print("  - 重新设计规则")
        print("  - 大幅增加训练数据")
        print("  - 考虑使用更复杂的模型")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    
    return main_accuracy >= 0.7

def test_edge_cases():
    """测试边缘情况"""
    print("\n7. 边缘情况测试...")
    
    classifier = IntentClassifier()
    
    edge_cases = [
        "",  # 空字符串
        "   ",  # 只有空格
        "？？？",  # 只有标点
        "a",  # 单个字符
        "你好你好你好你好你好" * 10,  # 很长的重复文本
        "苹果苹果苹果多少钱钱钱",  # 重复词汇
        "我想要买一些新鲜的有机苹果请问价格如何",  # 很长的句子
    ]
    
    for text in edge_cases:
        try:
            predicted, confidence = classifier.get_prediction_confidence(text)
            print(f"  '{text[:20]}...' -> {predicted} (置信度: {confidence:.3f})")
        except Exception as e:
            print(f"  '{text[:20]}...' -> ERROR: {e}")

if __name__ == "__main__":
    success = test_comprehensive_intent_classification()
    test_edge_cases()
    
    if success:
        print("\n[OK] 意图分类器测试通过")
        sys.exit(0)
    else:
        print("\n[FAIL] 意图分类器需要进一步改进")
        sys.exit(1)
