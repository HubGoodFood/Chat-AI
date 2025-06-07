#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政策查询API测试
测试通过HTTP API调用政策查询功能
"""

import requests
import json
import time

def test_policy_api():
    """测试政策查询API"""
    base_url = "http://localhost:5000"
    
    print("[测试] 开始测试政策查询API...")
    
    # 测试1: 政策列表查询
    print("\n[测试1] 政策列表查询")
    try:
        response = requests.post(f"{base_url}/chat", 
                               json={
                                   "message": "你们有什么政策？",
                                   "user_id": "test_api_user"
                               },
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[成功] 状态码: {response.status_code}")
            
            if "message" in data:
                print(f"[消息] {data['message'][:100]}...")
                
                if "product_suggestions" in data and data["product_suggestions"]:
                    suggestions = data["product_suggestions"]
                    print(f"[成功] 返回了 {len(suggestions)} 个政策类别按钮:")
                    for i, suggestion in enumerate(suggestions[:5]):
                        print(f"   {i+1}. {suggestion.get('display_text', 'N/A')}")
                else:
                    print("[错误] 没有返回政策类别按钮")
            else:
                print("[错误] 响应中没有message字段")
        else:
            print(f"[错误] HTTP状态码: {response.status_code}")
            print(f"[错误] 响应内容: {response.text}")
            
    except Exception as e:
        print(f"[错误] 政策列表查询失败: {e}")
    
    # 等待一下
    time.sleep(1)
    
    # 测试2: 政策类别选择
    print("\n[测试2] 政策类别选择")
    try:
        response = requests.post(f"{base_url}/chat", 
                               json={
                                   "message": "policy_category:delivery",
                                   "user_id": "test_api_user"
                               },
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[成功] 状态码: {response.status_code}")
            
            if "message" in data:
                message = data["message"]
                if "配送政策" in message:
                    print("[成功] 返回了配送政策内容")
                    print(f"[内容] {message[:200]}...")
                else:
                    print("[错误] 返回内容不包含配送政策")
                    print(f"[内容] {message[:100]}...")
            else:
                print("[错误] 响应中没有message字段")
        else:
            print(f"[错误] HTTP状态码: {response.status_code}")
            print(f"[错误] 响应内容: {response.text}")
            
    except Exception as e:
        print(f"[错误] 政策类别选择失败: {e}")
    
    # 测试3: 具体政策查询（确保不影响原有功能）
    print("\n[测试3] 具体政策查询")
    try:
        response = requests.post(f"{base_url}/chat", 
                               json={
                                   "message": "配送政策是什么",
                                   "user_id": "test_api_user"
                               },
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[成功] 状态码: {response.status_code}")
            
            if "message" in data:
                message = data["message"]
                if "配送" in message:
                    print("[成功] 返回了配送相关内容")
                    print(f"[内容] {message[:200]}...")
                else:
                    print("[警告] 返回内容可能不相关")
                    print(f"[内容] {message[:100]}...")
            else:
                print("[错误] 响应中没有message字段")
        else:
            print(f"[错误] HTTP状态码: {response.status_code}")
            print(f"[错误] 响应内容: {response.text}")
            
    except Exception as e:
        print(f"[错误] 具体政策查询失败: {e}")
    
    print("\n[完成] 政策查询API测试完成！")

if __name__ == "__main__":
    test_policy_api()
