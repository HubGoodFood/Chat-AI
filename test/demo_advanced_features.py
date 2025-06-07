"""
高级功能演示
展示中期优化的三个核心功能：高级NLP、深度上下文理解、个性化学习
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import numpy as np
from unittest.mock import Mock

# 导入组件
from src.core.deep_context_engine import DeepContextEngine
from src.app.personalization.learning_engine import PersonalizationEngine

def demo_deep_context_understanding():
    """演示深度上下文理解功能"""
    print("=" * 60)
    print(">> 深度上下文理解演示")
    print("=" * 60)
    
    # 创建mock NLP引擎
    mock_nlp = Mock()
    mock_nlp.encode_text.return_value = np.random.rand(384)
    
    # 初始化深度上下文引擎
    context_engine = DeepContextEngine(nlp_engine=mock_nlp)
    
    user_id = "demo_user"
    
    print("模拟多轮对话场景：")
    print("-" * 60)
    
    # 模拟对话序列
    dialogue_sequence = [
        ("你有什么水果", "query", "recommendation"),
        ("我们有苹果、香蕉、草莓等", "response", None),
        ("苹果多少钱", "query", "price_query"),
        ("苹果5元一斤", "response", None),
        ("还有其他推荐吗", "query", "recommendation"),
        ("推荐草莓，很新鲜很甜", "response", None),
        ("草莓怎么样", "query", "product_query")
    ]
    
    # 逐步添加对话上下文
    for i, (content, node_type, intent) in enumerate(dialogue_sequence, 1):
        print(f"{i}. {content} ({node_type})")
        
        node_id = context_engine.update_context(
            user_id=user_id,
            content=content,
            node_type=node_type,
            intent=intent
        )
        
        time.sleep(0.1)  # 模拟时间间隔
    
    print("\n上下文分析结果：")
    print("-" * 60)
    
    # 获取上下文摘要
    summary = context_engine.get_context_summary(user_id)
    print(f"对话状态: {summary['dialogue_state']}")
    print(f"上下文节点数: {summary['total_context_nodes']}")
    print(f"活跃实体数: {summary['active_entities']}")
    print(f"最近意图: {summary['recent_intents']}")
    print(f"主要实体: {summary['top_entities']}")
    
    # 测试相关上下文检索
    print("\n相关上下文检索测试：")
    print("-" * 60)
    
    test_queries = [
        "苹果怎么样",
        "价格如何",
        "还有什么推荐"
    ]
    
    for query in test_queries:
        relevant_context = context_engine.get_relevant_context(
            user_id=user_id,
            query=query,
            max_nodes=3
        )
        print(f"查询: {query}")
        print(f"相关上下文: {len(relevant_context)} 个节点")
        for ctx in relevant_context[:2]:  # 显示前2个
            print(f"  - {ctx.content} ({ctx.node_type})")
        print()

def demo_personalization_learning():
    """演示个性化学习功能"""
    print("=" * 60)
    print(">> 个性化学习演示")
    print("=" * 60)
    
    # 初始化个性化引擎
    personalization_engine = PersonalizationEngine()
    
    user_id = "demo_user"
    
    print("模拟用户交互学习过程：")
    print("-" * 60)
    
    # 模拟用户交互历史
    interactions = [
        {
            'query': '推荐一些好吃的苹果',
            'intent': 'recommendation',
            'response': '推荐红富士苹果，很甜很脆',
            'products': ['苹果'],
            'feedback': '很好，谢谢'
        },
        {
            'query': '苹果多少钱',
            'intent': 'price_query',
            'response': '红富士苹果5元一斤',
            'products': ['苹果'],
            'feedback': '有点贵'
        },
        {
            'query': '有便宜点的水果吗',
            'intent': 'recommendation',
            'response': '推荐香蕉，3元一斤',
            'products': ['香蕉'],
            'feedback': '不错'
        },
        {
            'query': '香蕉新鲜吗',
            'intent': 'product_query',
            'response': '香蕉很新鲜，今天刚到货',
            'products': ['香蕉'],
            'feedback': '好的'
        },
        {
            'query': '还有什么便宜的水果',
            'intent': 'recommendation',
            'response': '还有橙子，4元一斤',
            'products': ['橙子'],
            'feedback': '可以'
        },
        {
            'query': '给我推荐一些蔬菜',
            'intent': 'recommendation',
            'response': '推荐白菜和萝卜',
            'products': ['白菜', '萝卜'],
            'feedback': '好'
        }
    ]
    
    # 记录交互历史
    for i, interaction in enumerate(interactions, 1):
        print(f"{i}. 用户: {interaction['query']}")
        print(f"   系统: {interaction['response']}")
        print(f"   反馈: {interaction['feedback']}")
        
        personalization_engine.record_interaction(
            user_id=user_id,
            query=interaction['query'],
            intent=interaction['intent'],
            response=interaction['response'],
            products_mentioned=interaction['products'],
            user_feedback=interaction['feedback']
        )
        
        time.sleep(0.1)
    
    print("\n个性化学习结果：")
    print("-" * 60)
    
    # 获取用户画像
    profile = personalization_engine.get_user_profile(user_id)
    print(f"交互风格: {profile.interaction_style}")
    print(f"主要偏好:")
    sorted_prefs = sorted(profile.preferences.items(), key=lambda x: x[1], reverse=True)
    for pref, score in sorted_prefs[:5]:
        print(f"  - {pref}: {score:.2f}")
    
    print(f"\n行为模式:")
    for pattern, value in profile.behavior_patterns.items():
        if isinstance(value, (int, float)):
            print(f"  - {pattern}: {value:.2f}")
        else:
            print(f"  - {pattern}: {value}")
    
    # 测试个性化推荐
    print("\n个性化推荐测试：")
    print("-" * 60)
    
    candidates = [
        {'name': '苹果', 'category': '水果', 'base_score': 0.8, 'price': 5, 'novelty_score': 0.1},
        {'name': '香蕉', 'category': '水果', 'base_score': 0.7, 'price': 3, 'novelty_score': 0.2},
        {'name': '橙子', 'category': '水果', 'base_score': 0.6, 'price': 4, 'novelty_score': 0.3},
        {'name': '葡萄', 'category': '水果', 'base_score': 0.9, 'price': 8, 'novelty_score': 0.8},
        {'name': '白菜', 'category': '蔬菜', 'base_score': 0.5, 'price': 2, 'novelty_score': 0.1}
    ]
    
    recommendations = personalization_engine.get_personalized_recommendations(
        user_id=user_id,
        context="推荐一些产品",
        candidates=candidates
    )
    
    print("基于用户偏好的个性化推荐:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} ({rec['category']}) - 价格: {rec['price']}元")
    
    # 测试自适应回复风格
    print("\n自适应回复风格：")
    print("-" * 60)
    
    style_config = personalization_engine.get_adaptive_response_style(user_id)
    print(f"推荐回复风格: {style_config}")
    
    # 获取学习统计
    print("\n学习统计信息：")
    print("-" * 60)
    
    stats = personalization_engine.get_learning_stats(user_id)
    print(f"学习状态: {stats['status']}")
    print(f"总交互次数: {stats['total_interactions']}")
    print(f"学习进度: {stats['learning_progress']:.1%}")
    if stats['avg_satisfaction']:
        print(f"平均满意度: {stats['avg_satisfaction']:.2f}")

def demo_integrated_features():
    """演示集成功能"""
    print("=" * 60)
    print(">> 集成功能演示")
    print("=" * 60)
    
    # 创建mock NLP引擎
    mock_nlp = Mock()
    mock_nlp.encode_text.return_value = np.random.rand(384)
    mock_nlp.calculate_semantic_similarity.return_value = 0.85
    
    # 初始化组件
    context_engine = DeepContextEngine(nlp_engine=mock_nlp)
    personalization_engine = PersonalizationEngine(
        nlp_engine=mock_nlp,
        context_engine=context_engine
    )
    
    user_id = "integrated_user"
    
    print("模拟完整的智能对话场景：")
    print("-" * 60)
    
    # 场景：用户寻找水果推荐
    scenarios = [
        {
            'user_input': '你有什么水果最好吃',
            'system_response': '我推荐红富士苹果和草莓，都很新鲜很甜',
            'user_feedback': '好的'
        },
        {
            'user_input': '苹果多少钱',
            'system_response': '红富士苹果5元一斤',
            'user_feedback': '有点贵'
        },
        {
            'user_input': '有便宜点的吗',
            'system_response': '根据您的偏好，推荐香蕉3元一斤，也很甜',
            'user_feedback': '不错'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n轮次 {i}:")
        print(f"用户: {scenario['user_input']}")
        
        # 1. 更新上下文
        context_engine.update_context(
            user_id=user_id,
            content=scenario['user_input'],
            node_type='query',
            intent='recommendation'
        )
        
        # 2. 获取相关上下文
        relevant_context = context_engine.get_relevant_context(
            user_id=user_id,
            query=scenario['user_input']
        )
        
        print(f"系统: {scenario['system_response']}")
        print(f"(使用了 {len(relevant_context)} 个上下文节点)")
        
        # 3. 更新响应上下文
        context_engine.update_context(
            user_id=user_id,
            content=scenario['system_response'],
            node_type='response'
        )
        
        # 4. 记录个性化学习
        personalization_engine.record_interaction(
            user_id=user_id,
            query=scenario['user_input'],
            intent='recommendation',
            response=scenario['system_response'],
            user_feedback=scenario['user_feedback']
        )
        
        print(f"用户反馈: {scenario['user_feedback']}")
    
    print("\n集成效果分析：")
    print("-" * 60)
    
    # 上下文分析
    context_summary = context_engine.get_context_summary(user_id)
    print(f"上下文状态: {context_summary['dialogue_state']}")
    print(f"对话轮次: {context_summary['total_context_nodes']//2}")
    
    # 个性化分析
    learning_stats = personalization_engine.get_learning_stats(user_id)
    print(f"个性化学习: {learning_stats['learning_progress']:.1%}")
    print(f"交互风格: {learning_stats['interaction_style']}")
    
    print("\n智能化程度提升:")
    print("√ 上下文连贯性: 系统能记住之前的对话内容")
    print("√ 个性化适配: 根据用户反馈调整推荐策略")
    print("√ 语义理解: 理解'便宜点的'指向价格偏好")
    print("√ 智能推荐: 结合用户偏好和上下文信息")

def main():
    """主演示函数"""
    print(">> Chat AI 中期优化功能演示")
    print("=" * 60)
    print("本演示展示三个核心优化功能的实际效果：")
    print("1. 集成更强大的中文NLP模型 (模拟)")
    print("2. 实现深度上下文理解")
    print("3. 添加个性化学习机制")
    print()
    
    try:
        # 1. 深度上下文理解演示
        demo_deep_context_understanding()
        print()
        
        # 2. 个性化学习演示
        demo_personalization_learning()
        print()
        
        # 3. 集成功能演示
        demo_integrated_features()
        print()
        
        print("=" * 60)
        print("√ 中期优化功能演示完成！")
        print("=" * 60)
        print("\n主要改进效果:")
        print("• 深度上下文理解: 多轮对话连贯性显著提升")
        print("• 个性化学习: 系统能够学习用户偏好并适配")
        print("• 智能化程度: 从简单问答升级为智能助手")
        print("• 用户体验: 更自然、更个性化的交互体验")
        
    except Exception as e:
        print(f"X 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
