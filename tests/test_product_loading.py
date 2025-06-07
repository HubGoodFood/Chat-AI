#!/usr/bin/env python3
"""
测试产品加载功能
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.app.products.manager import ProductManager
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

def test_product_loading():
    """测试产品加载"""
    
    print("测试产品加载:")
    print("=" * 50)
    
    try:
        pm = ProductManager()
        
        print(f"产品目录加载状态: {len(pm.product_catalog)} 个产品")
        
        if len(pm.product_catalog) == 0:
            print("[ERROR] 产品目录为空")
            return False
        
        print("前几个产品:")
        for i, (key, details) in enumerate(list(pm.product_catalog.items())[:5]):
            name = details.get('name', 'N/A')
            print(f"  {i+1}. Key: '{key}' -> Name: '{name}'")
        
        # 测试草莓是否存在
        strawberry_found = False
        for key, details in pm.product_catalog.items():
            name = details.get('name', '')
            if '草莓' in name:
                print(f"找到草莓产品: Key='{key}', Name='{name}'")
                strawberry_found = True
                break
        
        if not strawberry_found:
            print("[WARNING] 没有找到草莓产品")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 产品加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fuzzy_matching():
    """测试模糊匹配"""
    
    print("\n测试模糊匹配:")
    print("=" * 50)
    
    try:
        pm = ProductManager()
        
        if len(pm.product_catalog) == 0:
            print("[ERROR] 产品目录为空，无法测试模糊匹配")
            return False
        
        test_queries = ["草莓", "苹果", "不草莓"]
        
        for query in test_queries:
            matches = pm.fuzzy_match_product(query)
            print(f"查询 '{query}' 找到 {len(matches)} 个匹配:")
            
            for i, (product_key, score) in enumerate(matches[:3]):
                product_details = pm.product_catalog.get(product_key, {})
                product_name = product_details.get('name', product_key)
                print(f"  {i+1}. {product_name} (得分: {score:.3f})")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 模糊匹配测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_product_loading()
    success2 = test_fuzzy_matching()
    
    if success1 and success2:
        print("\n[OK] 产品加载和模糊匹配功能正常")
    else:
        print("\n[FAIL] 产品加载或模糊匹配有问题")
