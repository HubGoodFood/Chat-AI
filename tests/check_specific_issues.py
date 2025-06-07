#!/usr/bin/env python3
"""
检查特定问题的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def check_specific_issues():
    """检查特定的问题"""
    print("=== 检查特定问题 ===\n")
    
    try:
        # 初始化系统
        cache_manager = CacheManager()
        product_manager = ProductManager(cache_manager=cache_manager)
        success = product_manager.load_product_data('data/products.csv')
        
        if not success:
            print("[ERROR] 无法加载产品数据")
            return
            
        chat_handler = ChatHandler(product_manager=product_manager)
        
        # 检查问题查询
        problem_queries = [
            "卖不卖草莓",
            "我想买苹果", 
            "有龙虾吗"
        ]
        
        for query in problem_queries:
            print(f"=== 检查查询: {query} ===")
            
            # 1. 检查是否找到了实际产品
            fuzzy_matches = product_manager.fuzzy_match_product(query, threshold=0.3)
            print(f"模糊匹配结果: {len(fuzzy_matches)}")
            for key, score in fuzzy_matches[:3]:
                product_name = product_manager.product_catalog[key]['original_display_name']
                print(f"  - {product_name}: {score:.3f}")
            
            # 2. 检查类别推断
            inferred_category = product_manager.find_related_category(query)
            print(f"推断类别: {inferred_category}")
            
            # 3. 执行完整查询
            try:
                response = chat_handler.handle_chat_message(query, "test_user")
                print(f"回复类型: {type(response)}")
                print(f"回复长度: {len(response) if isinstance(response, str) else 'N/A'}")
                
                if isinstance(response, str):
                    # 检查是否是产品不可用回复
                    is_unavailable_response = any(word in response for word in ["很抱歉", "不好意思", "可惜", "暂时没有"])
                    print(f"是否为不可用回复: {is_unavailable_response}")
                    
                    # 检查是否有推荐
                    has_recommendations = "-" in response and "$" in response
                    print(f"是否有推荐产品: {has_recommendations}")
                    
                    # 显示回复
                    print(f"回复内容:")
                    print(response)
                else:
                    print(f"回复内容: {response}")
                    
            except Exception as e:
                print(f"[ERROR] 查询处理失败: {e}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"[ERROR] 系统错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_specific_issues()
