"""
语义增强功能演示
展示中文语序处理、语义匹配和上下文理解的改进效果
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.nlp.chinese_processor import ChineseProcessor
from src.app.nlp.semantic_matcher import SemanticMatcher
from src.app.intent.lightweight_classifier import LightweightIntentClassifier

def demo_chinese_order_processing():
    """演示中文语序处理改进"""
    print("=" * 60)
    print(">> 中文语序处理改进演示")
    print("=" * 60)
    
    intent_classifier = LightweightIntentClassifier(lazy_load=False)
    
    # 原问题和相关变体
    test_cases = [
        "你有什么水果最好吃",      # 原问题
        "什么水果最好吃",          # 简化版
        "有什么好吃的水果",        # 语序变化
        "最好吃的水果是什么",      # 另一种语序
        "推荐一些好吃的水果",      # 明确推荐
        "哪种水果比较甜",          # 类似表达
        "你们有什么特别好的蔬菜",  # 扩展到蔬菜
    ]
    
    print("测试用例及识别结果：")
    print("-" * 60)
    
    for i, text in enumerate(test_cases, 1):
        intent = intent_classifier.predict(text)
        confidence = intent_classifier.get_prediction_confidence(text)[1]
        
        status = "√" if intent == "request_recommendation" else "?"
        print(f"{i}. {text}")
        print(f"   意图: {intent} (置信度: {confidence:.3f}) {status}")
        print()
    
    print("说明：")
    print("√ = 正确识别为推荐意图")
    print("? = 需要进一步优化")

def demo_semantic_matching():
    """演示语义匹配功能"""
    print("=" * 60)
    print(">> 语义匹配功能演示")
    print("=" * 60)
    
    chinese_processor = ChineseProcessor()
    semantic_matcher = SemanticMatcher(chinese_processor)
    
    # 测试语义相似度
    similar_pairs = [
        ("你有什么水果最好吃", "什么水果最好吃"),
        ("推荐一些好的蔬菜", "有什么好的蔬菜推荐"),
        ("苹果多少钱", "苹果价格"),
        ("有没有草莓", "卖不卖草莓"),
    ]
    
    print("语义相似度计算：")
    print("-" * 60)
    
    for text1, text2 in similar_pairs:
        similarity = semantic_matcher.calculate_semantic_similarity(text1, text2)
        print(f"文本1: {text1}")
        print(f"文本2: {text2}")
        print(f"相似度: {similarity:.3f}")
        print("-" * 30)

def demo_feature_extraction():
    """演示特征提取功能"""
    print("=" * 60)
    print(">> 语义特征提取演示")
    print("=" * 60)
    
    chinese_processor = ChineseProcessor()
    
    test_text = "你有什么水果最好吃"
    
    print(f"分析文本: {test_text}")
    print("-" * 60)
    
    # 关键词提取
    keywords = chinese_processor.extract_keywords(test_text)
    print(f"关键词: {keywords}")
    
    # 语义特征提取
    features = chinese_processor.extract_intent_features(test_text)
    print(f"疑问词: {features.get('question_words', [])}")
    print(f"修饰词: {features.get('modifiers', [])}")
    print(f"类别词: {features.get('categories', [])}")
    print(f"情感倾向: {features.get('sentiment', 'neutral')}")
    
    # 语义模式分析
    patterns = chinese_processor.analyze_semantic_pattern(test_text)
    print(f"语义模式: {list(patterns.keys())}")

def demo_template_matching():
    """演示模板匹配功能"""
    print("=" * 60)
    print(">> 语义模板匹配演示")
    print("=" * 60)
    
    chinese_processor = ChineseProcessor()
    semantic_matcher = SemanticMatcher(chinese_processor)
    
    test_cases = [
        "你有什么水果最好吃",
        "苹果多少钱",
        "有没有草莓",
        "推荐一些好的蔬菜"
    ]
    
    for text in test_cases:
        matches = semantic_matcher.match_intent_template(text)
        print(f"文本: {text}")
        
        if matches:
            for intent, match_info in matches.items():
                score = match_info['score']
                groups = match_info['groups']
                print(f"  匹配意图: {intent} (分数: {score:.3f})")
                print(f"  提取组件: {groups}")
        else:
            print("  无匹配模板")
        print("-" * 30)

def demo_improvement_comparison():
    """演示改进前后对比"""
    print("=" * 60)
    print(">> 改进效果对比")
    print("=" * 60)
    
    intent_classifier = LightweightIntentClassifier(lazy_load=False)
    
    # 重点测试原问题
    original_problem = "你有什么水果最好吃"
    
    print(f"原问题: {original_problem}")
    print("-" * 60)
    
    # 当前识别结果
    current_intent = intent_classifier.predict(original_problem)
    current_confidence = intent_classifier.get_prediction_confidence(original_problem)[1]
    
    print(f"当前识别结果:")
    print(f"  意图: {current_intent}")
    print(f"  置信度: {current_confidence:.3f}")
    print(f"  状态: {'√ 正确' if current_intent == 'request_recommendation' else 'X 错误'}")
    
    print("\n改进说明:")
    print("1. 新增了复杂语序的正则表达式模式")
    print("2. 实现了语义模板匹配机制")
    print("3. 增强了中文分词和特征提取")
    print("4. 添加了多层意图识别策略")

def main():
    """主演示函数"""
    print(">> Chat AI 语义增强功能演示")
    print("=" * 60)
    print("本演示展示了针对中文语序处理的优化改进")
    print("重点解决：'你有什么水果最好吃' 类似表达的意图识别")
    print()
    
    try:
        # 1. 中文语序处理演示
        demo_chinese_order_processing()
        print()
        
        # 2. 语义匹配演示
        demo_semantic_matching()
        print()
        
        # 3. 特征提取演示
        demo_feature_extraction()
        print()
        
        # 4. 模板匹配演示
        demo_template_matching()
        print()
        
        # 5. 改进对比演示
        demo_improvement_comparison()
        print()
        
        print("=" * 60)
        print("√ 演示完成！语义增强功能运行正常。")
        print("=" * 60)
        
    except Exception as e:
        print(f"X 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
