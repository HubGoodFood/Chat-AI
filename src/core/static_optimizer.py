#!/usr/bin/env python3
"""
静态文件优化服务
自动选择最优的静态文件版本（压缩、gzip、WebP等）
"""

import os
from flask import send_from_directory, request, abort
from .cache_headers import add_cache_headers, get_content_type

class StaticOptimizer:
    def __init__(self, static_folder):
        self.static_folder = static_folder
    
    def serve_optimized_static(self, filename):
        """提供优化的静态文件服务"""
        print(f"[DEBUG] 请求静态文件: {filename}")
        try:
            # 检查文件是否存在
            original_path = os.path.join(self.static_folder, filename)
            if not os.path.exists(original_path):
                print(f"[DEBUG] 文件不存在: {original_path}")
                abort(404)
            
            # 1. 检查是否支持gzip并且有gzip版本
            if self._supports_gzip():
                gzip_response = self._try_serve_gzip(filename)
                if gzip_response:
                    return gzip_response
            
            # 2. 检查是否支持WebP（仅对图片）
            if self._supports_webp() and self._is_image(filename):
                webp_response = self._try_serve_webp(filename)
                if webp_response:
                    return webp_response
            
            # 3. 检查是否有压缩版本（CSS/JS）
            if self._is_compressible(filename):
                print(f"[DEBUG] 尝试提供压缩版本: {filename}")
                minified_response = self._try_serve_minified(filename)
                if minified_response:
                    print(f"[DEBUG] 成功提供压缩版本: {filename}")
                    return minified_response
                else:
                    print(f"[DEBUG] 压缩版本不存在: {filename}")
            
            # 4. 提供原始文件
            return self._serve_with_cache(filename)
            
        except Exception as e:
            print(f"提供静态文件时出错 {filename}: {e}")
            abort(500)
    
    def _supports_gzip(self):
        """检查客户端是否支持gzip"""
        accept_encoding = request.headers.get('Accept-Encoding', '')
        return 'gzip' in accept_encoding.lower()
    
    def _supports_webp(self):
        """检查客户端是否支持WebP"""
        accept = request.headers.get('Accept', '')
        return 'image/webp' in accept.lower()
    
    def _is_image(self, filename):
        """检查是否为图片文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def _is_compressible(self, filename):
        """检查是否为可压缩的文件类型"""
        compressible_extensions = ['.css', '.js']
        return any(filename.lower().endswith(ext) for ext in compressible_extensions)
    
    def _try_serve_gzip(self, filename):
        """尝试提供gzip压缩版本"""
        # 首先尝试压缩文件的gzip版本
        if self._is_compressible(filename):
            min_filename = self._get_minified_filename(filename)
            gzip_path = os.path.join(self.static_folder, min_filename + '.gz')
            if os.path.exists(gzip_path):
                response = send_from_directory(self.static_folder, min_filename + '.gz')
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Type'] = get_content_type(filename)
                response.headers['Vary'] = 'Accept-Encoding'
                return add_cache_headers(response, 'static')
        
        # 然后尝试原文件的gzip版本
        gzip_path = os.path.join(self.static_folder, filename + '.gz')
        if os.path.exists(gzip_path):
            response = send_from_directory(self.static_folder, filename + '.gz')
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Type'] = get_content_type(filename)
            response.headers['Vary'] = 'Accept-Encoding'
            return add_cache_headers(response, 'static')
        
        return None
    
    def _try_serve_webp(self, filename):
        """尝试提供WebP版本"""
        name, ext = os.path.splitext(filename)
        webp_filename = name + '.webp'
        webp_path = os.path.join(self.static_folder, webp_filename)
        
        if os.path.exists(webp_path):
            response = send_from_directory(self.static_folder, webp_filename)
            response.headers['Vary'] = 'Accept'
            return add_cache_headers(response, 'static')
        
        return None
    
    def _try_serve_minified(self, filename):
        """尝试提供压缩版本"""
        min_filename = self._get_minified_filename(filename)
        min_path = os.path.join(self.static_folder, min_filename)
        
        if os.path.exists(min_path):
            response = send_from_directory(self.static_folder, min_filename)
            return add_cache_headers(response, 'static')
        
        return None
    
    def _get_minified_filename(self, filename):
        """获取压缩文件名"""
        if filename.endswith('.css'):
            return filename.replace('.css', '.min.css')
        elif filename.endswith('.js'):
            return filename.replace('.js', '.min.js')
        return filename
    
    def _serve_with_cache(self, filename):
        """提供带缓存头的原始文件"""
        response = send_from_directory(self.static_folder, filename)
        return add_cache_headers(response, 'static')
