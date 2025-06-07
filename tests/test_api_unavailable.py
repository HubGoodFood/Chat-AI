#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API不可用产品的推荐按钮功能
"""

import requests
import json

def test_api_unavailable_products():
    """测试API端点的不可用产品处理"""
    
    print("=== 测试API不可用产品处理 ===")
    print()
    
    # 测试查询 - 使用一个确实不存在的产品
    test_queries = ["有草莓吗？", "想买草莓", "草莓多少钱"]
    
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
                            print(f"       payload: {suggestion.get('payload', 'N/A')}")
                    
                    # 检查clarification_options
                    clarification_options = data.get('clarification_options', [])
                    print(f"  clarification_options数量: {len(clarification_options)}")
                    
                    # 完整响应
                    print(f"\n完整响应:")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                        
            else:
                print(f"API错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("无法连接到API - 请确保应用正在运行")
        except Exception as e:
            print(f"API测试出错: {e}")
        
        print("\n" + "=" * 60 + "\n")

def test_product_selection_api():
    """测试产品选择API流程"""
    
    print("=== 测试产品选择API流程 ===")
    print()
    
    # 步骤1: 查询不可用产品
    print("步骤1: 查询不可用产品 '有草莓吗？'")
    response1 = requests.post(
        'http://localhost:5000/chat',
        json={'message': '有草莓吗？', 'user_id': 'test_user'},
        timeout=10
    )
    
    if response1.status_code == 200:
        data1 = response1.json()
        product_suggestions = data1.get('product_suggestions', [])
        
        if product_suggestions:
            print(f"收到 {len(product_suggestions)} 个产品建议")
            
            # 步骤2: 选择第一个建议
            first_suggestion = product_suggestions[0]
            print(f"\n步骤2: 选择产品 '{first_suggestion['display_text']}'")
            
            selection_message = f"product_selection:{first_suggestion['payload']}"
            response2 = requests.post(
                'http://localhost:5000/chat',
                json={'message': selection_message, 'user_id': 'test_user'},
                timeout=10
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"产品选择响应: {data2.get('message', 'N/A')[:200]}...")
                
                # 检查是否包含产品信息
                message = data2.get('message', '')
                has_price = any(keyword in message for keyword in ['价格', '售价', '元', '$'])
                has_description = any(keyword in message for keyword in ['新鲜', '特点', '产地', '重量'])
                
                print(f"包含价格信息: {'是' if has_price else '否'}")
                print(f"包含描述信息: {'是' if has_description else '否'}")
                
                if has_price and has_description:
                    print("OK 完整的产品选择流程测试成功")
                else:
                    print("WARN 产品信息可能不完整")
            else:
                print(f"ERROR 产品选择失败: {response2.status_code}")
        else:
            print("ERROR 没有收到产品建议")
    else:
        print(f"ERROR 初始查询失败: {response1.status_code}")

if __name__ == "__main__":
    test_api_unavailable_products()
    print("\n" + "="*80 + "\n")
    test_product_selection_api()
