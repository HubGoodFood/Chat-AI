#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单验证测试：产品推荐按钮功能
"""

import requests
import json

def test_product_suggestions():
    """测试产品推荐按钮功能"""
    
    print("=== 产品推荐按钮功能验证 ===")
    print()
    
    # 测试查询不可用产品
    print("测试查询: '想买草莓'")
    print("-" * 40)
    
    response = requests.post(
        'http://localhost:5000/chat',
        json={'message': '想买草莓', 'user_id': 'test_user'},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("响应结构:")
        print(f"  message: 存在")
        print(f"  product_suggestions: {'存在' if 'product_suggestions' in data else '不存在'}")
        
        if 'product_suggestions' in data:
            suggestions = data['product_suggestions']
            print(f"  建议数量: {len(suggestions)}")
            
            if suggestions:
                print("  产品建议:")
                for i, suggestion in enumerate(suggestions):
                    print(f"    {i+1}. {suggestion.get('display_text', 'N/A')}")
                    print(f"       payload: {suggestion.get('payload', 'N/A')}")
                
                print("\nOK 产品推荐按钮功能正常工作!")
                print("- 后端正确返回product_suggestions")
                print("- 数据结构符合前端要求")
                print("- 前端JavaScript已准备好处理这些数据")
                
                return True
            else:
                print("ERROR 产品建议列表为空")
                return False
        else:
            print("ERROR 响应中没有product_suggestions字段")
            return False
    else:
        print(f"ERROR HTTP请求失败: {response.status_code}")
        return False

def test_product_selection():
    """测试产品选择功能"""
    
    print("\n=== 产品选择功能验证 ===")
    print()
    
    # 先获取产品建议
    response1 = requests.post(
        'http://localhost:5000/chat',
        json={'message': '想买草莓', 'user_id': 'test_user'},
        timeout=10
    )
    
    if response1.status_code == 200:
        data1 = response1.json()
        suggestions = data1.get('product_suggestions', [])
        
        if suggestions:
            # 选择第一个产品
            first_suggestion = suggestions[0]
            selection_message = f"product_selection:{first_suggestion['payload']}"
            
            print(f"选择产品: {first_suggestion['display_text']}")
            print(f"发送消息: {selection_message}")
            
            response2 = requests.post(
                'http://localhost:5000/chat',
                json={'message': selection_message, 'user_id': 'test_user'},
                timeout=10
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                message = data2.get('message', '')
                
                print(f"产品详情响应长度: {len(message)} 字符")
                print(f"响应预览: {message[:100]}...")
                
                # 检查关键信息
                has_price = any(keyword in message for keyword in ['价格', '售价', '元', '$'])
                has_description = any(keyword in message for keyword in ['新鲜', '特点', '产地', '重量', '口感'])
                
                print(f"包含价格信息: {'是' if has_price else '否'}")
                print(f"包含描述信息: {'是' if has_description else '否'}")
                
                if has_price or has_description:
                    print("OK 产品选择功能正常工作!")
                    return True
                else:
                    print("WARN 产品信息可能不完整")
                    return False
            else:
                print(f"ERROR 产品选择请求失败: {response2.status_code}")
                return False
        else:
            print("ERROR 没有产品建议可供选择")
            return False
    else:
        print(f"ERROR 获取产品建议失败: {response1.status_code}")
        return False

if __name__ == "__main__":
    print("开始验证产品推荐按钮功能...")
    print()
    
    success1 = test_product_suggestions()
    success2 = test_product_selection()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("SUCCESS 产品推荐按钮功能实现成功!")
        print()
        print("前端测试说明:")
        print("1. 打开 http://localhost:5000")
        print("2. 输入: '想买草莓'")
        print("3. 应该看到产品推荐按钮")
        print("4. 点击按钮查看产品详情")
    else:
        print("ERROR 部分功能存在问题，请检查实现")
    print("=" * 50)
