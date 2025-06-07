#!/usr/bin/env python3
"""
调试推荐引擎的具体问题
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def debug_recommendation_engine():
    """调试推荐引擎"""
    print("=== 调试推荐引擎 ===\n")
    
    try:
        # 初始化系统
        cache_manager = CacheManager()
        pm = ProductManager(cache_manager=cache_manager)
        success = pm.load_product_data('data/products.csv')
        
        if not success:
            print("[ERROR] 无法加载产品数据")
            return
            
        print(f"[SUCCESS] 加载了 {len(pm.product_catalog)} 个产品")
        
        # 检查产品类别
        print(f"\n=== 产品类别分析 ===")
        print(f"类别数量: {len(pm.product_categories)}")
        for category, products in pm.product_categories.items():
            print(f"  {category}: {len(products)} 个产品")
        
        # 测试查询
        test_queries = ["蓝莓", "草莓", "苹果"]
        
        for query in test_queries:
            print(f"\n{'='*50}")
            print(f"调试查询: {query}")
            print(f"{'='*50}")
            
            # 1. 检查类别推断
            inferred_category = pm.find_related_category(query)
            print(f"推断类别: {inferred_category}")
            
            # 2. 检查类别产品
            if inferred_category:
                category_products = pm.get_products_by_category(inferred_category, 5)
                print(f"类别产品数量: {len(category_products)}")
                for key, details in category_products[:3]:
                    print(f"  - {details['original_display_name']}")
            
            # 3. 检查模糊匹配
            fuzzy_matches = pm.fuzzy_match_product(query, threshold=0.3)
            print(f"模糊匹配结果: {len(fuzzy_matches)}")
            for key, score in fuzzy_matches[:3]:
                product_name = pm.product_catalog[key]['original_display_name']
                print(f"  - {product_name}: {score:.3f}")
            
            # 4. 检查当季产品
            seasonal_products = pm.get_seasonal_products(3, inferred_category)
            print(f"当季产品数量: {len(seasonal_products)}")
            for key, details in seasonal_products[:3]:
                print(f"  - {details['original_display_name']}")
            
            # 5. 检查热门产品
            popular_products = pm.get_popular_products(3, inferred_category)
            print(f"热门产品数量: {len(popular_products)}")
            for key, details in popular_products[:3]:
                print(f"  - {details['original_display_name']}")
            
            # 6. 测试推荐引擎
            print(f"\n--- 推荐引擎测试 ---")
            recommendations = pm.get_smart_recommendations(query, inferred_category)
            print(f"推荐数量: {len(recommendations)}")
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    print(f"  {i}. {rec.product_details['original_display_name']}")
                    print(f"     相似度: {rec.similarity_score:.3f}")
                    print(f"     理由: {rec.recommendation_reason}")
                    print(f"     类别: {rec.category_group}")
                
                # 测试回复生成
                print(f"\n--- 回复生成测试 ---")
                response = pm.recommendation_engine.generate_unavailable_response(
                    query, recommendations, inferred_category
                )
                print(f"回复长度: {len(response)} 字符")
                print(f"回复内容:\n{response}")
            else:
                print("  [WARNING] 没有找到推荐产品")
                
                # 测试无推荐回复
                response = pm.recommendation_engine._generate_no_recommendations_response(query)
                print(f"\n--- 无推荐回复测试 ---")
                print(f"回复长度: {len(response)} 字符")
                print(f"回复内容:\n{response}")
                
    except Exception as e:
        print(f"[ERROR] 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_recommendation_engine()
