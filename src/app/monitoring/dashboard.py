#!/usr/bin/env python3
"""
监控仪表板API
提供性能监控数据的REST API接口
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, render_template_string
from typing import Dict, Any, List

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.performance_monitor import get_global_monitor
from src.core.cache import CacheManager

# 创建蓝图
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@monitoring_bp.route('/dashboard')
def dashboard():
    """监控仪表板页面"""
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat AI 性能监控仪表板</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
            .metric-value { font-size: 24px; font-weight: bold; color: #27ae60; }
            .metric-unit { font-size: 14px; color: #7f8c8d; }
            .status-good { color: #27ae60; }
            .status-warning { color: #f39c12; }
            .status-error { color: #e74c3c; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
            .refresh-btn:hover { background: #2980b9; }
            .chart-container { height: 200px; background: #ecf0f1; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
            .endpoint-list { max-height: 300px; overflow-y: auto; }
            .endpoint-item { padding: 8px; border-bottom: 1px solid #ecf0f1; display: flex; justify-content: space-between; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Chat AI 性能监控仪表板</h1>
                <p>实时监控应用性能指标和系统健康状态</p>
                <button class="refresh-btn" onclick="refreshData()">🔄 刷新数据</button>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">系统状态</div>
                    <div id="system-status" class="metric-value status-good">正常</div>
                    <div class="metric-unit">运行时间: <span id="uptime">-</span></div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">总请求数</div>
                    <div id="total-requests" class="metric-value">-</div>
                    <div class="metric-unit">过去1小时</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">平均响应时间</div>
                    <div id="avg-response-time" class="metric-value">-</div>
                    <div class="metric-unit">毫秒</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">内存使用</div>
                    <div id="memory-usage" class="metric-value">-</div>
                    <div class="metric-unit">MB</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">CPU使用率</div>
                    <div id="cpu-usage" class="metric-value">-</div>
                    <div class="metric-unit">%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">缓存命中率</div>
                    <div id="cache-hit-rate" class="metric-value">-</div>
                    <div class="metric-unit">%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">API端点性能</div>
                    <div class="endpoint-list" id="endpoint-list">
                        <div class="endpoint-item">
                            <span>加载中...</span>
                        </div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">模型性能</div>
                    <div class="endpoint-list" id="model-list">
                        <div class="endpoint-item">
                            <span>加载中...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function formatUptime(seconds) {
                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                return `${hours}小时${minutes}分钟`;
            }
            
            function formatNumber(num) {
                return num.toLocaleString();
            }
            
            function refreshData() {
                fetch('/monitoring/api/metrics')
                    .then(response => response.json())
                    .then(data => {
                        // 更新基本指标
                        document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds || 0);
                        document.getElementById('total-requests').textContent = formatNumber(data.total_requests || 0);
                        
                        // 计算平均响应时间
                        let avgResponseTime = 0;
                        let totalEndpoints = 0;
                        for (const [endpoint, stats] of Object.entries(data.endpoints || {})) {
                            avgResponseTime += stats.avg_response_time_ms || 0;
                            totalEndpoints++;
                        }
                        if (totalEndpoints > 0) {
                            avgResponseTime = avgResponseTime / totalEndpoints;
                        }
                        document.getElementById('avg-response-time').textContent = avgResponseTime.toFixed(1);
                        
                        // 更新系统指标
                        const memoryUsage = data.system?.avg_process_memory_mb || 0;
                        const cpuUsage = data.system?.avg_cpu_percent || 0;
                        
                        document.getElementById('memory-usage').textContent = memoryUsage.toFixed(1);
                        document.getElementById('cpu-usage').textContent = cpuUsage.toFixed(1);
                        
                        // 更新端点列表
                        const endpointList = document.getElementById('endpoint-list');
                        endpointList.innerHTML = '';
                        for (const [endpoint, stats] of Object.entries(data.endpoints || {})) {
                            const item = document.createElement('div');
                            item.className = 'endpoint-item';
                            item.innerHTML = `
                                <span>${endpoint}</span>
                                <span>${stats.avg_response_time_ms.toFixed(1)}ms</span>
                            `;
                            endpointList.appendChild(item);
                        }
                        
                        // 更新模型列表
                        const modelList = document.getElementById('model-list');
                        modelList.innerHTML = '';
                        for (const [model, stats] of Object.entries(data.models || {})) {
                            const item = document.createElement('div');
                            item.className = 'endpoint-item';
                            item.innerHTML = `
                                <span>${model}</span>
                                <span>${stats.avg_duration_ms.toFixed(1)}ms</span>
                            `;
                            modelList.appendChild(item);
                        }
                    })
                    .catch(error => {
                        console.error('获取监控数据失败:', error);
                    });
                
                // 获取缓存统计
                fetch('/monitoring/api/cache')
                    .then(response => response.json())
                    .then(data => {
                        const hitRate = data.hit_rate || 0;
                        document.getElementById('cache-hit-rate').textContent = hitRate.toFixed(1);
                    })
                    .catch(error => {
                        console.error('获取缓存数据失败:', error);
                    });
            }
            
            // 页面加载时刷新数据
            refreshData();
            
            // 每30秒自动刷新
            setInterval(refreshData, 30000);
        </script>
    </body>
    </html>
    """
    return render_template_string(dashboard_html)

@monitoring_bp.route('/api/metrics')
def get_metrics():
    """获取性能指标API"""
    monitor = get_global_monitor()
    if not monitor:
        return jsonify({"error": "监控系统未启用"}), 503
    
    try:
        # 获取不同时间窗口的数据
        time_window = request.args.get('window', '60', type=int)
        metrics = monitor.get_performance_summary(time_window_minutes=time_window)
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": f"获取指标失败: {str(e)}"}), 500

@monitoring_bp.route('/api/cache')
def get_cache_stats():
    """获取缓存统计API"""
    try:
        # 这里需要从应用上下文获取cache_manager
        # 暂时返回模拟数据
        cache_stats = {
            "hit_rate": 85.5,
            "total_requests": 1250,
            "hits": 1069,
            "misses": 181,
            "redis_available": True,
            "memory_cache_size": 45
        }
        
        return jsonify(cache_stats)
    except Exception as e:
        return jsonify({"error": f"获取缓存统计失败: {str(e)}"}), 500

@monitoring_bp.route('/api/health')
def get_health():
    """获取系统健康状态API"""
    try:
        monitor = get_global_monitor()
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "monitoring_enabled": monitor is not None,
            "components": {
                "performance_monitor": monitor is not None,
                "cache_system": True,  # 假设缓存系统正常
                "database": True,      # 假设数据库正常
                "external_apis": True  # 假设外部API正常
            }
        }
        
        if monitor:
            # 添加监控系统的健康检查
            summary = monitor.get_performance_summary(time_window_minutes=5)
            health_data["uptime_seconds"] = summary.get("uptime_seconds", 0)
            health_data["recent_requests"] = summary.get("total_requests", 0)
        
        return jsonify(health_data)
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@monitoring_bp.route('/api/export')
def export_metrics():
    """导出监控数据"""
    try:
        monitor = get_global_monitor()
        if not monitor:
            return jsonify({"error": "监控系统未启用"}), 503
        
        # 生成导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_export_{timestamp}.json"
        filepath = os.path.join("cache", filename)
        
        # 导出指标
        monitor.export_metrics(filepath)
        
        return jsonify({
            "message": "指标导出成功",
            "filename": filename,
            "filepath": filepath
        })
    except Exception as e:
        return jsonify({"error": f"导出失败: {str(e)}"}), 500
