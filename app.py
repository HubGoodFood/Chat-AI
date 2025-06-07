#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI入口点文件
用于Render等部署平台的gunicorn启动
"""

import sys
import os
import logging

# 配置基本日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确保项目根目录在Python路径中
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    logger.info(f"已添加项目根目录到Python路径: {PROJECT_ROOT}")

try:
    # 导入Flask应用实例
    logger.info("正在导入Flask应用...")
    from src.app.main import app
    logger.info("Flask应用导入成功")

    # 为gunicorn提供应用实例
    application = app

except Exception as e:
    logger.error(f"导入Flask应用失败: {e}")
    # 创建一个最基本的Flask应用作为后备
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def health_check():
        return "应用启动中，请稍后再试...", 503

    application = app

if __name__ == '__main__':
    # 本地开发时的启动方式
    port = int(os.environ.get('PORT', 5000))
    app.run(
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true',
        host='0.0.0.0',
        port=port
    )
