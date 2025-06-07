#!/usr/bin/env python3
"""
验证浏览器中的优化效果
检查实际加载的文件是否为优化版本
"""

import requests
import time

def check_optimization_in_browser():
    """检查浏览器中的优化效果"""
    base_url = "http://localhost:5000"
    
    print("=" * 60)
    print("验证浏览器中的前端优化效果")
    print("=" * 60)
    
    # 1. 检查主页是否正常加载
    print("1. 检查主页加载...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print(f"  ✓ 主页加载成功 ({len(response.content):,} bytes)")
            
            # 检查HTML中是否包含优化的URL
            html_content = response.text
            if 'static_url_optimized' in html_content or '.min.' in html_content:
                print("  ✓ HTML中包含优化的静态文件引用")
            else:
                print("  ⚠ HTML中可能未使用优化的静态文件引用")
        else:
            print(f"  ✗ 主页加载失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ 主页加载异常: {e}")
        return False
    
    # 2. 检查静态文件的实际加载情况
    print("\n2. 检查静态文件加载...")
    
    static_files = [
        ("/static/style.css", "CSS文件"),
        ("/static/chat.js", "JavaScript文件")
    ]
    
    for file_url, file_type in static_files:
        try:
            # 普通请求
            response = requests.get(base_url + file_url, timeout=10)
            print(f"  {file_type}:")
            print(f"    状态码: {response.status_code}")
            print(f"    大小: {len(response.content):,} bytes")
            print(f"    Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            # 检查是否返回了压缩版本
            content_size = len(response.content)
            if file_url.endswith('.css') and content_size < 8000:  # 原始CSS约10KB
                print("    ✓ 可能返回了压缩版本")
            elif file_url.endswith('.js') and content_size < 8000:  # 原始JS约9KB
                print("    ✓ 可能返回了压缩版本")
            else:
                print("    ⚠ 可能返回了原始版本")
                
        except Exception as e:
            print(f"  ✗ {file_type}加载异常: {e}")
    
    # 3. 检查gzip压缩支持
    print("\n3. 检查Gzip压缩支持...")
    
    headers = {'Accept-Encoding': 'gzip, deflate'}
    
    for file_url, file_type in static_files:
        try:
            response = requests.get(base_url + file_url, headers=headers, timeout=10)
            print(f"  {file_type} (带gzip头):")
            print(f"    Content-Encoding: {response.headers.get('Content-Encoding', 'None')}")
            print(f"    大小: {len(response.content):,} bytes")
            
            if response.headers.get('Content-Encoding') == 'gzip':
                print("    ✓ 成功返回gzip压缩版本")
            else:
                print("    ⚠ 未返回gzip压缩版本")
                
        except Exception as e:
            print(f"  ✗ {file_type}gzip测试异常: {e}")
    
    # 4. 检查缓存头
    print("\n4. 检查缓存头设置...")
    
    for file_url, file_type in static_files:
        try:
            response = requests.get(base_url + file_url, timeout=10)
            cache_control = response.headers.get('Cache-Control', 'None')
            expires = response.headers.get('Expires', 'None')
            etag = response.headers.get('ETag', 'None')
            
            print(f"  {file_type}:")
            print(f"    Cache-Control: {cache_control}")
            print(f"    Expires: {expires}")
            print(f"    ETag: {etag}")
            
            if 'max-age' in cache_control or expires != 'None':
                print("    ✓ 设置了缓存策略")
            else:
                print("    ⚠ 缓存策略可能需要优化")
                
        except Exception as e:
            print(f"  ✗ {file_type}缓存头检查异常: {e}")
    
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)
    
    print("\n📋 如何在浏览器中验证优化效果:")
    print("1. 打开浏览器开发者工具 (F12)")
    print("2. 切换到 Network (网络) 标签")
    print("3. 刷新页面 (Ctrl+F5 或 Cmd+Shift+R)")
    print("4. 查看静态文件的加载大小:")
    print("   - style.css 应该显示约 7KB (压缩后)")
    print("   - chat.js 应该显示约 6.5KB (压缩后)")
    print("   - 如果支持gzip，实际传输大小会更小 (~2KB)")
    print("5. 检查 Response Headers 中的 Cache-Control 设置")
    
    return True

if __name__ == "__main__":
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("服务器运行正常，开始验证...")
            check_optimization_in_browser()
        else:
            print(f"服务器响应异常: {response.status_code}")
    except requests.exceptions.RequestException:
        print("无法连接到服务器 http://localhost:5000")
        print("请确保Flask应用正在运行:")
        print("  python app.py")
