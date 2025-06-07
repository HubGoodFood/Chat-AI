#!/usr/bin/env python3
"""
测试产品不可用回复修复的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def test_unavailable_responses():
    """测试产品不可用回复生成"""
    print("=== 测试产品不可用回复修复 ===\n")
    
    try:
        # 正确初始化ProductManager
        cache_manager = CacheManager()
        pm = ProductManager(cache_manager=cache_manager)
        
        # 手动加载产品数据
        success = pm.load_product_data('data/products.csv')
        if not success:
            print("[ERROR] 无法加载产品数据")
            return

        print(f"[SUCCESS] 成功加载 {len(pm.product_catalog)} 个产品\n")
        
        # 测试查询
        test_queries = ['蓝莓', '草莓', '苹果', '不存在的产品']
        
        for query in test_queries:
            print(f"=== 测试查询: {query} ===")
            try:
                response = pm.generate_unavailable_product_response(query)
                print(f"回复长度: {len(response)} 字符")
                print(f"回复内容:")
                print(response)
                print()
                
                # 检查是否有重复内容
                lines = response.split('\n')
                clean_lines = [line.strip() for line in lines if line.strip()]
                unique_lines = set(clean_lines)
                
                if len(clean_lines) != len(unique_lines):
                    print("[WARNING] 检测到可能的重复内容")
                    duplicates = []
                    seen = set()
                    for line in clean_lines:
                        if line in seen:
                            duplicates.append(line)
                        seen.add(line)
                    print(f"重复内容: {duplicates}")
                else:
                    print("[OK] 无重复内容")

                # 检查回复结构
                has_empathy = any(word in response for word in ["确实是", "真是个", "眼光真好", "都喜欢"])
                has_apology = any(word in response for word in ["很抱歉", "不好意思", "可惜", "真不好意思"])
                has_recommendation = "推荐" in response or "选择" in response

                if has_empathy and has_apology and has_recommendation:
                    print("[OK] 包含完整的三步结构")
                else:
                    missing = []
                    if not has_empathy: missing.append("共情确认")
                    if not has_apology: missing.append("道歉告知")
                    if not has_recommendation: missing.append("推荐替代")
                    print(f"[WARNING] 缺少: {', '.join(missing)}")

            except Exception as e:
                print(f"[ERROR] 错误: {e}")
                import traceback
                traceback.print_exc()
            
            print("-" * 50)
            
    except Exception as e:
        print(f"[ERROR] 初始化错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unavailable_responses()
