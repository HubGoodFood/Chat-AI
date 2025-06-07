#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的产品选择流程
"""

import requests
import json
import time

def test_complete_flow():
    """测试完整的产品选择流程"""
    
    print("=== 测试完整产品选择流程 ===")
    print()
    
    base_url = "http://localhost:5000"
    
    # 测试步骤1: 发送模糊查询，应该返回clarification_options
    print("步骤1: 发送模糊查询 '玉米'")
    print("-" * 50)
    
    try:
        response = requests.post(
            f'{base_url}/chat',
            json={'message': '玉米', 'user_id': 'test_user'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("OK 响应成功")
            print(f"  消息: {data.get('message', 'N/A')[:80]}...")

            clarification_options = data.get('clarification_options', [])
            print(f"  clarification_options数量: {len(clarification_options)}")

            if clarification_options:
                print("  选项:")
                for i, option in enumerate(clarification_options):
                    print(f"    {i+1}. {option.get('display_text', 'N/A')} (payload: {option.get('payload', 'N/A')})")

                # 测试步骤2: 选择第一个选项
                print(f"\n步骤2: 选择第一个选项 '{clarification_options[0]['display_text']}'")
                print("-" * 50)

                selection_message = f"product_selection:{clarification_options[0]['payload']}"

                response2 = requests.post(
                    f'{base_url}/chat',
                    json={'message': selection_message, 'user_id': 'test_user'},
                    timeout=10
                )

                if response2.status_code == 200:
                    data2 = response2.json()
                    print("OK 产品选择响应成功")
                    print(f"  消息: {data2.get('message', 'N/A')[:100]}...")

                    # 检查是否包含产品详细信息
                    message = data2.get('message', '')
                    has_price = any(keyword in message for keyword in ['价格', '售价', '元', '$', '¥'])
                    has_description = any(keyword in message for keyword in ['新鲜', '特点', '产地', '重量'])

                    print(f"  包含价格信息: {'是' if has_price else '否'}")
                    print(f"  包含描述信息: {'是' if has_description else '否'}")

                    if has_price and has_description:
                        print("OK 产品详细信息完整")
                    else:
                        print("WARN 产品详细信息可能不完整")

                else:
                    print(f"ERROR 产品选择失败: HTTP {response2.status_code}")
                    print(f"  错误: {response2.text}")

            else:
                print("ERROR 没有返回clarification_options")

        else:
            print(f"ERROR 初始查询失败: HTTP {response.status_code}")
            print(f"  错误: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR 无法连接到API - 请确保应用正在运行")
    except Exception as e:
        print(f"ERROR 测试出错: {e}")
    
    print("\n" + "=" * 60)
    
    # 测试其他查询
    other_queries = ["蛋", "鸡"]
    
    for query in other_queries:
        print(f"\n测试查询: '{query}'")
        print("-" * 30)
        
        try:
            response = requests.post(
                f'{base_url}/chat',
                json={'message': query, 'user_id': 'test_user'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                clarification_options = data.get('clarification_options', [])
                print(f"OK 响应成功，clarification_options数量: {len(clarification_options)}")

                if clarification_options:
                    for i, option in enumerate(clarification_options[:2]):  # 只显示前2个
                        print(f"  {i+1}. {option.get('display_text', 'N/A')}")
                else:
                    print("  没有clarification_options")

            else:
                print(f"ERROR 查询失败: HTTP {response.status_code}")

        except Exception as e:
            print(f"ERROR 查询出错: {e}")

def test_frontend_integration():
    """测试前端集成"""
    
    print("\n=== 前端集成测试说明 ===")
    print()
    print("请在浏览器中测试以下步骤:")
    print("1. 打开 http://localhost:5000")
    print("2. 在聊天框中输入 '玉米'")
    print("3. 检查是否出现选择按钮")
    print("4. 点击任意按钮")
    print("5. 检查是否显示产品详细信息")
    print()
    print("预期结果:")
    print("- 输入 '玉米' 后应该出现2个按钮: '有机农场玉米' 和 '甜心玉米粒罐头'")
    print("- 点击按钮后应该显示对应产品的详细信息（价格、描述等）")
    print("- 按钮点击后应该变灰并禁用")

if __name__ == "__main__":
    test_complete_flow()
    test_frontend_integration()
