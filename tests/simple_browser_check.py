#!/usr/bin/env python3
"""
简单的浏览器优化验证
"""

import requests

def simple_check():
    """简单检查优化效果"""
    base_url = "http://localhost:5000"
    
    print("检查前端优化效果...")
    print("=" * 50)
    
    # 检查CSS文件
    try:
        css_response = requests.get(f"{base_url}/static/style.css", timeout=10)
        css_size = len(css_response.content)
        print(f"CSS文件大小: {css_size:,} bytes")
        
        if css_size < 8000:  # 小于8KB说明可能是压缩版本
            print("状态: 可能正在使用压缩版本 (原始约10KB)")
        else:
            print("状态: 可能正在使用原始版本")
            
    except Exception as e:
        print(f"CSS检查失败: {e}")
    
    # 检查JS文件
    try:
        js_response = requests.get(f"{base_url}/static/chat.js", timeout=10)
        js_size = len(js_response.content)
        print(f"JS文件大小: {js_size:,} bytes")
        
        if js_size < 8000:  # 小于8KB说明可能是压缩版本
            print("状态: 可能正在使用压缩版本 (原始约9KB)")
        else:
            print("状态: 可能正在使用原始版本")
            
    except Exception as e:
        print(f"JS检查失败: {e}")
    
    # 检查gzip支持
    print("\n检查Gzip压缩...")
    try:
        headers = {'Accept-Encoding': 'gzip, deflate'}
        gzip_response = requests.get(f"{base_url}/static/style.css", headers=headers, timeout=10)
        
        content_encoding = gzip_response.headers.get('Content-Encoding', 'None')
        gzip_size = len(gzip_response.content)
        
        print(f"Content-Encoding: {content_encoding}")
        print(f"Gzip响应大小: {gzip_size:,} bytes")
        
        if content_encoding == 'gzip':
            print("状态: 成功启用Gzip压缩")
        else:
            print("状态: Gzip压缩未启用")
            
    except Exception as e:
        print(f"Gzip检查失败: {e}")
    
    print("\n" + "=" * 50)
    print("验证完成")
    
    print("\n在浏览器中验证:")
    print("1. 按F12打开开发者工具")
    print("2. 切换到Network标签")
    print("3. 刷新页面")
    print("4. 查看style.css和chat.js的文件大小")
    print("   - 如果显示约7KB和6.5KB，说明优化生效")
    print("   - 如果显示约10KB和9KB，说明使用原始文件")

if __name__ == "__main__":
    try:
        # 检查服务器
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            simple_check()
        else:
            print("服务器响应异常")
    except:
        print("无法连接到服务器，请确保应用正在运行:")
        print("python app.py")
