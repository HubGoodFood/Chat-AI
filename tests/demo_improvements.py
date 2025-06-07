#!/usr/bin/env python3
"""
演示产品推荐引擎改进的脚本
"""

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.products.manager import ProductManager

def demo_improvements():
    """演示改进后的产品推荐功能"""
    print("=== 产品推荐引擎改进演示 ===")
    print()
    
    # 初始化产品管理器
    product_manager = ProductManager()
    
    if not product_manager.product_catalog:
        print("产品目录为空，请检查 data/products.csv 文件")
        return
    
    print(f"已加载 {len(product_manager.product_catalog)} 个产品")
    print(f"产品类别: {', '.join(product_manager.product_categories.keys())}")
    print()
    
    # 测试场景
    test_scenarios = [
        ("蓝莓", "时令水果", "用户查询不存在的水果"),
        ("白菜", "新鲜蔬菜", "用户查询不存在的蔬菜"),
        ("龙虾", "海鲜河鲜", "用户查询不存在的海鲜"),
        ("牛奶", None, "用户查询不存在的产品（无指定类别）"),
    ]
    
    for i, (query, category, description) in enumerate(test_scenarios, 1):
        print(f"--- 场景 {i}: {description} ---")
        print(f"查询: '{query}' (类别: {category or '未指定'})")
        print()
        
        try:
            # 获取智能推荐
            recommendations = product_manager.get_smart_recommendations(query, category, 3)
            print(f"找到 {len(recommendations)} 个推荐产品:")
            
            for j, rec in enumerate(recommendations, 1):
                product_name = rec.product_details.get('original_display_name', '未知产品')
                category_name = rec.category_group
                similarity = rec.similarity_score
                reason = rec.recommendation_reason
                
                print(f"  {j}. {product_name}")
                print(f"     类别: {category_name}")
                print(f"     相似度: {similarity:.2f}")
                print(f"     推荐理由: {reason}")
            
            print()
            
            # 生成完整回复
            print("生成的完整回复:")
            response = product_manager.generate_unavailable_product_response(query, category)
            
            # 由于控制台编码问题，我们只显示回复的结构信息
            lines = response.split('\n')
            print(f"  - 回复包含 {len(lines)} 行")
            print(f"  - 回复长度: {len(response)} 字符")
            
            # 检查是否包含关键结构
            has_empathy = any('确实' in line or '真好' in line or '不错' in line for line in lines)
            has_apology = any('抱歉' in line or '缺货' in line or '没有' in line for line in lines)
            has_recommendations = any('推荐' in line or '选择' in line for line in lines)
            
            print(f"  - 包含共情表达: {'是' if has_empathy else '否'}")
            print(f"  - 包含道歉说明: {'是' if has_apology else '否'}")
            print(f"  - 包含产品推荐: {'是' if has_recommendations else '否'}")
            
        except Exception as e:
            print(f"处理过程中出现错误: {e}")
        
        print()
        print("-" * 50)
        print()

def show_product_categories():
    """显示产品类别信息"""
    print("=== 产品类别信息 ===")
    print()
    
    product_manager = ProductManager()
    
    for category, products in product_manager.product_categories.items():
        print(f"{category}: {len(products)} 个产品")
        
        # 显示前3个产品作为示例
        for i, product_key in enumerate(products[:3]):
            if product_key in product_manager.product_catalog:
                product_details = product_manager.product_catalog[product_key]
                product_name = product_details.get('original_display_name', product_key)
                print(f"  - {product_name}")
        
        if len(products) > 3:
            print(f"  ... 还有 {len(products) - 3} 个产品")
        
        print()

if __name__ == "__main__":
    try:
        demo_improvements()
        show_product_categories()
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
