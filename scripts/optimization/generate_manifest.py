#!/usr/bin/env python3
"""
生成资源清单文件
用于版本管理和缓存破坏
"""

import hashlib
import json
import os
from pathlib import Path
from datetime import datetime

def generate_file_hash(file_path):
    """生成文件哈希"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except Exception as e:
        print(f"生成哈希失败 {file_path}: {e}")
        return "00000000"

def get_file_info(file_path):
    """获取文件信息"""
    try:
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'type': get_file_type(file_path.suffix)
        }
    except Exception as e:
        print(f"获取文件信息失败 {file_path}: {e}")
        return {'size': 0, 'modified': '', 'type': 'unknown'}

def get_file_type(extension):
    """根据扩展名确定文件类型"""
    type_map = {
        '.css': 'stylesheet',
        '.js': 'script',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.gif': 'image',
        '.webp': 'image',
        '.svg': 'image',
        '.ico': 'icon',
        '.woff': 'font',
        '.woff2': 'font',
        '.ttf': 'font',
        '.eot': 'font'
    }
    return type_map.get(extension.lower(), 'other')

def generate_manifest():
    """生成资源清单"""
    static_dir = Path('static')
    
    if not static_dir.exists():
        print("static目录不存在")
        return False
    
    manifest = {
        'version': '1.0.0',
        'generated': datetime.now().isoformat(),
        'files': {},
        'stats': {
            'total_files': 0,
            'total_size': 0,
            'by_type': {}
        }
    }
    
    print("扫描静态资源文件...")
    
    # 扫描所有文件
    for file_path in static_dir.rglob('*'):
        if file_path.is_file() and not file_path.name.startswith('.'):
            relative_path = str(file_path.relative_to(static_dir)).replace('\\', '/')
            
            # 跳过临时文件和备份文件
            if any(skip in relative_path for skip in ['.tmp', '.bak', '.old']):
                continue
            
            file_hash = generate_file_hash(file_path)
            file_info = get_file_info(file_path)
            
            # 生成版本化文件名
            name, ext = os.path.splitext(relative_path)
            versioned_name = f"{name}.{file_hash}{ext}"
            
            manifest['files'][relative_path] = {
                'versioned': versioned_name,
                'hash': file_hash,
                'size': file_info['size'],
                'modified': file_info['modified'],
                'type': file_info['type']
            }
            
            # 更新统计信息
            manifest['stats']['total_files'] += 1
            manifest['stats']['total_size'] += file_info['size']
            
            file_type = file_info['type']
            if file_type not in manifest['stats']['by_type']:
                manifest['stats']['by_type'][file_type] = {'count': 0, 'size': 0}
            manifest['stats']['by_type'][file_type]['count'] += 1
            manifest['stats']['by_type'][file_type]['size'] += file_info['size']
            
            print(f"  {relative_path} -> {versioned_name}")
    
    # 保存清单
    manifest_path = static_dir / 'manifest.json'
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"\n资源清单生成完成:")
        print(f"  总文件数: {manifest['stats']['total_files']}")
        print(f"  总大小: {manifest['stats']['total_size']:,} bytes")
        print(f"  清单文件: {manifest_path}")

        # 按类型显示统计
        print(f"  文件类型统计:")
        for file_type, stats in manifest['stats']['by_type'].items():
            print(f"    {file_type}: {stats['count']} 个文件, {stats['size']:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"保存清单失败: {e}")
        return False

if __name__ == "__main__":
    print("开始生成资源清单...")
    success = generate_manifest()
    if success:
        print("资源清单生成完成！")
    else:
        print("资源清单生成失败！")
        exit(1)
