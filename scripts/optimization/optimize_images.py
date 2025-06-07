#!/usr/bin/env python3
"""
图片优化脚本
压缩图片，转换格式，生成WebP版本
"""

import os
from pathlib import Path

def check_pillow():
    """检查Pillow是否已安装"""
    try:
        from PIL import Image
        return True
    except ImportError:
        print("未安装Pillow库")
        print("请运行: pip install Pillow")
        return False

def optimize_image(image_path, quality=85):
    """优化单个图片"""
    try:
        from PIL import Image
        
        print(f"优化 {image_path}")
        
        img = Image.open(image_path)
        original_size = os.path.getsize(image_path)
        
        # 转换为RGB（如果是RGBA）
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # 保存优化版本
        optimized_path = image_path.with_suffix('.optimized' + image_path.suffix)
        img.save(optimized_path, optimize=True, quality=quality)
        
        # 生成WebP版本
        webp_path = image_path.with_suffix('.webp')
        img.save(webp_path, 'WebP', optimize=True, quality=quality)
        
        # 计算压缩率
        optimized_size = os.path.getsize(optimized_path)
        webp_size = os.path.getsize(webp_path)
        
        print(f"  原始: {original_size:,} bytes")
        print(f"  优化: {optimized_size:,} bytes ({(1-optimized_size/original_size)*100:.1f}% 减少)")
        print(f"  WebP: {webp_size:,} bytes ({(1-webp_size/original_size)*100:.1f}% 减少)")
        print(f"  生成文件: {optimized_path.name}, {webp_path.name}")
        
        return original_size, optimized_size, webp_size
        
    except Exception as e:
        print(f"  优化失败: {e}")
        return 0, 0, 0

def optimize_all_images():
    """优化所有图片"""
    if not check_pillow():
        return False
    
    static_dir = Path('static')
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    
    image_files = []
    for ext in image_extensions:
        image_files.extend(static_dir.glob(f'**/*{ext}'))
    
    if not image_files:
        print("未找到图片文件，跳过图片优化")
        return True
    
    total_original_size = 0
    total_optimized_size = 0
    total_webp_size = 0
    processed_count = 0
    
    for image_file in image_files:
        # 跳过已经优化的文件
        if '.optimized' in image_file.name:
            continue
            
        original_size, optimized_size, webp_size = optimize_image(image_file)
        
        if original_size > 0:  # 成功处理
            total_original_size += original_size
            total_optimized_size += optimized_size
            total_webp_size += webp_size
            processed_count += 1
    
    # 总结
    if processed_count > 0:
        print(f"\n图片优化总结:")
        print(f"  处理文件数: {processed_count}")
        print(f"  总原始大小: {total_original_size:,} bytes")
        print(f"  总优化大小: {total_optimized_size:,} bytes")
        print(f"  总WebP大小: {total_webp_size:,} bytes")
        if total_original_size > 0:
            print(f"  优化压缩率: {(1 - total_optimized_size/total_original_size)*100:.1f}%")
            print(f"  WebP压缩率: {(1 - total_webp_size/total_original_size)*100:.1f}%")
    else:
        print("没有图片需要优化")
    
    return True

if __name__ == "__main__":
    print("开始图片优化...")
    success = optimize_all_images()
    if success:
        print("图片优化完成！")
    else:
        print("图片优化失败！")
        exit(1)
