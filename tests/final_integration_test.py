#!/usr/bin/env python3
"""
最终集成测试 - 验证产品不可用回复修复
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def test_chat_handler_integration():
    """测试聊天处理器的集成功能"""
    print("=== 最终集成测试 ===\n")
    
    try:
        # 初始化组件
        cache_manager = CacheManager()
        product_manager = ProductManager(cache_manager=cache_manager)
        
        # 手动加载产品数据
        success = product_manager.load_product_data('data/products.csv')
        if not success:
            print("[ERROR] 无法加载产品数据")
            return
            
        # 初始化聊天处理器
        chat_handler = ChatHandler(product_manager=product_manager)
        
        print(f"[SUCCESS] 系统初始化完成，加载了 {len(product_manager.product_catalog)} 个产品\n")
        
        # 测试不同类型的产品不可用查询
        test_cases = [
            {
                "query": "有没有蓝莓",
                "description": "水果类产品查询"
            },
            {
                "query": "卖不卖草莓", 
                "description": "中文意图识别测试"
            },
            {
                "query": "我想买苹果",
                "description": "购买意图测试"
            },
            {
                "query": "有龙虾吗",
                "description": "海鲜类产品查询"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"=== 测试 {i}: {description} ===")
            print(f"查询: {query}")
            
            try:
                # 模拟用户查询
                user_id = "test_user"
                response = chat_handler.handle_chat_message(query, user_id)
                handled = response is not None
                
                if handled and isinstance(response, str):
                    print(f"回复类型: 字符串回复")
                    print(f"回复长度: {len(response)} 字符")
                    print(f"回复内容:")
                    print(response)
                    
                    # 验证回复质量
                    quality_checks = {
                        "无重复内容": check_no_duplicates(response),
                        "包含三步结构": check_three_step_structure(response),
                        "语气温暖": check_warm_tone(response),
                        "有推荐产品": check_has_recommendations(response)
                    }
                    
                    print("\n质量检查:")
                    for check_name, passed in quality_checks.items():
                        status = "[OK]" if passed else "[FAIL]"
                        print(f"  {status} {check_name}")
                        
                elif handled and isinstance(response, dict):
                    print(f"回复类型: 澄清选项")
                    print(f"澄清消息: {response.get('message', '')}")
                    print(f"选项数量: {len(response.get('clarification_options', []))}")
                else:
                    print(f"回复类型: 未处理或其他")
                    print(f"处理状态: {handled}")
                    
            except Exception as e:
                print(f"[ERROR] 处理查询时出错: {e}")
                import traceback
                traceback.print_exc()
            
            print("-" * 60)
            
    except Exception as e:
        print(f"[ERROR] 系统初始化错误: {e}")
        import traceback
        traceback.print_exc()

def check_no_duplicates(response):
    """检查是否有重复内容"""
    lines = response.split('\n')
    clean_lines = [line.strip() for line in lines if line.strip()]
    return len(clean_lines) == len(set(clean_lines))

def check_three_step_structure(response):
    """检查是否包含三步结构"""
    has_empathy = any(word in response for word in ["确实是", "真是个", "眼光真好", "都喜欢"])
    has_apology = any(word in response for word in ["很抱歉", "不好意思", "可惜", "真不好意思"])
    has_recommendation = "推荐" in response or "选择" in response or "-" in response
    return has_empathy and has_apology and has_recommendation

def check_warm_tone(response):
    """检查是否有温暖的语气"""
    warm_words = ["确实", "真是", "眼光", "不错", "很棒", "优质", "受欢迎", "感兴趣"]
    return any(word in response for word in warm_words)

def check_has_recommendations(response):
    """检查是否包含产品推荐"""
    return "-" in response and "$" in response

if __name__ == "__main__":
    test_chat_handler_integration()
