#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不一致回复问题的诊断脚本
用于分析为什么有些查询正常，有些不正常
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.config import settings as config
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_query_processing():
    """测试查询处理的完整流程"""
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager)
    
    # 测试查询 - 基于用户截图中的例子
    test_queries = [
        "你们卖不卖鸭子",      # 截图显示正常
        "你们卖不卖蓝莓",      # 截图显示正常
        "有没有馒头？",        # 截图显示可能有问题
        "月饼卖不",           # 截图显示可能有问题
    ]
    
    print("=" * 80)
    print("查询处理诊断测试")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n【测试 {i}】查询: '{query}'")
        print("-" * 60)
        
        try:
            # 1. 预处理
            processed_input, original_input = chat_handler.preprocess_user_input(query, "test_user")
            print(f"1. 预处理结果: '{processed_input}' (原始: '{original_input}')")
            
            # 2. 意图识别
            intent = chat_handler.detect_intent(processed_input)
            print(f"2. 识别意图: {intent}")
            
            # 3. 产品名称提取
            extracted_product = chat_handler._extract_product_name_from_query(processed_input)
            print(f"3. 提取产品: '{extracted_product}'")
            
            # 4. 模糊匹配
            fuzzy_matches = product_manager.fuzzy_match_product(extracted_product or processed_input)
            print(f"4. 模糊匹配结果: {fuzzy_matches[:3]}")  # 只显示前3个
            
            # 5. 分类推断
            related_category = product_manager.find_related_category(processed_input)
            print(f"5. 推断分类: {related_category}")
            
            # 6. 完整处理
            response = chat_handler.handle_chat_message(query, "test_user")
            print(f"6. 最终回复类型: {type(response)}")

            if isinstance(response, dict):
                print(f"   回复消息长度: {len(response.get('message', ''))}")
                print(f"   推荐按钮数量: {len(response.get('product_suggestions', []))}")
                print(f"   回复预览: {response.get('message', '')[:100]}...")
            elif isinstance(response, str):
                print(f"   回复长度: {len(response)}")
                print(f"   回复预览: {response[:100]}...")
            else:
                print(f"   回复内容: {response}")

        except Exception as e:
            print(f"[ERROR] 处理出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)

def test_recommendation_engine():
    """专门测试推荐引擎的一致性"""

    product_manager = ProductManager()

    print("\n" + "=" * 80)
    print("推荐引擎一致性测试")
    print("=" * 80)

    test_cases = [
        ("鸭子", "禽类产品"),
        ("蓝莓", "时令水果"),
        ("馒头", None),  # 可能没有明确分类
        ("月饼", None),  # 可能没有明确分类
    ]

    for product_name, expected_category in test_cases:
        print(f"\n测试产品: '{product_name}' (期望分类: {expected_category})")
        print("-" * 40)

        try:
            # 测试分类推断
            inferred_category = product_manager.find_related_category(product_name)
            print(f"推断分类: {inferred_category}")

            # 测试推荐引擎的各个步骤
            if hasattr(product_manager, 'recommendation_engine'):
                rec_engine = product_manager.recommendation_engine

                # 1. 测试分类匹配
                if inferred_category:
                    category_matches = rec_engine._find_by_category(inferred_category, 3)
                    print(f"分类匹配结果: {len(category_matches)} 个")
                    for rec in category_matches:
                        print(f"  - {rec.product_details.get('name', 'Unknown')} (分数: {rec.similarity_score:.2f})")

                # 2. 测试关键词匹配
                keyword_matches = rec_engine._find_by_keywords(product_name, 3)
                print(f"关键词匹配结果: {len(keyword_matches)} 个")
                for rec in keyword_matches:
                    print(f"  - {rec.product_details.get('name', 'Unknown')} (分数: {rec.similarity_score:.2f})")

                # 3. 测试备选产品
                fallback_matches = rec_engine._find_fallback_products(3, inferred_category)
                print(f"备选产品结果: {len(fallback_matches)} 个")
                for rec in fallback_matches:
                    print(f"  - {rec.product_details.get('name', 'Unknown')} (分数: {rec.similarity_score:.2f})")

                # 4. 测试完整推荐流程
                recommendations = rec_engine.find_similar_products(
                    product_name, inferred_category, max_recommendations=3
                )
                print(f"最终推荐数量: {len(recommendations)}")
                for rec in recommendations:
                    print(f"  - {rec.product_details.get('name', 'Unknown')} (分数: {rec.similarity_score:.2f}, 原因: {rec.recommendation_reason})")

                # 测试生成回复
                response = rec_engine.generate_unavailable_response(
                    product_name, recommendations, inferred_category
                )
                print(f"回复类型: {type(response)}")
                if isinstance(response, dict):
                    print(f"回复格式正确: {'message' in response and 'product_suggestions' in response}")
                    print(f"推荐按钮数量: {len(response.get('product_suggestions', []))}")

        except Exception as e:
            print(f"[ERROR] 推荐引擎测试出错: {e}")
            import traceback
            traceback.print_exc()

def test_category_matching():
    """测试分类匹配的准确性"""
    
    product_manager = ProductManager()
    
    print("\n" + "=" * 80)
    print("分类匹配准确性测试")
    print("=" * 80)
    
    test_products = [
        "鸭子", "蓝莓", "馒头", "月饼", "草莓", "苹果", 
        "白菜", "鸡蛋", "鲫鱼", "包子"
    ]
    
    for product in test_products:
        category = product_manager.find_related_category(product)
        print(f"'{product}' -> 分类: {category}")
        
        # 检查该分类下是否有产品
        if category and category in product_manager.product_categories:
            category_products = product_manager.product_categories[category]
            print(f"  该分类下有 {len(category_products)} 个产品")
        else:
            print(f"  [WARNING] 分类不存在或为空")

def test_fallback_mechanism():
    """测试备选产品机制"""

    product_manager = ProductManager()

    print("\n" + "=" * 80)
    print("备选产品机制测试")
    print("=" * 80)

    test_categories = [
        "禽类产品",
        "美味熟食/面点",
        "时令水果",
        None
    ]

    for category in test_categories:
        print(f"\n测试分类: '{category}'")
        print("-" * 40)

        # 测试季节性产品
        seasonal = product_manager.get_seasonal_products(3, category)
        print(f"季节性产品: {len(seasonal)} 个")
        for key, details in seasonal:
            print(f"  - {details.get('name', key)} (分类: {details.get('category', 'Unknown')})")

        # 测试热门产品
        popular = product_manager.get_popular_products(3, category)
        print(f"热门产品: {len(popular)} 个")
        for key, details in popular:
            print(f"  - {details.get('name', key)} (分类: {details.get('category', 'Unknown')})")

def test_category_products():
    """测试分类产品获取"""

    product_manager = ProductManager()

    print("\n" + "=" * 80)
    print("分类产品获取测试")
    print("=" * 80)

    test_categories = [
        "禽类产品",
        "美味熟食/面点",
        "时令水果",
        "新鲜蔬菜"
    ]

    for category in test_categories:
        print(f"\n测试分类: '{category}'")
        print("-" * 40)

        # 测试get_products_by_category
        products = product_manager.get_products_by_category(category, 5)
        print(f"get_products_by_category结果: {len(products)} 个")
        for key, details in products:
            print(f"  - {details.get('name', key)} (分类: {details.get('category', 'Unknown')})")

def test_recommendation_engine_direct():
    """直接测试推荐引擎的_find_by_category方法"""

    product_manager = ProductManager()

    print("\n" + "=" * 80)
    print("推荐引擎直接测试")
    print("=" * 80)

    if hasattr(product_manager, 'recommendation_engine'):
        rec_engine = product_manager.recommendation_engine

        test_categories = [
            "禽类产品",
            "美味熟食/面点",
            "时令水果",
        ]

        for category in test_categories:
            print(f"\n测试分类: '{category}'")
            print("-" * 40)

            # 直接调用_find_by_category
            try:
                recommendations = rec_engine._find_by_category(category, 3)
                print(f"_find_by_category结果: {len(recommendations)} 个")
                for rec in recommendations:
                    print(f"  - {rec.product_details.get('name', rec.product_key)} (分数: {rec.similarity_score:.2f})")
            except Exception as e:
                print(f"[ERROR] _find_by_category出错: {e}")
                import traceback
                traceback.print_exc()

def test_find_similar_products_detailed():
    """详细测试find_similar_products方法的逻辑"""

    product_manager = ProductManager()

    print("\n" + "=" * 80)
    print("find_similar_products详细测试")
    print("=" * 80)

    if hasattr(product_manager, 'recommendation_engine'):
        rec_engine = product_manager.recommendation_engine

        test_cases = [
            ("鸭子", "禽类产品"),
            ("月饼", "美味熟食/面点"),
        ]

        for product_name, expected_category in test_cases:
            print(f"\n测试产品: '{product_name}'")
            print("-" * 40)

            # 1. 测试推断分类
            inferred_category = product_manager.find_related_category(product_name)
            print(f"推断分类: {inferred_category}")

            # 2. 测试不传入target_category的情况
            print("\n不传入target_category:")
            recommendations_no_target = rec_engine.find_similar_products(
                product_name, target_category=None, max_recommendations=3
            )
            print(f"  推荐数量: {len(recommendations_no_target)}")
            for rec in recommendations_no_target:
                print(f"    - {rec.product_details.get('name', rec.product_key)} (分数: {rec.similarity_score:.2f})")

            # 3. 测试传入推断分类的情况
            print(f"\n传入推断分类 '{inferred_category}':")
            recommendations_with_target = rec_engine.find_similar_products(
                product_name, target_category=inferred_category, max_recommendations=3
            )
            print(f"  推荐数量: {len(recommendations_with_target)}")
            for rec in recommendations_with_target:
                print(f"    - {rec.product_details.get('name', rec.product_key)} (分数: {rec.similarity_score:.2f})")

            # 4. 测试传入错误分类的情况
            print(f"\n传入错误分类 '不存在的分类':")
            recommendations_wrong_target = rec_engine.find_similar_products(
                product_name, target_category="不存在的分类", max_recommendations=3
            )
            print(f"  推荐数量: {len(recommendations_wrong_target)}")
            for rec in recommendations_wrong_target:
                print(f"    - {rec.product_details.get('name', rec.product_key)} (分数: {rec.similarity_score:.2f})")

def test_debug_find_similar_products():
    """调试find_similar_products方法的具体执行过程"""

    product_manager = ProductManager()

    print("\n" + "=" * 80)
    print("调试find_similar_products方法")
    print("=" * 80)

    if hasattr(product_manager, 'recommendation_engine'):
        rec_engine = product_manager.recommendation_engine

        # 测试"鸭子"查询
        product_name = "鸭子"
        target_category = "禽类产品"

        print(f"\n调试产品: '{product_name}' 分类: '{target_category}'")
        print("-" * 60)

        # 手动执行find_similar_products的逻辑
        recommendations = []
        max_recommendations = 3

        print(f"1. 检查target_category: '{target_category}' (bool: {bool(target_category)})")

        # 步骤1：基于类别匹配
        if target_category:
            print(f"2. 调用_find_by_category('{target_category}', {max_recommendations})")
            category_matches = rec_engine._find_by_category(target_category, max_recommendations)
            print(f"   返回结果: {len(category_matches)} 个")
            for i, rec in enumerate(category_matches):
                print(f"     [{i}] {rec.product_details.get('name', rec.product_key)} (分数: {rec.similarity_score:.2f})")
            recommendations.extend(category_matches)
            print(f"   当前推荐总数: {len(recommendations)}")

        # 步骤2：推断类别（跳过，因为有target_category）
        if not target_category:
            print("3. 推断类别（跳过，因为有target_category）")
        else:
            print("3. 跳过推断类别步骤")

        # 步骤3：关键词匹配
        print(f"4. 检查是否需要关键词匹配: {len(recommendations)} < {max_recommendations} = {len(recommendations) < max_recommendations}")
        if len(recommendations) < max_recommendations:
            print(f"5. 调用_find_by_keywords('{product_name}', {max_recommendations - len(recommendations)})")
            keyword_matches = rec_engine._find_by_keywords(product_name, max_recommendations - len(recommendations))
            print(f"   返回结果: {len(keyword_matches)} 个")
            for i, rec in enumerate(keyword_matches):
                print(f"     [{i}] {rec.product_details.get('name', rec.product_key)} (分数: {rec.similarity_score:.2f})")
            recommendations.extend(keyword_matches)
            print(f"   当前推荐总数: {len(recommendations)}")

        # 步骤4：备选产品
        print(f"6. 检查是否需要备选产品: {len(recommendations)} < {max_recommendations} = {len(recommendations) < max_recommendations}")
        if len(recommendations) < max_recommendations:
            print(f"7. 调用_find_fallback_products({max_recommendations - len(recommendations)}, '{target_category}')")
            fallback_matches = rec_engine._find_fallback_products(max_recommendations - len(recommendations), target_category)
            print(f"   返回结果: {len(fallback_matches)} 个")
            for i, rec in enumerate(fallback_matches):
                print(f"     [{i}] {rec.product_details.get('name', rec.product_key)} (分数: {rec.similarity_score:.2f})")
            recommendations.extend(fallback_matches)
            print(f"   当前推荐总数: {len(recommendations)}")

        print(f"\n最终推荐数量: {len(recommendations)}")

        # 对比完整方法调用
        print(f"\n对比完整方法调用:")
        full_recommendations = rec_engine.find_similar_products(product_name, target_category, max_recommendations)
        print(f"完整方法返回: {len(full_recommendations)} 个")

if __name__ == "__main__":
    test_query_processing()
    test_recommendation_engine()
    test_category_matching()
    test_fallback_mechanism()
    test_category_products()
    test_recommendation_engine_direct()
    test_find_similar_products_detailed()
    test_debug_find_similar_products()
