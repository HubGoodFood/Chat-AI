"""
高级功能测试
测试NLP引擎、深度上下文理解和个性化学习功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import time
import numpy as np
from unittest.mock import Mock, patch

# 导入要测试的组件
from src.app.nlp.advanced_nlp_engine import AdvancedNLPEngine
from src.core.deep_context_engine import DeepContextEngine
from src.app.personalization.learning_engine import PersonalizationEngine
from src.core.advanced_chat_engine import AdvancedChatEngine

class TestAdvancedNLPEngine(unittest.TestCase):
    """测试高级NLP引擎"""
    
    def setUp(self):
        """设置测试环境"""
        # 使用mock避免实际加载大模型
        with patch('src.app.nlp.advanced_nlp_engine.SentenceTransformer'):
            self.nlp_engine = AdvancedNLPEngine(lazy_load=True)
            # 模拟模型已加载
            self.nlp_engine.model_loaded = True
            self.nlp_engine.sentence_model = Mock()
    
    def test_text_encoding(self):
        """测试文本编码功能"""
        print("\n=== 测试文本编码功能 ===")
        
        # 模拟编码结果
        mock_vector = np.random.rand(384)
        self.nlp_engine.sentence_model.encode.return_value = mock_vector
        
        text = "你有什么水果最好吃"
        vector = self.nlp_engine.encode_text(text)
        
        self.assertIsInstance(vector, np.ndarray)
        self.assertEqual(len(vector), 384)
        print(f"文本编码成功: {text} -> 向量维度 {len(vector)}")
    
    def test_semantic_similarity(self):
        """测试语义相似度计算"""
        print("\n=== 测试语义相似度计算 ===")
        
        # 模拟相似的向量
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0.8, 0.6, 0])
        
        self.nlp_engine.sentence_model.encode.side_effect = [vec1, vec2]
        
        similarity = self.nlp_engine.calculate_semantic_similarity(
            "你有什么水果最好吃", 
            "什么水果最好吃"
        )
        
        self.assertGreater(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        print(f"语义相似度计算成功: {similarity:.3f}")
    
    def test_keyword_extraction(self):
        """测试关键词提取"""
        print("\n=== 测试关键词提取 ===")
        
        text = "你有什么水果最好吃"
        keywords = self.nlp_engine.extract_keywords(text)
        
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        print(f"关键词提取成功: {keywords}")
    
    def test_performance_stats(self):
        """测试性能统计"""
        print("\n=== 测试性能统计 ===")
        
        stats = self.nlp_engine.get_performance_stats()
        
        self.assertIn('model_loaded', stats)
        self.assertIn('cache_hit_rate', stats)
        print(f"性能统计获取成功: {stats}")

class TestDeepContextEngine(unittest.TestCase):
    """测试深度上下文引擎"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建mock NLP引擎
        self.mock_nlp = Mock()
        self.mock_nlp.encode_text.return_value = np.random.rand(384)
        
        self.context_engine = DeepContextEngine(nlp_engine=self.mock_nlp)
    
    def test_session_creation(self):
        """测试会话创建"""
        print("\n=== 测试会话创建 ===")
        
        user_id = "test_user"
        session = self.context_engine.get_user_session(user_id)
        
        self.assertIn('context_graph', session)
        self.assertIn('entity_states', session)
        self.assertIn('dialogue_state', session)
        print(f"会话创建成功: 用户 {user_id}")
    
    def test_context_update(self):
        """测试上下文更新"""
        print("\n=== 测试上下文更新 ===")
        
        user_id = "test_user"
        message = "你有什么水果最好吃"
        
        node_id = self.context_engine.update_context(
            user_id=user_id,
            content=message,
            node_type='query',
            intent='recommendation'
        )
        
        self.assertIsNotNone(node_id)
        
        session = self.context_engine.get_user_session(user_id)
        self.assertIn(node_id, session['context_graph'])
        print(f"上下文更新成功: 节点ID {node_id}")
    
    def test_relevant_context_retrieval(self):
        """测试相关上下文检索"""
        print("\n=== 测试相关上下文检索 ===")
        
        user_id = "test_user"
        
        # 添加一些上下文
        self.context_engine.update_context(user_id, "苹果多少钱", "query")
        self.context_engine.update_context(user_id, "苹果5元一斤", "response")
        
        relevant_context = self.context_engine.get_relevant_context(
            user_id=user_id,
            query="苹果怎么样",
            max_nodes=5
        )
        
        self.assertIsInstance(relevant_context, list)
        print(f"相关上下文检索成功: 找到 {len(relevant_context)} 个相关节点")
    
    def test_context_summary(self):
        """测试上下文摘要"""
        print("\n=== 测试上下文摘要 ===")
        
        user_id = "test_user"
        
        # 添加一些上下文
        self.context_engine.update_context(user_id, "推荐水果", "query", intent="recommendation")
        
        summary = self.context_engine.get_context_summary(user_id)
        
        self.assertIn('dialogue_state', summary)
        self.assertIn('total_context_nodes', summary)
        print(f"上下文摘要生成成功: {summary}")

