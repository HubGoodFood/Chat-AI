#!/usr/bin/env python3
"""
JavaScript优化脚本
压缩JS文件，移除无用代码，生成gzip版本
"""

import os
import re
import gzip
from pathlib import Path

def minify_js(js_content):
    """JavaScript最小化（简单版本）"""
    # 移除单行注释（但保留URL中的//）
    js_content = re.sub(r'(?<!:)//.*$', '', js_content, flags=re.MULTILINE)
    
    # 移除多行注释
    js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
    
    # 移除多余空白，但保留字符串内的空白
    lines = js_content.split('\n')
    minified_lines = []
    
    for line in lines:
        # 移除行首行尾空白
        line = line.strip()
        if line:  # 跳过空行
            minified_lines.append(line)
    
    # 合并行，在适当位置添加分号
    js_content = ' '.join(minified_lines)
    
    # 基本的空白压缩
    js_content = re.sub(r'\s*;\s*', ';', js_content)
    js_content = re.sub(r'\s*{\s*', '{', js_content)
    js_content = re.sub(r'\s*}\s*', '}', js_content)
    js_content = re.sub(r'\s*,\s*', ',', js_content)
    js_content = re.sub(r'\s*\(\s*', '(', js_content)
    js_content = re.sub(r'\s*\)\s*', ')', js_content)
    js_content = re.sub(r'\s*=\s*', '=', js_content)
    js_content = re.sub(r'\s*\+\s*', '+', js_content)
    js_content = re.sub(r'\s*-\s*', '-', js_content)
    js_content = re.sub(r'\s*\*\s*', '*', js_content)
    js_content = re.sub(r'\s*\/\s*', '/', js_content)
    js_content = re.sub(r'\s+', ' ', js_content)
    
    return js_content.strip()

def optimize_js_files():
    """优化所有JavaScript文件"""
    static_dir = Path('static')
    js_files = list(static_dir.glob('**/*.js'))
    
    if not js_files:
        print("未找到JavaScript文件")
        return False
    
    total_original_size = 0
    total_minified_size = 0
    total_gzip_size = 0
    
    for js_file in js_files:
        # 跳过已经压缩的文件
        if '.min.' in js_file.name:
            continue
            
        print(f"优化 {js_file}")
        
        try:
            # 读取原文件
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 压缩
            minified = minify_js(content)
            
            # 保存压缩版本
            minified_path = js_file.with_suffix('.min.js')
            with open(minified_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            # 创建gzip版本
            gzip_path = str(minified_path) + '.gz'
            with gzip.open(gzip_path, 'wt', encoding='utf-8') as f:
                f.write(minified)
            
            # 计算大小
            original_size = len(content.encode('utf-8'))
            minified_size = len(minified.encode('utf-8'))
            
            with open(gzip_path, 'rb') as f:
                gzip_size = len(f.read())
            
            total_original_size += original_size
            total_minified_size += minified_size
            total_gzip_size += gzip_size
            
            print(f"  原始大小: {original_size:,} bytes")
            print(f"  压缩大小: {minified_size:,} bytes ({(1 - minified_size/original_size)*100:.1f}% 减少)")
            print(f"  Gzip大小: {gzip_size:,} bytes ({(1 - gzip_size/original_size)*100:.1f}% 减少)")
            print(f"  生成文件: {minified_path.name}, {gzip_path}")
            
        except Exception as e:
            print(f"  优化失败: {e}")
            return False

    # 总结
    print(f"\nJavaScript优化总结:")
    print(f"  处理文件数: {len([f for f in js_files if '.min.' not in f.name])}")
    print(f"  总原始大小: {total_original_size:,} bytes")
    print(f"  总压缩大小: {total_minified_size:,} bytes")
    print(f"  总Gzip大小: {total_gzip_size:,} bytes")
    if total_original_size > 0:
        print(f"  总压缩率: {(1 - total_minified_size/total_original_size)*100:.1f}%")
        print(f"  总Gzip压缩率: {(1 - total_gzip_size/total_original_size)*100:.1f}%")
    
    return True

if __name__ == "__main__":
    print("开始JavaScript优化...")
    success = optimize_js_files()
    if success:
        print("JavaScript优化完成！")
    else:
        print("JavaScript优化失败！")
        exit(1)
