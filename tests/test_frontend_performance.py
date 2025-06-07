#!/usr/bin/env python3
"""
前端性能测试
验证优化效果和功能正确性
"""

import requests
import time
import os
from pathlib import Path

class FrontendPerformanceTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
    
    def test_static_file_loading(self):
        """测试静态文件加载性能"""
        print("测试静态文件加载性能...")
        
        static_files = [
            "/static/style.css",
            "/static/chat.js",
            "/static/style.min.css",
            "/static/chat.min.js"
        ]
        
        for file_url in static_files:
            url = self.base_url + file_url
            
            try:
                # 测试加载时间
                start_time = time.time()
                response = requests.get(url, timeout=10)
                load_time = time.time() - start_time
                
                file_name = file_url.split('/')[-1]
                self.results[file_name] = {
                    'status_code': response.status_code,
                    'size': len(response.content),
                    'load_time': load_time,
                    'cache_control': response.headers.get('Cache-Control', 'None'),
                    'content_type': response.headers.get('Content-Type', 'None')
                }
                
                print(f"  {file_url}:")
                print(f"    状态码: {response.status_code}")
                print(f"    大小: {len(response.content):,} bytes")
                print(f"    加载时间: {load_time:.3f}s")
                print(f"    缓存头: {response.headers.get('Cache-Control', 'None')}")
                print(f"    内容类型: {response.headers.get('Content-Type', 'None')}")
                print()
                
            except Exception as e:
                print(f"  错误 {file_url}: {e}")
                self.results[file_name] = {'error': str(e)}
    
    def test_compression(self):
        """测试压缩效果"""
        print("测试压缩效果...")
        
        # 测试gzip压缩
        headers = {'Accept-Encoding': 'gzip, deflate'}
        
        test_files = ['/static/style.css', '/static/chat.js']
        
        for file_url in test_files:
            url = self.base_url + file_url
            
            try:
                # 不带压缩头的请求
                response_normal = requests.get(url, timeout=10)
                
                # 带压缩头的请求
                response_compressed = requests.get(url, headers=headers, timeout=10)
                
                file_name = file_url.split('/')[-1]
                
                print(f"  {file_url}:")
                print(f"    普通请求大小: {len(response_normal.content):,} bytes")
                print(f"    压缩请求大小: {len(response_compressed.content):,} bytes")
                print(f"    Content-Encoding: {response_compressed.headers.get('Content-Encoding', 'None')}")
                
                if len(response_compressed.content) < len(response_normal.content):
                    compression_ratio = (1 - len(response_compressed.content) / len(response_normal.content)) * 100
                    print(f"    压缩率: {compression_ratio:.1f}%")
                print()
                
            except Exception as e:
                print(f"  错误 {file_url}: {e}")
    
    def test_cache_headers(self):
        """测试缓存头设置"""
        print("测试缓存头设置...")
        
        test_files = ['/static/style.css', '/static/chat.js']
        
        for file_url in test_files:
            url = self.base_url + file_url
            
            try:
                response = requests.get(url, timeout=10)
                
                print(f"  {file_url}:")
                print(f"    Cache-Control: {response.headers.get('Cache-Control', 'None')}")
                print(f"    Expires: {response.headers.get('Expires', 'None')}")
                print(f"    ETag: {response.headers.get('ETag', 'None')}")
                print(f"    Last-Modified: {response.headers.get('Last-Modified', 'None')}")
                print()
                
            except Exception as e:
                print(f"  错误 {file_url}: {e}")
    
    def test_main_page_performance(self):
        """测试主页加载性能"""
        print("测试主页加载性能...")
        
        try:
            start_time = time.time()
            response = requests.get(self.base_url, timeout=10)
            load_time = time.time() - start_time
            
            print(f"  主页状态码: {response.status_code}")
            print(f"  主页大小: {len(response.content):,} bytes")
            print(f"  主页加载时间: {load_time:.3f}s")
            print(f"  内容类型: {response.headers.get('Content-Type', 'None')}")
            print()
            
        except Exception as e:
            print(f"  主页加载错误: {e}")
    
    def compare_file_sizes(self):
        """比较文件大小"""
        print("比较文件大小...")
        
        static_dir = Path('static')
        
        comparisons = [
            ('style.css', 'style.min.css'),
            ('chat.js', 'chat.min.js')
        ]
        
        for original, minified in comparisons:
            original_path = static_dir / original
            minified_path = static_dir / minified
            
            if original_path.exists() and minified_path.exists():
                original_size = original_path.stat().st_size
                minified_size = minified_path.stat().st_size
                compression_ratio = (1 - minified_size / original_size) * 100
                
                print(f"  {original} vs {minified}:")
                print(f"    原始大小: {original_size:,} bytes")
                print(f"    压缩大小: {minified_size:,} bytes")
                print(f"    压缩率: {compression_ratio:.1f}%")
                print()
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("前端性能测试开始")
        print("=" * 60)
        
        self.compare_file_sizes()
        self.test_static_file_loading()
        self.test_compression()
        self.test_cache_headers()
        self.test_main_page_performance()
        
        print("=" * 60)
        print("前端性能测试完成")
        print("=" * 60)
        
        return self.results

if __name__ == "__main__":
    # 检查服务器是否运行
    test_url = "http://localhost:5000"
    
    try:
        response = requests.get(test_url + "/health", timeout=5)
        if response.status_code == 200:
            print("服务器运行正常，开始测试...")
            tester = FrontendPerformanceTest(test_url)
            results = tester.run_all_tests()
        else:
            print(f"服务器响应异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"无法连接到服务器 {test_url}")
        print("请确保Flask应用正在运行:")
        print("  python app.py")
        print(f"错误: {e}")
