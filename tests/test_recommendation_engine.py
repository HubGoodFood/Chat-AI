#!/usr/bin/env python3
"""
测试推荐引擎功能的简单脚本
"""

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.products.manager import ProductManager
from src.app.products.recommendation_engine import ProductRecommendationEngine

def test_recommendation_engine():
    """测试推荐引擎的基本功能"""
    print("=== 测试产品推荐引擎 ===\n")
    
    # 初始化产品管理器
    print("1. 初始化产品管理器...")
    product_manager = ProductManager()
    
    if not product_manager.product_catalog:
        print("ERROR: 产品目录为空，请检查 data/products.csv 文件")
        return

    print(f"SUCCESS: 成功加载 {len(product_manager.product_catalog)} 个产品")
    
    # 测试推荐引擎
    print("\n2. 测试推荐引擎...")
    
    # 测试场景1：查询不存在的水果
    print("\n--- 测试场景1：查询不存在的水果 '蓝莓' ---")
    response1 = product_manager.generate_unavailable_product_response("蓝莓", "时令水果")
    print("回复:")
    print(response1)
    
    # 测试场景2：查询不存在的蔬菜
    print("\n--- 测试场景2：查询不存在的蔬菜 '白菜' ---")
    response2 = product_manager.generate_unavailable_product_response("白菜", "新鲜蔬菜")
    print("回复:")
    print(response2)
    
    # 测试场景3：查询不存在的海鲜
    print("\n--- 测试场景3：查询不存在的海鲜 '龙虾' ---")
    response3 = product_manager.generate_unavailable_product_response("龙虾", "海鲜河鲜")
    print("回复:")
    print(response3)
    
    # 测试场景4：查询不存在的产品（无类别）
    print("\n--- 测试场景4：查询不存在的产品 '牛奶'（无指定类别）---")
    response4 = product_manager.generate_unavailable_product_response("牛奶")
    print("回复:")
    print(response4)
    
    print("\n=== 测试完成 ===")

def test_smart_recommendations():
    """测试智能推荐功能"""
    print("\n=== 测试智能推荐功能 ===\n")
    
    product_manager = ProductManager()
    
    # 测试获取推荐
    print("--- 测试获取智能推荐 ---")
    recommendations = product_manager.get_smart_recommendations("苹果", "时令水果", 3)
    
    print(f"为 '苹果' 找到 {len(recommendations)} 个推荐:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.product_details['original_display_name']}")
        print(f"   类别: {rec.category_group}")
        print(f"   相似度: {rec.similarity_score:.2f}")
        print(f"   推荐理由: {rec.recommendation_reason}")
        print()

if __name__ == "__main__":
    try:
        test_recommendation_engine()
        test_smart_recommendations()
    except Exception as e:
        print(f"ERROR: 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
