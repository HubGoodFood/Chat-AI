# config.py
import os
from dotenv import load_dotenv  # 加载 .env 文件中的环境变量
load_dotenv()

# --- 模糊匹配配置 ---
FUZZY_MATCH_THRESHOLD = 0.6
MIN_SUBSTRING_MATCH_LENGTH = 2

# --- 产品查询与澄清逻辑配置 ---
MIN_ACCEPTABLE_MATCH_SCORE = 0.4  # 模糊匹配产品名称时，可接受的最低匹配分数
PRICE_OR_BUY_CLARIFICATION_CANDIDATE_THRESHOLD = 0.65  # 当多个产品匹配得分高于此阈值时，可能会触发用户澄清 (降低以增加澄清机会)
DOMINANT_MATCH_THRESHOLD = 0.80  # 如果最相关的产品匹配得分高于此阈值，并且显著优于其他产品，则可能直接选择该产品而无需澄清 (降低以增加澄清机会)
SIGNIFICANT_SCORE_DIFFERENCE = 0.15  # 如果最高匹配得分与次高匹配得分之间的差异大于此值，则认为最高匹配是显著更优的
MAX_CLARIFICATION_OPTIONS = 3  # 在向用户请求澄清时，最多提供的产品选项数量
MAX_PRODUCT_SUGGESTIONS_BUTTONS = 3 # 在推荐产品时，最多提供的按钮数量
# --- 意图关键词 --- 
BUY_INTENT_KEYWORDS = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只", "卖"]
PRICE_QUERY_KEYWORDS = ["多少钱", "价格是", "什么价", "价钱"]
WHAT_DO_YOU_SELL_KEYWORDS = ["卖什么", "有什么产品", "商品列表", "菜单", "有哪些东西", "有什么卖"]
RECOMMEND_KEYWORDS = ["推荐", "介绍点", "什么好吃", "什么值得买", "有什么好", "当季", "新鲜"]
FOLLOW_UP_KEYWORDS = ["它", "这个", "那个", "这", "那", "刚才", "刚刚"]
GENERAL_QUERY_KEYWORDS = ["有", "有没有", "卖不卖", "是不是", "有没有卖"]

# --- 平台政策关键词 ---
POLICY_KEYWORD_MAP = {
    "delivery": ["配送", "送货", "运费", "截单"],
    "refund": ["退款", "退货", "质量", "credit"],
    "payment": ["付款", "支付", "venmo", "汇款"],
    "pickup": ["取货", "自取", "取货点", "地址"]
}

POLICY_FILE = os.getenv("POLICY_FILE", "policy.md")

# --- 产品类别关键词 ---
FRUIT_KEYWORDS = ["苹果", "梨", "香蕉", "橙子", "橘子", "柚子", "葡萄", "西瓜", "哈密瓜", "草莓", "蓝莓",
                "桃", "李子", "杏", "樱桃", "石榴", "山楂", "柿子", "猕猴桃", "菠萝", "芒果", "荔枝", "龙眼",
                "榴莲", "木瓜", "枇杷", "山竹", "椰子", "甘蔗", "柑橘", "金橘", "枣", "无花果", "杨梅", "柠檬"]

VEGETABLE_KEYWORDS = ["白菜", "卷心菜", "生菜", "菠菜", "空心菜", "韭菜", "芹菜", "茼蒿", "油菜", "花椰菜",
                    "西兰花", "芦笋", "竹笋", "藕", "土豆", "红薯", "山药", "芋头", "茄子", "辣椒", "青椒",
                    "番茄", "黄瓜", "冬瓜", "南瓜", "丝瓜", "苦瓜", "豆角", "豌豆", "蚕豆", "毛豆", "莲子",
                    "玉米", "洋葱", "大蒜", "生姜", "胡萝卜", "白萝卜", "芥菜", "莴笋", "香菜", "葱", "蒜", "姜"]

CATEGORY_KEYWORD_MAP = {
    "水果": ["果", "莓", "橙", "桃", "芒", "龙眼", "荔枝", "凤梨", "葡萄", "石榴", "山楂", "芭乐", "瓜",
            "苹果", "梨", "柑橘", "香蕉", "菠萝", "李子", "樱桃", "蓝莓", "草莓", "猕猴桃"],
    "蔬菜": ["菜", "瓜", "菇", "笋", "姜", "菠菜", "花苔", "萝卜", "南瓜", "玉米", "花生",
            "白菜", "茄子", "土豆", "黄瓜", "豆角", "番茄", "洋葱", "芹菜", "生菜"],
    "禽类": ["鸡", "鸭", "鹅", "鸽子", "禽", "家禽", "散养", "走地"],
    "海鲜": ["鱼", "虾", "螺", "蛏", "蛤", "海鲜", "水产", "河鲜", "贝", "蟹"],
    "熟食面点": ["饺", "饼", "爪", "包子", "花卷", "生煎", "燕丸", "火烧", "馄炖", "粽", "面", "小吃", "点心"],
    "蛋类": ["蛋", "鸡蛋", "鸭蛋", "皮蛋", "咸蛋"]
}

# --- LLM 模型参数 ---
LLM_MAX_TOKENS = 1500
LLM_TEMPERATURE = 0.5
LLM_MODEL_NAME = "deepseek-ai/DeepSeek-V3-0324" # 模型名称

# --- API 配置 ---
# DEEPSEEK_API_KEY 从环境变量 `os.getenv('DEEPSEEK_API_KEY')` 读取
# 在 app.py 中处理，这里仅作说明
DEEPSEEK_BASE_URL = "https://llm.chutes.ai/v1"

# --- 其他配置 ---

# 允许通过环境变量自定义产品 CSV 路径，默认使用仓库根目录下的 products.csv
PRODUCT_DATA_FILE = os.getenv("PRODUCT_DATA_FILE", "products.csv")

# --- LLM Client Initialization ---
from openai import OpenAI # 确保 openai 库被导入
import logging

# 获取一个logger实例，可以与app.py中的logger区分开，或者使用相同的配置
# 为了简单起见，这里我们创建一个新的，或者您可以从主应用传递logger配置
config_logger = logging.getLogger(__name__) # 使用 __name__ 会得到 'config' logger
# 如果希望它能输出，需要确保这个logger被配置了handler和level
# 例如，可以在 app.py 初始化日志后，也为这个logger配置
# logging.getLogger('config').setLevel(logging.INFO) # 示例

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
llm_client = None

if not DEEPSEEK_API_KEY:
    config_logger.warning("配置警告：未找到 DEEPSEEK_API_KEY 环境变量。DeepSeek API 将无法使用。")
else:
    try:
        llm_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL # DEEPSEEK_BASE_URL 已在文件上方定义
        )
        config_logger.info(f"LLM 客户端已成功配置 (config.py)，指向: {DEEPSEEK_BASE_URL}")
    except Exception as e:
        config_logger.error(f"在 config.py 中配置 LLM 客户端失败: {e}")
        llm_client = None # 确保在失败时 llm_client 是 None 