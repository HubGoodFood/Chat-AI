#!/usr/bin/env python3
"""
模拟原始问题场景，验证修复效果
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.app.intent.classifier import IntentClassifier
import logging

# 配置日志以模拟原始环境
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

def simulate_chat_request():
    """模拟聊天请求处理"""
    
    print("模拟原始问题场景:")
    print("=" * 50)
    
    # 初始化分类器
    classifier = IntentClassifier()
    
    # 模拟用户输入"草莓"
    user_input = "草莓"
    print(f"用户输入: '{user_input}'")
    
    # 预测意图
    predicted_intent, confidence = classifier.get_prediction_confidence(user_input)
    
    print(f"预测意图: {predicted_intent}")
    print(f"置信度: {confidence:.3f}")
    
    # 检查是否还会被识别为unknown
    if predicted_intent == 'unknown':
        print("[FAIL] 问题仍然存在：草莓被识别为unknown")
        print("这意味着用户查询会回退到LLM处理")
        return False
    elif predicted_intent == 'inquiry_availability':
        print("[OK] 问题已修复：草莓被正确识别为库存查询")
        print("这意味着系统会直接处理库存查询，不需要LLM兜底")
        return True
    else:
        print(f"[WARNING] 意外结果：草莓被识别为{predicted_intent}")
        return False

def test_other_scenarios():
    """测试其他相关场景"""
    
    print("\n测试其他相关场景:")
    print("=" * 50)
    
    classifier = IntentClassifier()
    
    test_cases = [
        ("苹果", "inquiry_availability"),
        ("西瓜", "inquiry_availability"), 
        ("香蕉", "inquiry_availability"),
        ("山楂", "inquiry_availability"),
        ("芭乐", "inquiry_availability"),
        ("草莓多少钱", "inquiry_price_or_buy"),
        ("有草莓吗", "inquiry_availability"),
        ("我要买草莓", "inquiry_price_or_buy")
    ]
    
    all_correct = True
    
    for text, expected in test_cases:
        predicted, confidence = classifier.get_prediction_confidence(text)
        is_correct = predicted == expected
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"{status} '{text}' -> {predicted} (期望: {expected}, 置信度: {confidence:.3f})")
        
        if not is_correct:
            all_correct = False
    
    return all_correct

def main():
    """主函数"""
    
    print("验证草莓意图识别修复效果")
    print("=" * 60)
    
    # 模拟原始问题
    success1 = simulate_chat_request()
    
    # 测试其他场景
    success2 = test_other_scenarios()
    
    print("\n" + "=" * 60)
    print("修复验证结果:")
    
    if success1 and success2:
        print("[OK] 修复成功！")
        print("- 草莓现在被正确识别为inquiry_availability")
        print("- 其他产品名称也能正确识别")
        print("- 不再需要回退到LLM处理")
        print("- 系统响应更快，更准确")
        return True
    else:
        print("[FAIL] 修复不完整，需要进一步调整")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
