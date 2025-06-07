#!/usr/bin/env python3
"""
简化的前端优化测试
验证基本功能和文件大小
"""

import os
from pathlib import Path

def test_file_optimization():
    """测试文件优化结果"""
    print("=" * 50)
    print("前端优化验证测试")
    print("=" * 50)
    
    static_dir = Path('static')
    
    # 检查优化文件是否存在
    files_to_check = [
        ('style.css', 'style.min.css'),
        ('chat.js', 'chat.min.js'),
        ('style.min.css.gz', None),
        ('chat.min.js.gz', None),
        ('manifest.json', None)
    ]
    
    print("1. 检查优化文件存在性:")
    for original, optimized in files_to_check:
        if optimized:
            original_path = static_dir / original
            optimized_path = static_dir / optimized
            
            if original_path.exists() and optimized_path.exists():
                original_size = original_path.stat().st_size
                optimized_size = optimized_path.stat().st_size
                compression_ratio = (1 - optimized_size / original_size) * 100
                
                print(f"  成功 {original} -> {optimized}")
                print(f"    原始: {original_size:,} bytes")
                print(f"    优化: {optimized_size:,} bytes")
                print(f"    压缩率: {compression_ratio:.1f}%")
            else:
                print(f"  失败 {original} -> {optimized} (文件不存在)")
        else:
            file_path = static_dir / original
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"  存在 {original} ({file_size:,} bytes)")
            else:
                print(f"  缺失 {original} (文件不存在)")
        print()
    
    # 检查清单文件内容
    print("2. 检查资源清单:")
    manifest_path = static_dir / 'manifest.json'
    if manifest_path.exists():
        import json
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            print(f"  版本: {manifest.get('version', 'N/A')}")
            print(f"  生成时间: {manifest.get('generated', 'N/A')}")
            print(f"  文件数量: {manifest.get('stats', {}).get('total_files', 0)}")
            print(f"  总大小: {manifest.get('stats', {}).get('total_size', 0):,} bytes")
            
            if 'files' in manifest:
                print("  文件列表:")
                for filename, info in manifest['files'].items():
                    print(f"    {filename} -> {info.get('versioned', 'N/A')}")
        except Exception as e:
            print(f"  清单文件解析失败: {e}")
    else:
        print("  清单文件不存在")
    
    print()
    
    # 计算总体优化效果
    print("3. 总体优化效果:")
    
    original_total = 0
    optimized_total = 0
    
    # CSS文件
    css_original = static_dir / 'style.css'
    css_optimized = static_dir / 'style.min.css'
    if css_original.exists() and css_optimized.exists():
        original_total += css_original.stat().st_size
        optimized_total += css_optimized.stat().st_size
    
    # JS文件
    js_original = static_dir / 'chat.js'
    js_optimized = static_dir / 'chat.min.js'
    if js_original.exists() and js_optimized.exists():
        original_total += js_original.stat().st_size
        optimized_total += js_optimized.stat().st_size
    
    if original_total > 0:
        total_compression = (1 - optimized_total / original_total) * 100
        print(f"  原始总大小: {original_total:,} bytes")
        print(f"  优化总大小: {optimized_total:,} bytes")
        print(f"  总压缩率: {total_compression:.1f}%")
        print(f"  节省空间: {original_total - optimized_total:,} bytes")
    
    # 检查gzip文件
    print("\n4. Gzip压缩文件:")
    gzip_files = list(static_dir.glob('*.gz'))
    if gzip_files:
        for gzip_file in gzip_files:
            gzip_size = gzip_file.stat().st_size
            print(f"  {gzip_file.name}: {gzip_size:,} bytes")
    else:
        print("  未找到gzip文件")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_file_optimization()
