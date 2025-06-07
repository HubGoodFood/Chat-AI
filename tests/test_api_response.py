#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API响应格式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager

def test_api_response():
    """测试API响应格式"""
    
    print("=== 测试API响应格式 ===")
    print()
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试查询
    test_queries = [
        "玉米",
        "蛋", 
        "鸡"
    ]
    
    for query in test_queries:
        print(f"测试查询: '{query}'")
        print("-" * 40)
        
        try:
            # 直接调用chat handler
            response = chat_handler.handle_chat_message(query, "test_user")
            
            print(f"响应类型: {type(response)}")
            
            if isinstance(response, dict):
                print("响应是字典格式:")
                print(f"  message: {response.get('message', 'N/A')[:100]}...")
                print(f"  clarification_options: {response.get('clarification_options', 'N/A')}")
                print(f"  product_suggestions: {response.get('product_suggestions', 'N/A')}")
                
                # 检查clarification_options的结构
                if 'clarification_options' in response:
                    options = response['clarification_options']
                    print(f"  clarification_options数量: {len(options) if options else 0}")
                    if options:
                        for i, opt in enumerate(options[:2]):  # 只显示前2个
                            print(f"    选项{i+1}: display_text='{opt.get('display_text', 'N/A')}', payload='{opt.get('payload', 'N/A')}'")
                
            elif isinstance(response, str):
                print(f"响应是字符串: {response[:100]}...")
            else:
                print(f"响应是其他类型: {response}")
                
        except Exception as e:
            print(f"处理出错: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60 + "\n")

def test_live_api():
    """测试实际的API端点"""
    
    print("=== 测试实际API端点 ===")
    print()
    
    # 测试查询
    test_queries = ["玉米", "蛋", "鸡"]
    
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
                    print(f"  clarification_options存在: {'clarification_options' in data}")
                    print(f"  product_suggestions存在: {'product_suggestions' in data}")
                    
                    if 'clarification_options' in data:
                        options = data['clarification_options']
                        print(f"  clarification_options: {options}")
                        
                print(f"完整响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                print(f"API错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("无法连接到API - 请确保应用正在运行")
        except Exception as e:
            print(f"API测试出错: {e}")
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    test_api_response()
    print("\n" + "="*80 + "\n")
    test_live_api()
