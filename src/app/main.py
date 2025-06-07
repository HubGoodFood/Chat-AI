import sys
import os
import time
# Add the project root directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, request, jsonify, render_template
# import os # Already imported
import re
import csv
import random # Ensure random is imported at the top level
import logging # 新增：导入日志模块
from src.config import settings as config # Reverted to src.
# import sys # Already imported

from src.core.cache import CacheManager # Reverted to src.
from src.app.products.manager import ProductManager # Reverted to src.
from src.app.chat.handler import ChatHandler # Reverted to src.
from src.app.policy.manager import PolicyManager # Reverted to src.
from src.core.performance_monitor import init_global_monitor, get_global_monitor, monitor_performance

app = Flask(__name__, template_folder='../../templates', static_folder='../../static') # 修改

# --- 新增：配置日志 ---
logging.basicConfig(level=logging.DEBUG, # 修改日志级别为 DEBUG
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
# --- 结束：配置日志 ---

# 注册监控蓝图
try:
    from src.app.monitoring.dashboard import monitoring_bp
    app.register_blueprint(monitoring_bp)
    logger.info("监控仪表板已注册")
except Exception as e:
    logger.warning(f"监控仪表板注册失败: {e}")

logger.info(" Flask app script is starting up... ") # 修改
logger.info(" Flask app object created. ") # 修改

# --- 初始化监控系统 ---
enable_monitoring = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
performance_monitor = init_global_monitor(enable_detailed_monitoring=enable_monitoring)

# --- 初始化管理器 ---
enable_redis = os.environ.get('REDIS_ENABLED', 'true').lower() == 'true'
redis_url = os.environ.get('REDIS_URL')
cache_manager = CacheManager(enable_redis=enable_redis, redis_url=redis_url)
product_manager = ProductManager(cache_manager=cache_manager)
policy_manager = PolicyManager(lazy_load=True)  # 使用懒加载避免启动时超时

# 加载产品数据 (product_manager 内部会处理缓存)
try:
    if not product_manager.load_product_data():
        logger.error("应用启动失败：无法加载产品数据。请检查 products.csv 文件和配置。")
        if os.environ.get('APP_ENV') == 'production':
            logger.critical("生产环境中无法加载产品数据，应用退出")
            sys.exit(1)  # 在生产环境中退出
        else:
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
            chat_handler = None  # 明确设置为 None，后续使用前需要检查

@app.route('/health')
@monitor_performance(performance_monitor, endpoint='/health')
def health_check():
    """健康检查端点"""
    # 获取系统健康状态
    health_status = {
        "status": "ok",
        "message": "应用运行正常",
        "uptime_seconds": time.time() - performance_monitor.start_time,
        "cache": cache_manager.health_check(),
        "monitoring": {
            "enabled": enable_monitoring,
            "stats": performance_monitor.get_performance_summary(time_window_minutes=5)
        }
    }

    return jsonify(health_status), 200

@app.route('/')
def index():
    """渲染主聊天页面。"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.exception(f"渲染首页时发生异常: {e}")
        return "系统维护中，请稍后再试", 500

@app.route('/test_frontend.html')
def test_frontend():
    """提供前端测试页面。"""
    try:
        with open('test_frontend.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.exception(f"提供测试页面时发生异常: {e}")
        return "测试页面不可用", 500

@app.route('/chat', methods=['POST'])
@monitor_performance(performance_monitor, endpoint='/chat')
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
        logger.info(f"回复类型: {type(final_response)}")
        if isinstance(final_response, dict):
            logger.info(f"字典键: {list(final_response.keys())}")
            logger.info(f"clarification_options: {final_response.get('clarification_options', 'N/A')}")
        if isinstance(final_response, dict):
            # 如果 ChatHandler 返回的是字典，假定它已包含 'message' 键
            # 以及可能的 'clarification_options' 或 'product_suggestions'。
            # 前端期望 'message' 和其他选项键在顶层。
            # 我们需要确保 'message' 键存在。
            if 'message' not in final_response:
                if 'clarification_options' in final_response or 'product_suggestions' in final_response:
                    final_response['message'] = "请查看以下选项："
                else:
                    # 对于没有 'message' 且没有已知选项键的字典 (例如空字典)
                    # chat_handler 应该避免返回这种情况。
                    final_response['message'] = "抱歉，处理已完成但未提供具体消息。"
            return jsonify(final_response)
        elif isinstance(final_response, str):
            # 如果 ChatHandler 返回的是字符串，将其包装在 'message' 键中。
            return jsonify({'message': final_response})
        elif final_response is None:
            # 如果 ChatHandler 返回 None (例如，没有特定回复或发生内部错误)。
            return jsonify({'message': "抱歉，我暂时无法理解您的意思，请换个说法试试？"})
        else:
            # 处理来自 chat_handler 的任何其他意外类型。
            logger.error(f"来自ChatHandler的未知响应类型: {type(final_response)}. 原始值: {final_response}")
            return jsonify({'message': "抱歉，系统响应格式异常。"}), 500
                        
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