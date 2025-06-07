#!/usr/bin/env python3
"""
深入调试产品不可用回复的调用链路
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 设置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

class DebugChatHandler(ChatHandler):
    """带调试功能的ChatHandler"""
    
    def handle_chat_message(self, user_input: str, user_id: str):
        print(f"\n=== DEBUG: handle_chat_message 开始 ===")
        print(f"输入: {user_input}")
        print(f"用户ID: {user_id}")
        
        result = super().handle_chat_message(user_input, user_id)
        
        print(f"=== DEBUG: handle_chat_message 结束 ===")
        print(f"结果类型: {type(result)}")
        if isinstance(result, str):
            print(f"结果长度: {len(result)} 字符")
            print(f"结果内容:\n{result}")
        
        return result
    
    def _handle_price_or_buy_fallback_recommendation(self, user_input_original, user_input_processed, identified_query_product_name):
        print(f"\n=== DEBUG: _handle_price_or_buy_fallback_recommendation 被调用 ===")
        print(f"原始输入: {user_input_original}")
        print(f"处理后输入: {user_input_processed}")
        print(f"识别的产品名: {identified_query_product_name}")
        
        result = super()._handle_price_or_buy_fallback_recommendation(
            user_input_original, user_input_processed, identified_query_product_name
        )
        
        print(f"=== DEBUG: _handle_price_or_buy_fallback_recommendation 结果 ===")
        print(f"结果长度: {len(result)} 字符")
        print(f"结果内容:\n{result}")
        
        return result

class DebugProductManager(ProductManager):
    """带调试功能的ProductManager"""
    
    def generate_unavailable_product_response(self, query_product_name: str, target_category=None):
        print(f"\n=== DEBUG: ProductManager.generate_unavailable_product_response 被调用 ===")
        print(f"查询产品名: {query_product_name}")
        print(f"目标类别: {target_category}")
        
        try:
            result = super().generate_unavailable_product_response(query_product_name, target_category)
            print(f"=== DEBUG: ProductManager.generate_unavailable_product_response 成功 ===")
            print(f"结果长度: {len(result)} 字符")
            print(f"结果内容:\n{result}")
            return result
        except Exception as e:
            print(f"=== DEBUG: ProductManager.generate_unavailable_product_response 异常 ===")
            print(f"异常: {e}")
            raise

def debug_call_chain():
    """调试完整的调用链路"""
    print("=== 深入调试产品不可用回复调用链路 ===\n")
    
    try:
        # 初始化组件
        cache_manager = CacheManager()
        product_manager = DebugProductManager(cache_manager=cache_manager)
        
        # 手动加载产品数据
        success = product_manager.load_product_data('data/products.csv')
        if not success:
            print("[ERROR] 无法加载产品数据")
            return
            
        # 初始化调试版聊天处理器
        chat_handler = DebugChatHandler(product_manager=product_manager)
        
        print(f"[SUCCESS] 系统初始化完成，加载了 {len(product_manager.product_catalog)} 个产品\n")
        
        # 测试具体的产品不可用查询
        test_queries = [
            "有没有蓝莓",
            "卖不卖草莓", 
            "我想买苹果"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}: {query}")
            print(f"{'='*60}")
            
            try:
                # 清除任何可能的缓存
                user_id = f"debug_user_{i}"
                
                # 调用聊天处理器
                response = chat_handler.handle_chat_message(query, user_id)
                
                # 检查重复内容
                if isinstance(response, str):
                    lines = response.split('\n')
                    clean_lines = [line.strip() for line in lines if line.strip()]
                    unique_lines = set(clean_lines)
                    
                    print(f"\n=== 重复内容检查 ===")
                    print(f"总行数: {len(clean_lines)}")
                    print(f"唯一行数: {len(unique_lines)}")
                    
                    if len(clean_lines) != len(unique_lines):
                        print("[WARNING] 检测到重复内容!")
                        duplicates = []
                        seen = set()
                        for line in clean_lines:
                            if line in seen:
                                duplicates.append(line)
                            seen.add(line)
                        print(f"重复的行: {duplicates}")
                    else:
                        print("[OK] 无重复内容")
                
            except Exception as e:
                print(f"[ERROR] 处理查询时出错: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"[ERROR] 系统初始化错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_call_chain()
