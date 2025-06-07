#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试编码问题
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def test_encoding():
    """测试编码问题"""
    print("=== 测试编码问题 ===")
    
    try:
        # 初始化系统
        cache_manager = CacheManager()
        pm = ProductManager(cache_manager=cache_manager)
        success = pm.load_product_data('data/products.csv')
        
        if not success:
            print("[ERROR] 无法加载产品数据")
            return
        
        # 测试龙虾查询
        query = "有龙虾吗"
        print(f"测试查询: {query}")
        
        # 检查类别推断
        category = pm.find_related_category(query)
        print(f"推断类别: {category}")
        
        # 获取推荐
        recommendations = pm.get_smart_recommendations(query, category)
        print(f"推荐数量: {len(recommendations)}")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"推荐 {i}: {rec.product_details['original_display_name']}")
        
        # 生成回复
        response = pm.generate_unavailable_product_response(query, category)
        print(f"回复长度: {len(response)}")
        
        # 尝试安全打印
        try:
            print("回复内容:")
            print(response)
        except UnicodeEncodeError as e:
            print(f"编码错误: {e}")
            # 尝试替换有问题的字符
            safe_response = response.encode('utf-8', errors='replace').decode('utf-8')
            print("安全回复内容:")
            print(safe_response)
            
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_encoding()
