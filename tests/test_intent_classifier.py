#!/usr/bin/env python3
"""
意图分类器测试脚本
用于诊断当前意图识别系统的问题
"""

import sys
import os
# Add the project root directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from src.app.intent.classifier import IntentClassifier
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_intent_classifier():
    """测试意图分类器的加载和预测功能"""
    
    print("=" * 60)
    print("意图分类器诊断测试")
    print("=" * 60)
    
    # 1. 测试模型加载
    print("\n1. 测试模型加载...")
    classifier = IntentClassifier()
    
    if classifier.model is None:
        print("[FAIL] 模型加载失败！")
        print("   - 检查模型文件是否存在")
        print("   - 检查模型路径配置")
        return False
    else:
        print("[OK] 模型加载成功")
        print(f"   - 模型路径: {classifier.model_path}")
        print(f"   - 标签映射: {classifier.label_map}")
    
    # 2. 测试训练数据分析
    print("\n2. 分析训练数据...")
    try:
        df = pd.read_csv('data/intent_training_data.csv')
        print(f"   - 总样本数: {len(df)}")
        print(f"   - 意图类别数: {df['intent'].nunique()}")
        print("\n   各类别样本分布:")
        intent_counts = df['intent'].value_counts()
        for intent, count in intent_counts.items():
            print(f"     {intent}: {count} 样本")
        
        # 检查数据平衡性
        min_samples = intent_counts.min()
        max_samples = intent_counts.max()
        balance_ratio = min_samples / max_samples
        print(f"\n   数据平衡性: {balance_ratio:.2f} (1.0为完全平衡)")
        if balance_ratio < 0.5:
            print("   [WARNING] 数据不平衡，可能影响模型性能")

    except Exception as e:
        print(f"[FAIL] 训练数据分析失败: {e}")
        return False
    
    # 3. 测试预测功能
    print("\n3. 测试预测功能...")
    test_cases = [
        ("你好", "greeting"),
        ("苹果多少钱", "inquiry_price_or_buy"),
        ("有什么推荐的", "request_recommendation"),
        ("有苹果吗", "inquiry_availability"),
        ("你们卖什么", "what_do_you_sell"),
        ("退货政策", "inquiry_policy"),
        ("你是谁", "identity_query"),
        ("今天天气真好", "unknown"),
        ("我要买草莓", "inquiry_price_or_buy"),
        ("还有别的水果吗", "inquiry_availability")
    ]
    
    correct_predictions = 0
    total_predictions = len(test_cases)
    
    print("\n   测试用例预测结果:")
    for text, expected in test_cases:
        predicted = classifier.predict(text)
        is_correct = predicted == expected
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"     {status} '{text}' -> 预测: {predicted}, 期望: {expected}")
        if is_correct:
            correct_predictions += 1
    
    accuracy = correct_predictions / total_predictions
    print(f"\n   预测准确率: {accuracy:.2f} ({correct_predictions}/{total_predictions})")
    
    if accuracy < 0.7:
        print("   [WARNING] 准确率较低，建议重新训练模型")
    
    # 4. 检查常见问题
    print("\n4. 检查常见问题...")
    
    # 检查模型文件完整性
    model_files = ['config.json', 'pytorch_model.bin', 'tokenizer_config.json', 'vocab.txt', 'label_map.json']
    missing_files = []
    for file in model_files:
        file_path = os.path.join(classifier.model_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"   [FAIL] 缺少模型文件: {missing_files}")
    else:
        print("   [OK] 模型文件完整")
    
    # 检查标签映射一致性
    if classifier.label_map:
        csv_intents = set(df['intent'].unique())
        model_intents = set(classifier.label_map.keys())
        
        if csv_intents != model_intents:
            print(f"   [WARNING] 标签不一致:")
            print(f"      CSV中的意图: {csv_intents}")
            print(f"      模型中的意图: {model_intents}")
            print(f"      缺少: {csv_intents - model_intents}")
            print(f"      多余: {model_intents - csv_intents}")
        else:
            print("   [OK] 标签映射一致")
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
    return accuracy >= 0.7

if __name__ == "__main__":
    success = test_intent_classifier()
    if not success:
        print("\n建议执行以下步骤修复问题:")
        print("1. 检查并扩充训练数据")
        print("2. 重新训练模型: python src/app/intent/trainer.py")
        print("3. 重新运行此测试脚本")
        sys.exit(1)
    else:
        print("\n[OK] 意图分类器工作正常")
