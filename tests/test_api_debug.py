#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API响应以查看调试信息
"""

import requests
import json

def test_api_with_debug():
    """测试API并查看调试输出"""
    
    print("=== 测试API调试输出 ===")
    
    # 测试查询
    test_queries = ["玉米"]
    
    for query in test_queries:
        print(f"\n测试查询: '{query}'")
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
                print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                print(f"API错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("无法连接到API - 请确保应用正在运行")
        except Exception as e:
            print(f"API测试出错: {e}")

if __name__ == "__main__":
    test_api_with_debug()
