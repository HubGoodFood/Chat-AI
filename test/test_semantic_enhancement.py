"""
测试语义增强功能
验证中文语序处理、语义匹配和上下文理解的改进
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.app.nlp.chinese_processor import ChineseProcessor
from src.app.nlp.semantic_matcher import SemanticMatcher
from src.core.context_manager import EnhancedContextManager
from src.app.intent.lightweight_classifier import LightweightIntentClassifier

class TestSemanticEnhancement(unittest.TestCase):
    """测试语义增强功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.chinese_processor = ChineseProcessor()
        self.semantic_matcher = SemanticMatcher(self.chinese_processor)
        self.context_manager = EnhancedContextManager()
        self.intent_classifier = LightweightIntentClassifier(lazy_load=False)
    
    def test_chinese_word_segmentation(self):
        """测试中文分词功能"""
        print("\n=== 测试中文分词功能 ===")
        
        test_cases = [
            "你有什么水果最好吃",
            "推荐一些新鲜的蔬菜",
            "苹果多少钱一斤",
            "有没有当季的水果"
        ]
        
        for text in test_cases:
            keywords = self.chinese_processor.extract_keywords(text)
            pos_keywords = self.chinese_processor.extract_keywords(text, with_pos=True)
            print(f"文本: {text}")
            print(f"关键词: {keywords}")
            print(f"词性关键词: {pos_keywords}")
            print("-" * 50)
    
    def test_semantic_pattern_matching(self):
        """测试语义模式匹配"""
        print("\n=== 测试语义模式匹配 ===")
        
        test_cases = [
            "你有什么水果最好吃",  # 原问题案例
            "什么水果最好吃",
            "有什么好吃的水果",
            "推荐一些好的蔬菜",
            "哪种苹果比较甜",
            "苹果多少钱",
            "有没有草莓",
            "卖不卖香蕉"
        ]
        
        for text in test_cases:
            patterns = self.chinese_processor.analyze_semantic_pattern(text)
            template_matches = self.semantic_matcher.match_intent_template(text)
            print(f"文本: {text}")
            print(f"语义模式: {patterns}")
            print(f"模板匹配: {template_matches}")
            print("-" * 50)
    
    def test_intent_classification_improvement(self):
        """测试意图识别改进"""
        print("\n=== 测试意图识别改进 ===")
        
        test_cases = [
            ("你有什么水果最好吃", "request_recommendation"),
            ("什么水果最好吃", "request_recommendation"),
            ("有什么好吃的水果", "request_recommendation"),
            ("推荐一些好的蔬菜", "request_recommendation"),
            ("哪种苹果比较甜", "request_recommendation"),
            ("苹果多少钱", "inquiry_price_or_buy"),
            ("有没有草莓", "inquiry_availability"),
            ("卖不卖香蕉", "inquiry_availability"),
            ("你好", "greeting"),
            ("配送政策是什么", "inquiry_policy")
        ]
        
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        for text, expected_intent in test_cases:
            predicted_intent = self.intent_classifier.predict(text)
            is_correct = predicted_intent == expected_intent
            if is_correct:
                correct_predictions += 1
            
            print(f"文本: {text}")
            print(f"预期意图: {expected_intent}")
            print(f"预测意图: {predicted_intent}")
            print(f"正确: {'√' if is_correct else 'X'}")
            print("-" * 50)
        
        accuracy = correct_predictions / total_predictions
        print(f"\n意图识别准确率: {accuracy:.2%} ({correct_predictions}/{total_predictions})")
        
        # 断言准确率应该大于80%
        self.assertGreater(accuracy, 0.8, f"意图识别准确率 {accuracy:.2%} 低于期望的80%")
    
    def test_semantic_similarity(self):
        """测试语义相似度计算"""
        print("\n=== 测试语义相似度计算 ===")
        
        test_pairs = [
            ("你有什么水果最好吃", "什么水果最好吃"),
            ("推荐一些好的蔬菜", "有什么好的蔬菜推荐"),
            ("苹果多少钱", "苹果价格"),
            ("有没有草莓", "卖不卖草莓"),
            ("你好", "您好")
        ]
        
        for text1, text2 in test_pairs:
            similarity = self.semantic_matcher.calculate_semantic_similarity(text1, text2)
            print(f"文本1: {text1}")
            print(f"文本2: {text2}")
            print(f"相似度: {similarity:.3f}")
            print("-" * 50)
    
    def test_context_management(self):
        """测试上下文管理"""
        print("\n=== 测试上下文管理 ===")
        
        user_id = "test_user"
        
        # 模拟对话序列
        dialogue_sequence = [
            ("你有什么水果", "query"),
            ("苹果", "product"),
            ("多少钱", "query"),
            ("还有其他推荐吗", "query")
        ]
        
        for content, item_type in dialogue_sequence:
            self.context_manager.update_context(
                user_id=user_id,
                content=content,
                item_type=item_type,
                metadata={"timestamp": "2024-01-01"}
            )
        
        # 获取上下文摘要
        context_summary = self.context_manager.get_context_summary(user_id)
        print(f"上下文摘要: {context_summary}")
        
        # 获取相关上下文
        relevant_context = self.context_manager.get_relevant_context(
            user_id=user_id,
            current_query="苹果怎么样",
            max_items=5
        )
        print(f"相关上下文项数量: {len(relevant_context)}")
        for item in relevant_context:
            print(f"  - {item.content} ({item.item_type})")
    
    def test_complex_chinese_expressions(self):
        """测试复杂中文表达的处理"""
        print("\n=== 测试复杂中文表达处理 ===")
        
        complex_expressions = [
            "你们这里有什么水果是最好吃的",
            "能不能推荐一些比较新鲜的蔬菜",
            "哪种苹果口感最好价格也不贵",
            "有没有什么特别甜的水果推荐",
            "你们卖的草莓新鲜吗多少钱一斤"
        ]
        
        for text in complex_expressions:
            # 提取语义特征
            features = self.chinese_processor.extract_intent_features(text)
            
            # 意图识别
            intent = self.intent_classifier.predict(text)
            
            print(f"文本: {text}")
            print(f"关键词: {features.get('keywords', [])}")
            print(f"疑问词: {features.get('question_words', [])}")
            print(f"修饰词: {features.get('modifiers', [])}")
            print(f"类别词: {features.get('categories', [])}")
            print(f"预测意图: {intent}")
            print("-" * 50)

def run_semantic_enhancement_tests():
    """运行语义增强测试"""
    print("开始语义增强功能测试...")
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestSemanticEnhancement)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n√ 所有语义增强测试通过！")
        return True
    else:
        print(f"\nX 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        return False

if __name__ == "__main__":
    success = run_semantic_enhancement_tests()
    sys.exit(0 if success else 1)
