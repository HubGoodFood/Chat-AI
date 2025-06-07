#!/usr/bin/env python3
"""
CSS优化脚本
压缩CSS文件，移除无用代码，生成gzip版本
"""

import os
import re
import gzip
from pathlib import Path

def minify_css(css_content):
    """CSS最小化处理"""
    # 移除注释
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # 移除多余空白
    css_content = re.sub(r'\s+', ' ', css_content)
    css_content = re.sub(r';\s*}', '}', css_content)
    css_content = re.sub(r'{\s*', '{', css_content)
    css_content = re.sub(r'}\s*', '}', css_content)
    css_content = re.sub(r':\s*', ':', css_content)
    css_content = re.sub(r';\s*', ';', css_content)
    css_content = re.sub(r',\s*', ',', css_content)
    
    # 移除行首行尾空白
    css_content = css_content.strip()
    
    return css_content

def optimize_css_files():
    """优化所有CSS文件"""
    static_dir = Path('static')
    css_files = list(static_dir.glob('**/*.css'))
    
    if not css_files:
        print("未找到CSS文件")
        return False
    
    total_original_size = 0
    total_minified_size = 0
    total_gzip_size = 0
    
    for css_file in css_files:
        # 跳过已经压缩的文件
        if '.min.' in css_file.name:
            continue
            
        print(f"优化 {css_file}")
        
        try:
            # 读取原文件
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 压缩
            minified = minify_css(content)
            
            # 保存压缩版本
            minified_path = css_file.with_suffix('.min.css')
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
    print(f"\nCSS优化总结:")
    print(f"  处理文件数: {len([f for f in css_files if '.min.' not in f.name])}")
    print(f"  总原始大小: {total_original_size:,} bytes")
    print(f"  总压缩大小: {total_minified_size:,} bytes")
    print(f"  总Gzip大小: {total_gzip_size:,} bytes")
    if total_original_size > 0:
        print(f"  总压缩率: {(1 - total_minified_size/total_original_size)*100:.1f}%")
        print(f"  总Gzip压缩率: {(1 - total_gzip_size/total_original_size)*100:.1f}%")
    
    return True

if __name__ == "__main__":
    print("开始CSS优化...")
    success = optimize_css_files()
    if success:
        print("CSS优化完成！")
    else:
        print("CSS优化失败！")
        exit(1)