class TestPersonalizationEngine(unittest.TestCase):
    """测试个性化学习引擎"""
    
    def setUp(self):
        """设置测试环境"""
        self.personalization_engine = PersonalizationEngine()
    
    def test_user_profile_creation(self):
        """测试用户画像创建"""
        print("\n=== 测试用户画像创建 ===")
        
        user_id = "test_user"
        profile = self.personalization_engine.get_user_profile(user_id)
        
        self.assertEqual(profile.user_id, user_id)
        self.assertIn('水果', profile.preferences)
        self.assertIn('新鲜度', profile.preferences)
        print(f"用户画像创建成功: 用户 {user_id}")
    
    def test_interaction_recording(self):
        """测试交互记录"""
        print("\n=== 测试交互记录 ===")
        
        user_id = "test_user"
        
        self.personalization_engine.record_interaction(
            user_id=user_id,
            query="推荐一些好吃的苹果",
            intent="recommendation",
            response="推荐红富士苹果",
            products_mentioned=["苹果"],
            user_feedback="很好"
        )
        
        records = self.personalization_engine.interaction_records[user_id]
        self.assertEqual(len(records), 1)
        print(f"交互记录成功: 记录数 {len(records)}")
    
    def test_personalized_recommendations(self):
        """测试个性化推荐"""
        print("\n=== 测试个性化推荐 ===")
        
        user_id = "test_user"
        
        # 模拟一些交互历史
        for i in range(6):  # 超过最小交互次数
            self.personalization_engine.record_interaction(
                user_id=user_id,
                query=f"查询{i}",
                intent="product_query",
                response=f"响应{i}",
                products_mentioned=["苹果"],
                user_feedback="好"
            )
        
        candidates = [
            {'name': '苹果', 'category': '水果', 'base_score': 0.8, 'price': 5},
            {'name': '香蕉', 'category': '水果', 'base_score': 0.7, 'price': 3},
        ]
        
        recommendations = self.personalization_engine.get_personalized_recommendations(
            user_id=user_id,
            context="推荐水果",
            candidates=candidates
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        print(f"个性化推荐成功: 推荐数量 {len(recommendations)}")
    
    def test_adaptive_response_style(self):
        """测试自适应回复风格"""
        print("\n=== 测试自适应回复风格 ===")
        
        user_id = "test_user"
        style_config = self.personalization_engine.get_adaptive_response_style(user_id)
        
        self.assertIn('response_length', style_config)
        self.assertIn('include_details', style_config)
        print(f"自适应回复风格获取成功: {style_config}")

class TestAdvancedChatEngine(unittest.TestCase):
    """测试高级聊天引擎"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建mock组件
        self.mock_product_manager = Mock()
        self.mock_policy_manager = Mock()
        
        # 使用patch避免实际初始化重型组件
        with patch('src.core.advanced_chat_engine.AdvancedNLPEngine'), \
             patch('src.core.advanced_chat_engine.DeepContextEngine'), \
             patch('src.core.advanced_chat_engine.PersonalizationEngine'), \
             patch('src.core.advanced_chat_engine.ChatHandler'):
            
            self.chat_engine = AdvancedChatEngine(
                product_manager=self.mock_product_manager,
                policy_manager=self.mock_policy_manager,
                enable_advanced_nlp=True,
                enable_deep_context=True,
                enable_personalization=True
            )
            
            # 模拟基础聊天处理器
            self.chat_engine.base_chat_handler = Mock()
            self.chat_engine.base_chat_handler.handle_message.return_value = "测试响应"
            self.chat_engine.base_chat_handler.detect_intent.return_value = "recommendation"
    
    def test_message_processing(self):
        """测试消息处理"""
        print("\n=== 测试消息处理 ===")
        
        user_id = "test_user"
        message = "你有什么水果最好吃"
        
        response = self.chat_engine.process_message(user_id, message)
        
        self.assertIsNotNone(response.content)
        self.assertIsNotNone(response.intent)
        self.assertGreater(response.confidence, 0)
        print(f"消息处理成功: {response.content}")
    
    def test_engine_stats(self):
        """测试引擎统计"""
        print("\n=== 测试引擎统计 ===")
        
        # 处理一些消息以生成统计
        for i in range(3):
            self.chat_engine.process_message(f"user_{i}", f"测试消息{i}")
        
        stats = self.chat_engine.get_engine_stats()
        
        self.assertIn('total_requests', stats)
        self.assertIn('components', stats)
        self.assertEqual(stats['total_requests'], 3)
        print(f"引擎统计获取成功: {stats}")

def run_advanced_features_tests():
    """运行高级功能测试"""
    print("开始高级功能测试...")
    
    # 创建测试套件
    test_classes = [
        TestAdvancedNLPEngine,
        TestDeepContextEngine,
        TestPersonalizationEngine,
        TestAdvancedChatEngine
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n√ 所有高级功能测试通过！")
        return True
    else:
        print(f"\nX 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
        # 输出失败详情
        for test, traceback in result.failures + result.errors:
            print(f"\n失败测试: {test}")
            print(f"错误信息: {traceback}")
        
        return False

if __name__ == "__main__":
    success = run_advanced_features_tests()
    sys.exit(0 if success else 1)
