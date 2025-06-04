from flask import Flask, request, jsonify, render_template
import os
import re
import csv
import random # Ensure random is imported at the top level
import logging # 新增：导入日志模块
import config # 新增：导入配置文件
import sys  # 导入sys模块用于错误处理

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
try:
    if not product_manager.load_product_data():
        logger.error("应用启动失败：无法加载产品数据。请检查 products.csv 文件和配置。")
        # 在这种情况下，应用可能无法正常工作，可以考虑退出或进入维护模式
        if os.environ.get('APP_ENV') == 'production':
            logger.critical("生产环境中无法加载产品数据，应用退出")
            sys.exit(1)  # 在生产环境中退出
        else: # 这个else属于上面的if
            logger.warning("开发环境中无法加载产品数据，继续运行但功能可能受限")
except Exception as e:
    logger.exception(f"加载产品数据时发生致命异常: {e}")
    if os.environ.get('APP_ENV') == 'production':
        logger.critical("生产环境中加载产品数据异常导致应用退出")
        sys.exit(1)  # 在生产环境中退出
    else:
        logger.warning("开发环境中加载产品数据异常，继续运行但功能可能受限")

# 初始化聊天处理器
try:
    chat_handler = ChatHandler(product_manager=product_manager,
                               policy_manager=policy_manager,
                               cache_manager=cache_manager)
    logger.info("聊天处理器初始化成功")
except Exception as e:
    logger.exception(f"初始化聊天处理器时发生异常: {e}")
    if os.environ.get('APP_ENV') == 'production':
        logger.critical("生产环境中初始化聊天处理器异常，应用退出")
        sys.exit(1)  # 在生产环境中退出
    else:
        # 在开发环境中，尝试使用最基本的配置初始化
        logger.warning("尝试使用基本配置初始化聊天处理器")
        try:
            chat_handler = ChatHandler(product_manager=product_manager)
            logger.info("已使用基本配置成功初始化聊天处理器。")
        except Exception as basic_init_e:
            logger.exception(f"使用基本配置初始化聊天处理器也失败: {basic_init_e}")
            logger.critical("无法初始化聊天处理器，应用将无法处理聊天。请检查配置。")
            chat_handler = None # 明确设置为 None，后续使用前需要检查

@app.route('/')
def index():
    """渲染主聊天页面。"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.exception(f"渲染首页时发生异常: {e}")
        return "系统维护中，请稍后再试", 500

@app.route('/chat', methods=['POST'])
def chat():
    """处理用户发送的聊天消息的API端点。"""
    logger.info("--- Chat route entered ---")
    
    try:
        # 获取并验证输入
        data = request.get_json()
        if not data:
            logger.warning("接收到无效的JSON数据")
            return jsonify({'response': "抱歉，请求格式不正确。"}), 400
            
        user_input_original = data.get('message', '')
        user_id = data.get('user_id', 'anonymous')
        
        if not user_input_original:
            logger.warning(f"用户 {user_id} 发送了空消息")
            return jsonify({'response': "抱歉，我没有收到您的消息。"}), 400

        # 使用 ChatHandler 处理消息
        # ChatHandler 实例已经在全局创建: chat_handler
        final_response = chat_handler.handle_chat_message(user_input_original, user_id)
        
        logger.info(f"最终回复给用户 {user_id}: {final_response}")
        return jsonify({'response': final_response if final_response is not None 
                        else "抱歉，我暂时无法理解您的意思，请换个说法试试？"})
                        
    except Exception as e:
        logger.exception(f"处理聊天请求时发生异常: {e}")
        return jsonify({'response': "抱歉，系统暂时遇到了问题，请稍后再试。"}), 500

@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404错误: {request.path}")
    return jsonify({'error': '请求的资源不存在'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500错误: {str(e)}")
    return jsonify({'error': '服务器内部错误，请稍后再试'}), 500

if __name__ == '__main__':
    # 确保 llm_client 在 config.py 中正确初始化并可用
    if not config.DEEPSEEK_API_KEY:
        logger.warning("本地运行警告：未设置 DEEPSEEK_API_KEY 环境变量，DeepSeek API 调用将失败。")
    elif not config.llm_client:
        logger.warning("LLM客户端未成功初始化 (llm_client is None in config)。DeepSeek API 调用将失败。")
        
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true', 
                host='0.0.0.0', 
                port=port)
    except Exception as e:
        logger.exception(f"启动Flask应用时发生异常: {e}")
        sys.exit(1)
