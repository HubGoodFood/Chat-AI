#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试意图识别修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.intent.hybrid_classifier import HybridIntentClassifier
from src.app.intent.classifier import IntentClassifier

def test_intent_classifiers():
    """测试不同的意图分类器"""
    
    print("=== 测试意图分类器 ===")
    print()
    
    # 测试查询
    test_queries = [
        "蘑菇",
        "玉米", 
        "蛋",
        "鸡",
        "有蘑菇吗",
        "玉米有吗"
    ]
    
    print("1. 测试混合分类器 (HybridIntentClassifier)")
    print("-" * 50)
    
    try:
        hybrid_classifier = HybridIntentClassifier()
        
        for query in test_queries:
            intent, confidence = hybrid_classifier.get_prediction_confidence(query)
            print(f"'{query}' -> {intent} (置信度: {confidence:.3f})")
            
    except Exception as e:
        print(f"混合分类器出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. 测试BERT分类器 (IntentClassifier)")
    print("-" * 50)
    
    try:
        bert_classifier = IntentClassifier()
        
        for query in test_queries:
            if bert_classifier.model:
                intent = bert_classifier.predict(query)
                print(f"'{query}' -> {intent}")
            else:
                print(f"BERT模型未加载")
                break
                
    except Exception as e:
        print(f"BERT分类器出错: {e}")
        import traceback
        traceback.print_exc()

def test_retrain_hybrid():
    """重新训练混合分类器"""
    
    print("\n=== 重新训练混合分类器 ===")
    print()
    
    try:
        # 删除旧的模型文件，强制重新训练
        import shutil
        model_dir = "src/models/hybrid_intent_model"
        if os.path.exists(model_dir):
            shutil.rmtree(model_dir)
            print(f"已删除旧模型目录: {model_dir}")
        
        # 创建新的分类器，这会触发重新训练
        print("重新训练混合分类器...")
        hybrid_classifier = HybridIntentClassifier()
        
        # 测试新模型
        test_queries = ["蘑菇", "玉米", "蛋", "鸡"]
        
        print("\n重新训练后的结果:")
        for query in test_queries:
            intent, confidence = hybrid_classifier.get_prediction_confidence(query)
            print(f"'{query}' -> {intent} (置信度: {confidence:.3f})")
            
    except Exception as e:
        print(f"重新训练出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intent_classifiers()
    test_retrain_hybrid()
