#!/usr/bin/env python3
"""
CDN集成
支持多种CDN服务和资源版本管理
"""

import os
import json
from urllib.parse import urljoin
from pathlib import Path

class CDNManager:
    def __init__(self):
        self.cdn_enabled = os.environ.get('CDN_ENABLED', 'false').lower() == 'true'
        self.cdn_base_url = os.environ.get('CDN_BASE_URL', '')
        self.cdn_version = os.environ.get('CDN_VERSION', 'v1')
        self.manifest = self._load_manifest()
    
    def _load_manifest(self):
        """加载资源清单"""
        try:
            manifest_path = Path('static/manifest.json')
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载资源清单失败: {e}")
        return {}
    
    def get_static_url(self, filename):
        """获取静态文件URL"""
        if self.cdn_enabled and self.cdn_base_url:
            return urljoin(self.cdn_base_url, f"{self.cdn_version}/{filename}")
        else:
            return f"/static/{filename}"
    
    def get_versioned_url(self, filename):
        """获取版本化URL"""
        if self.manifest and 'files' in self.manifest and filename in self.manifest['files']:
            versioned_filename = self.manifest['files'][filename]['versioned']
            return self.get_static_url(versioned_filename)
        return self.get_static_url(filename)
    
    def get_optimized_filename(self, filename):
        """获取优化后的文件名"""
        # 检查是否有压缩版本
        if filename.endswith('.css'):
            min_filename = filename.replace('.css', '.min.css')
            if self.manifest and 'files' in self.manifest and min_filename in self.manifest['files']:
                return min_filename
        elif filename.endswith('.js'):
            min_filename = filename.replace('.js', '.min.js')
            if self.manifest and 'files' in self.manifest and min_filename in self.manifest['files']:
                return min_filename
        
        return filename
    
    def get_file_info(self, filename):
        """获取文件信息"""
        if self.manifest and 'files' in self.manifest and filename in self.manifest['files']:
            return self.manifest['files'][filename]
        return None
    
    def reload_manifest(self):
        """重新加载资源清单"""
        self.manifest = self._load_manifest()

# 全局CDN管理器
cdn_manager = CDNManager()

def static_url(filename, use_optimized=True):
    """模板函数：获取静态文件URL"""
    if use_optimized:
        filename = cdn_manager.get_optimized_filename(filename)
    return cdn_manager.get_versioned_url(filename)

def get_asset_info(filename):
    """获取资源信息"""
    return cdn_manager.get_file_info(filename)
