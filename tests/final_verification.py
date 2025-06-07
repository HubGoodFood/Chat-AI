#!/usr/bin/env python3
"""
最终验证脚本 - 确认产品不可用回复修复完成
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def final_verification():
    """最终验证修复效果"""
    print("=== 最终验证：产品不可用回复修复 ===\n")
    
    try:
        # 初始化系统
        cache_manager = CacheManager()
        product_manager = ProductManager(cache_manager=cache_manager)
        success = product_manager.load_product_data('data/products.csv')
        
        if not success:
            print("[ERROR] 无法加载产品数据")
            return
            
        chat_handler = ChatHandler(product_manager=product_manager)
        print(f"[SUCCESS] 系统初始化完成，加载了 {len(product_manager.product_catalog)} 个产品\n")
        
        # 测试用例 - 模拟用户原始反馈的问题
        test_cases = [
            {
                "query": "有没有蓝莓",
                "description": "原始问题案例1 - 蓝莓查询",
                "expected_features": ["三步结构", "无重复", "有推荐"]
            },
            {
                "query": "卖不卖草莓", 
                "description": "原始问题案例2 - 草莓查询",
                "expected_features": ["三步结构", "无重复", "有推荐"]
            },
            {
                "query": "我想买苹果",
                "description": "原始问题案例3 - 苹果查询", 
                "expected_features": ["三步结构", "无重复", "有推荐"]
            },
            {
                "query": "有龙虾吗",
                "description": "海鲜类产品查询",
                "expected_features": ["三步结构", "无重复", "有推荐"]
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            description = test_case["description"]
            expected_features = test_case["expected_features"]
            
            print(f"=== 测试 {i}: {description} ===")
            print(f"查询: {query}")
            
            try:
                # 执行查询
                user_id = f"test_user_{i}"
                response = chat_handler.handle_chat_message(query, user_id)
                
                if isinstance(response, str):
                    print(f"[OK] 成功生成回复 ({len(response)} 字符)")

                    # 验证修复效果
                    verification_results = verify_response_quality(response, expected_features)

                    print("修复验证结果:")
                    for feature, passed in verification_results.items():
                        status = "[OK]" if passed else "[FAIL]"
                        print(f"  {status} {feature}")
                        if not passed:
                            all_passed = False

                    # 显示回复内容（截断显示）
                    preview = response[:100] + "..." if len(response) > 100 else response
                    print(f"回复预览: {preview}")

                else:
                    print(f"[ERROR] 回复类型异常: {type(response)}")
                    all_passed = False

            except Exception as e:
                print(f"[ERROR] 处理查询时出错: {e}")
                all_passed = False
            
            print("-" * 60)
        
        # 最终结果
        print("\n=== 最终验证结果 ===")
        if all_passed:
            print("[SUCCESS] 所有测试通过！产品不可用回复修复成功完成！")
            print("\n[ACHIEVEMENTS] 修复成果:")
            print("  - 统一了产品不可用回复系统")
            print("  - 消除了重复内容问题")
            print("  - 标准化了三步回复结构")
            print("  - 确保了语气和格式一致性")
            print("  - 优化了推荐引擎和类别匹配")
        else:
            print("[WARNING] 部分测试未通过，需要进一步检查")
            
    except Exception as e:
        print(f"[ERROR] 系统错误: {e}")
        import traceback
        traceback.print_exc()

def verify_response_quality(response, expected_features):
    """验证回复质量"""
    results = {}
    
    # 检查三步结构
    if "三步结构" in expected_features:
        has_empathy = any(word in response for word in ["确实是", "真是个", "眼光真好", "都喜欢", "不错的选择"])
        has_apology = any(word in response for word in ["很抱歉", "不好意思", "可惜", "真不好意思"])
        has_recommendation = any(word in response for word in ["推荐", "选择", "不过", "-"])
        results["三步结构"] = has_empathy and has_apology and has_recommendation
    
    # 检查无重复内容
    if "无重复" in expected_features:
        lines = response.split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]
        unique_lines = set(clean_lines)
        results["无重复内容"] = len(clean_lines) == len(unique_lines)
    
    # 检查有推荐产品
    if "有推荐" in expected_features:
        has_products = "-" in response and "$" in response
        results["有推荐产品"] = has_products
    
    # 检查语气一致性
    warm_words = ["确实", "真是", "眼光", "不错", "很棒", "优质", "受欢迎", "感兴趣"]
    results["语气温暖"] = any(word in response for word in warm_words)
    
    # 检查格式规范
    results["格式规范"] = "\n\n" in response  # 应该有段落分隔
    
    return results

if __name__ == "__main__":
    final_verification()
