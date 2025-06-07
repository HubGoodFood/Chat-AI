#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI入口点文件
用于Render等部署平台的gunicorn启动
"""

import sys
import os
import logging
import time

# 设置环境变量以优化轻量级模型加载
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('PYTHONUNBUFFERED', '1')
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
os.environ.setdefault('MODEL_TYPE', 'lightweight')
os.environ.setdefault('LAZY_LOADING', 'true')

# 仅在使用重型模型时设置这些变量
if os.environ.get('MODEL_TYPE') != 'lightweight':
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
    os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 确保项目根目录在Python路径中
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    logger.info(f"已添加项目根目录到Python路径: {PROJECT_ROOT}")

def create_fallback_app():
    """创建后备应用"""
    from flask import Flask, jsonify
    fallback_app = Flask(__name__)

    @fallback_app.route('/')
    def health_check():
        return jsonify({
            "status": "starting",
            "message": "应用正在启动中，请稍后再试..."
        }), 503

    @fallback_app.route('/health')
    def health():
        return jsonify({"status": "ok"}), 200

    return fallback_app

def load_main_app():
    """加载主应用，带超时处理"""
    logger.info("正在导入Flask应用...")
    start_time = time.time()

    try:
        from src.app.main import app
        load_time = time.time() - start_time
        logger.info(f"Flask应用导入成功，耗时: {load_time:.2f}秒")
        return app
    except Exception as e:
        load_time = time.time() - start_time
        logger.error(f"导入Flask应用失败 (耗时: {load_time:.2f}秒): {e}")
        raise

# 尝试加载主应用
try:
    app = load_main_app()
    application = app
    logger.info("✅ 主应用加载成功")

except Exception as e:
    logger.error(f"❌ 主应用加载失败，使用后备应用: {e}")
    app = create_fallback_app()
    application = app

if __name__ == '__main__':
    # 本地开发时的启动方式
    port = int(os.environ.get('PORT', 5000))
    app.run(
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true',
        host='0.0.0.0',
        port=port
    )
