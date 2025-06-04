from flask import Flask, request, jsonify, render_template
import os
import re
import csv
import random # Ensure random is imported at the top level
import logging # 新增：导入日志模块
import config # 新增：导入配置文件

from cache_manager import CacheManager
from product_manager import ProductManager
from chat_handler import ChatHandler
from policy_manager import PolicyManager

app = Flask(__name__)

# --- 新增：配置日志 ---
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
# --- 结束：配置日志 ---

logger.info(" Flask app script is starting up... ") # 修改
logger.info(" Flask app object created. ") # 修改

# --- 初始化管理器 ---
cache_manager = CacheManager()
product_manager = ProductManager(cache_manager=cache_manager)
policy_manager = PolicyManager()
# 加载产品数据 (product_manager 内部会处理缓存)
if not product_manager.load_product_data():
    logger.error("应用启动失败：无法加载产品数据。请检查 products.csv 文件和配置。")
    # 在这种情况下，应用可能无法正常工作，可以考虑退出或进入维护模式
    # exit(1) # 或者其他错误处理机制

chat_handler = ChatHandler(product_manager=product_manager,
                           policy_manager=policy_manager,
                           cache_manager=cache_manager)

@app.route('/')
def index():
    """渲染主聊天页面。"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """处理用户发送的聊天消息的API端点。"""
    logger.info("--- Chat route entered ---")
    
    user_input_original = request.json.get('message', '')
    user_id = request.json.get('user_id', 'anonymous')
    
    if not user_input_original:
        return jsonify({'response': "抱歉，我没有收到您的消息。"}), 400

    # 使用 ChatHandler 处理消息
    # ChatHandler 实例已经在全局创建: chat_handler
    final_response = chat_handler.handle_chat_message(user_input_original, user_id)
    
    logger.info(f"最终回复给用户 {user_id}: {final_response}")
    return jsonify({'response': final_response if final_response is not None 
                    else "抱歉，我暂时无法理解您的意思，请换个说法试试？"})

if __name__ == '__main__':
    # 确保 llm_client 在 config.py 中正确初始化并可用
    if not config.DEEPSEEK_API_KEY:
        logger.warning("本地运行警告：未设置 DEEPSEEK_API_KEY 环境变量，DeepSeek API 调用将失败。")
    elif not config.llm_client:
        logger.warning("LLM客户端未成功初始化 (llm_client is None in config)。DeepSeek API 调用将失败。")
        
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
