#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试产品不可用时的推荐按钮功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager

def test_unavailable_product_buttons():
    """测试不可用产品的推荐按钮功能"""
    
    print("=== 测试不可用产品推荐按钮 ===")
    print()
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试不可用产品的查询
    unavailable_queries = [
        "有草莓吗？",
        "卖不卖草莓",
        "有没有草莓",
        "草莓多少钱",
        "想买草莓"
    ]
    
    for query in unavailable_queries:
        print(f"测试查询: '{query}'")
        print("-" * 40)
        
        try:
            # 直接调用chat handler
            response = chat_handler.handle_chat_message(query, "test_user")
            
            print(f"响应类型: {type(response)}")
            
            if isinstance(response, dict):
                print("响应是字典格式:")
                print(f"  message: {response.get('message', 'N/A')[:100]}...")
                
                # 检查product_suggestions
                product_suggestions = response.get('product_suggestions', [])
                print(f"  product_suggestions数量: {len(product_suggestions)}")
                
                if product_suggestions:
                    print("  推荐产品:")
                    for i, suggestion in enumerate(product_suggestions):
                        print(f"    {i+1}. {suggestion.get('display_text', 'N/A')} (payload: {suggestion.get('payload', 'N/A')})")
                else:
                    print("  没有产品推荐")
                
                # 检查clarification_options（应该没有）
                clarification_options = response.get('clarification_options', [])
                print(f"  clarification_options数量: {len(clarification_options)}")
                
            elif isinstance(response, str):
                print(f"响应是字符串: {response[:100]}...")
            else:
                print(f"响应是其他类型: {response}")
                
        except Exception as e:
            print(f"处理出错: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60 + "\n")

def test_api_unavailable_products():
    """测试API端点的不可用产品处理"""
    
    print("=== 测试API不可用产品处理 ===")
    print()
    
    # 测试查询
    test_queries = ["有草莓吗？", "卖不卖草莓"]
    
    for query in test_queries:
        print(f"测试API查询: '{query}'")
        print("-" * 40)
        
        try:
            # 发送POST请求到API
            response = requests.post(
                'http://localhost:5000/chat',
                json={'message': query, 'user_id': 'test_user'},
                timeout=10
            )
            
            print(f"HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应数据类型: {type(data)}")
                print(f"响应键: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                
                if isinstance(data, dict):
                    print(f"  message: {data.get('message', 'N/A')[:100]}...")
                    
                    # 检查product_suggestions
                    product_suggestions = data.get('product_suggestions', [])
                    print(f"  product_suggestions存在: {'product_suggestions' in data}")
                    print(f"  product_suggestions数量: {len(product_suggestions)}")
                    
                    if product_suggestions:
                        print("  推荐产品:")
                        for i, suggestion in enumerate(product_suggestions):
                            print(f"    {i+1}. {suggestion.get('display_text', 'N/A')}")
                    
                    # 检查clarification_options
                    clarification_options = data.get('clarification_options', [])
                    print(f"  clarification_options数量: {len(clarification_options)}")
                        
            else:
                print(f"API错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("无法连接到API - 请确保应用正在运行")
        except Exception as e:
            print(f"API测试出错: {e}")
        
        print("\n" + "=" * 60 + "\n")

def test_product_selection_flow():
    """测试完整的产品选择流程"""
    
    print("=== 测试完整产品选择流程 ===")
    print()
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    print("步骤1: 查询不可用产品")
    response1 = chat_handler.handle_chat_message("有草莓吗？", "test_user")
    
    if isinstance(response1, dict) and response1.get('product_suggestions'):
        suggestions = response1['product_suggestions']
        print(f"收到 {len(suggestions)} 个产品建议")
        
        if suggestions:
            # 选择第一个建议
            first_suggestion = suggestions[0]
            print(f"\n步骤2: 选择产品 '{first_suggestion['display_text']}'")
            
            selection_message = f"product_selection:{first_suggestion['payload']}"
            response2 = chat_handler.handle_chat_message(selection_message, "test_user")
            
            print(f"产品选择响应类型: {type(response2)}")
            if isinstance(response2, str):
                print(f"产品详情: {response2[:200]}...")
                
                # 检查是否包含产品信息
                has_price = any(keyword in response2 for keyword in ['价格', '售价', '元', '$'])
                has_description = any(keyword in response2 for keyword in ['新鲜', '特点', '产地', '重量'])
                
                print(f"包含价格信息: {'是' if has_price else '否'}")
                print(f"包含描述信息: {'是' if has_description else '否'}")
                
                if has_price and has_description:
                    print("OK 完整的产品选择流程测试成功")
                else:
                    print("WARN 产品信息可能不完整")
            else:
                print(f"意外的响应格式: {response2}")
    else:
        print("ERROR 没有收到产品建议")

if __name__ == "__main__":
    test_unavailable_product_buttons()
    print("\n" + "="*80 + "\n")
    test_api_unavailable_products()
    print("\n" + "="*80 + "\n")
    test_product_selection_flow()
