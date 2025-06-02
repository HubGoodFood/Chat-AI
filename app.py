from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI # ADDED for DeepSeek (OpenAI compatible)
import re
import csv
import random # Ensure random is imported at the top level

app = Flask(__name__)
print(" Flask app script is starting up... ")
print(" Flask app object created. ")

# --- ADDED DeepSeek API Key and Client Initialization ---
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1" # As per user info

llm_client = None
if not DEEPSEEK_API_KEY:
    print("警告：未找到 DEEPSEEK_API_KEY 环境变量。DeepSeek API 将无法使用。")
else:
    try:
        llm_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        print(f"--- OpenAI client configured for DeepSeek API at {DEEPSEEK_BASE_URL} ---")
    except Exception as e:
        print(f"配置 DeepSeek API 客户端失败: {e}")
        llm_client = None

# 全局变量来存储产品数据
PRODUCT_CATALOG = {}
PRODUCT_CATEGORIES = {} # 用于存储每个类别的产品列表
ALL_PRODUCT_KEYWORDS = [] # 用于存储所有产品关键词
last_identified_product_key_for_context = None # 用于存储上一个明确处理的产品的key
# 添加用户历史记录和热门商品跟踪
USER_HISTORY = {} # 简单的用户历史记录 {user_id: [product_keys]}
POPULAR_PRODUCTS = {} # 热门商品计数 {product_key: count}
SEASONAL_PRODUCTS = [] # 当季/推荐商品列表

# 类别关键词映射字典，用于辅助分类识别
category_keywords = {
    "水果": ["果", "莓", "橙", "桃", "芒", "龙眼", "荔枝", "凤梨", "葡萄", "石榴", "山楂", "芭乐", "瓜", 
            "苹果", "梨", "柑橘", "香蕉", "菠萝", "李子", "樱桃", "蓝莓", "草莓", "猕猴桃"],
    "蔬菜": ["菜", "瓜", "菇", "笋", "姜", "菠菜", "花苔", "萝卜", "南瓜", "玉米", "花生", 
            "白菜", "茄子", "土豆", "黄瓜", "豆角", "番茄", "洋葱", "芹菜", "生菜"],
    "禽类": ["鸡", "鸭", "鹅", "鸽子", "禽", "家禽", "散养", "走地"],
    "海鲜": ["鱼", "虾", "螺", "蛏", "蛤", "海鲜", "水产", "河鲜", "贝", "蟹"],
    "熟食面点": ["饺", "饼", "爪", "包子", "花卷", "生煎", "燕丸", "火烧", "馄炖", "粽", "面", "小吃", "点心"],
    "蛋类": ["蛋", "鸡蛋", "鸭蛋", "皮蛋", "咸蛋"]
}

def load_product_data(file_path="products.csv"): 
    print(f"Attempting to load product data from {file_path}...") 
    global PRODUCT_CATALOG, PRODUCT_CATEGORIES, ALL_PRODUCT_KEYWORDS, SEASONAL_PRODUCTS
    PRODUCT_CATALOG = {}
    PRODUCT_CATEGORIES = {} 
    ALL_PRODUCT_KEYWORDS = [] 
    SEASONAL_PRODUCTS = []
    expected_headers = ['ProductName', 'Specification', 'Price', 'Unit', 'Category', 'Description', 'IsSeasonal'] # 更新期望的列标题
    try:
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile: 
            reader = csv.DictReader(csvfile)
            print(f"--- DEBUG: CSV Headers read by DictReader: {reader.fieldnames} ---") 
            # 检查是否有新增的可选列
            has_description = 'Description' in (reader.fieldnames or [])
            has_seasonal = 'IsSeasonal' in (reader.fieldnames or [])
            
            if not reader.fieldnames or not all(col in reader.fieldnames for col in ['ProductName', 'Specification', 'Price', 'Unit', 'Category']):
                print(f"错误: CSV文件 {file_path} 的基本列标题不正确。必须包含: ProductName, Specification, Price, Unit, Category")
                return
            
            for row_num, row in enumerate(reader, 1): 
                try:
                    product_name = row['ProductName'].strip()
                    specification = row['Specification'].strip()
                    price_str = row['Price'].strip()
                    unit = row['Unit'].strip()
                    category = row['Category'].strip() # 读取Category列
                    # 读取可选列
                    description = row.get('Description', '').strip() if has_description else ""
                    is_seasonal = row.get('IsSeasonal', '').strip().lower() in ['true', 'yes', '1', 'y'] if has_seasonal else False

                    if not product_name or not price_str or not specification or not unit or not category:
                        print(f"警告: CSV文件第 {row_num+1} 行数据不完整（包含Category），已跳过: {row}")
                        continue
                    price = float(price_str)
                    unique_product_key = product_name
                    if specification and specification.lower() != unit.lower() and specification not in product_name:
                        unique_product_key = f"{product_name} ({specification})"
                    
                    PRODUCT_CATALOG[unique_product_key.lower()] = {
                        'name': product_name, 
                        'specification': specification, 
                        'price': price, 
                        'unit': unit, 
                        'category': category, # 存储Category信息
                        'original_display_name': unique_product_key,
                        'description': description, # 添加描述
                        'is_seasonal': is_seasonal, # 添加季节性标记
                        'popularity': 0 # 初始化人气值
                    }
                    
                    # 记录季节性产品
                    if is_seasonal:
                        SEASONAL_PRODUCTS.append(unique_product_key.lower())
                        
                    # 构建类别索引
                    if category not in PRODUCT_CATEGORIES:
                        PRODUCT_CATEGORIES[category] = []
                    PRODUCT_CATEGORIES[category].append(unique_product_key.lower())
                    
                    # 提取产品关键词
                    product_name = unique_product_key.lower()
                    # 添加完整产品名
                    if product_name not in ALL_PRODUCT_KEYWORDS:
                        ALL_PRODUCT_KEYWORDS.append(product_name)
                    # 添加单个词作为关键词
                    for word in re.findall(r'[\w\u4e00-\u9fff]+', product_name):
                        if len(word) > 1 and word not in ALL_PRODUCT_KEYWORDS:
                            ALL_PRODUCT_KEYWORDS.append(word)
                    
                except ValueError as ve:
                    print(f"警告: CSV文件第 {row_num+1} 行价格格式错误，已跳过: {row} - {ve}")
                except KeyError as ke:
                    print(f"警告: CSV文件第 {row_num+1} 行缺少必要的列，已跳过: {row} - {ke}")
                except Exception as e:
                    print(f"警告: 处理CSV文件第 {row_num+1} 行时发生未知错误，已跳过: {row} - {e}")
    except FileNotFoundError:
        print(f"错误: 产品文件 {file_path} 未找到。请确保它在应用根目录。")
    except Exception as e:
        print(f"加载产品数据时发生严重错误: {e}")
    
    if not PRODUCT_CATALOG:
        print("警告: 产品目录为空。请检查 products.csv 文件是否存在且包含有效数据和正确的列标题。")
    else:
        print(f"产品目录加载完成，共 {len(PRODUCT_CATALOG)} 条产品规格。")
        if SEASONAL_PRODUCTS:
            print(f"当季推荐产品: {len(SEASONAL_PRODUCTS)} 条")

    # 构建类别索引和关键词列表
    if PRODUCT_CATALOG:
        for key, details in PRODUCT_CATALOG.items():
            category = details.get('category', '未分类')
            if category not in PRODUCT_CATEGORIES:
                PRODUCT_CATEGORIES[category] = []
            PRODUCT_CATEGORIES[category].append(key)
            
            # 提取产品关键词
            product_name = details['name'].lower()
            # 添加完整产品名
            if product_name not in ALL_PRODUCT_KEYWORDS:
                ALL_PRODUCT_KEYWORDS.append(product_name)
            # 添加单个词作为关键词
            for word in re.findall(r'[\w\u4e00-\u9fff]+', product_name):
                if len(word) > 1 and word not in ALL_PRODUCT_KEYWORDS:
                    ALL_PRODUCT_KEYWORDS.append(word)

# 应用启动时加载产品数据 (确保在定义路由之前)
load_product_data() # 默认加载 products.csv

# 更新商品热度的函数
def update_product_popularity(product_key, increment=1):
    if product_key and product_key in PRODUCT_CATALOG:
        PRODUCT_CATALOG[product_key]['popularity'] = PRODUCT_CATALOG[product_key].get('popularity', 0) + increment
        POPULAR_PRODUCTS[product_key] = POPULAR_PRODUCTS.get(product_key, 0) + increment

# 获取特定类别的产品
def get_products_by_category(category, limit=5):
    if not category:
        return []
    matching_products = []
    for key, details in PRODUCT_CATALOG.items():
        if details['category'].lower() == category.lower():
            matching_products.append((key, details))
    # 按热度排序
    matching_products.sort(key=lambda x: x[1].get('popularity', 0), reverse=True)
    return matching_products[:limit]

# 获取热门产品
def get_popular_products(limit=3, category=None):
    products = []
    for key, details in PRODUCT_CATALOG.items():
        # 如果指定了类别，只选择该类别
        if category and details['category'].lower() != category.lower():
            continue
        products.append((key, details))
    # 按热度排序
    products.sort(key=lambda x: x[1].get('popularity', 0), reverse=True)
    return products[:limit]

# 获取季节性产品
def get_seasonal_products(limit=3, category=None):
    products = []
    for key in SEASONAL_PRODUCTS:
        if key in PRODUCT_CATALOG:
            details = PRODUCT_CATALOG[key]
            # 如果指定了类别，只选择该类别
            if category and details['category'].lower() != category.lower():
                continue
            products.append((key, details))
    # 如果季节性产品不足，补充热门产品
    if len(products) < limit:
        popular = get_popular_products(limit - len(products), category)
        # 确保不重复
        for key, details in popular:
            if key not in [p[0] for p in products]:
                products.append((key, details))
    return products[:limit]

# 添加一个新的函数用于模糊匹配产品
def fuzzy_match_product(query_text, threshold=0.6):
    """模糊匹配产品名称，返回可能的匹配及其相似度"""
    query_lower = query_text.lower()
    direct_matches = []
    partial_matches = []
    
    # 1. 尝试直接匹配产品名或catalog_key
    for key, details in PRODUCT_CATALOG.items():
        if query_lower in key or query_lower in details['name'].lower():
            direct_matches.append((key, 1.0))  # 完全匹配，相似度为1
        
    if direct_matches:
        return direct_matches
    
    # 2. 尝试关键词部分匹配
    for key, details in PRODUCT_CATALOG.items():
        product_name = details['name'].lower()
        
        # 计算关键词覆盖率
        query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query_lower))
        product_words = set(re.findall(r'[\w\u4e00-\u9fff]+', product_name))
        
        if not query_words:
            continue
            
        # 计算有多少查询词出现在产品名中
        matched_words = query_words.intersection(product_words)
        if matched_words:
            similarity = len(matched_words) / len(query_words)
            if similarity >= threshold:
                partial_matches.append((key, similarity))
    
    # 按相似度排序
    partial_matches.sort(key=lambda x: x[1], reverse=True)
    return partial_matches

# 找到与查询相关的产品类别
def find_related_category(query_text):
    """基于查询文本找到最相关的产品类别"""
    query_lower = query_text.lower()
    
    # 常见水果和蔬菜关键词手动映射
    fruit_keywords = ["苹果", "梨", "香蕉", "橙子", "橘子", "柚子", "葡萄", "西瓜", "哈密瓜", "草莓", "蓝莓", 
                    "桃", "李子", "杏", "樱桃", "石榴", "山楂", "柿子", "猕猴桃", "菠萝", "芒果", "荔枝", "龙眼",
                    "榴莲", "木瓜", "枇杷", "山竹", "椰子", "甘蔗", "柑橘", "金橘", "枣", "无花果", "杨梅", "柠檬"]
    
    vegetable_keywords = ["白菜", "卷心菜", "生菜", "菠菜", "空心菜", "韭菜", "芹菜", "茼蒿", "油菜", "花椰菜",
                        "西兰花", "芦笋", "竹笋", "藕", "土豆", "红薯", "山药", "芋头", "茄子", "辣椒", "青椒", 
                        "番茄", "黄瓜", "冬瓜", "南瓜", "丝瓜", "苦瓜", "豆角", "豌豆", "蚕豆", "毛豆", "莲子",
                        "玉米", "洋葱", "大蒜", "生姜", "胡萝卜", "白萝卜", "芥菜", "莴笋", "香菜", "葱", "蒜", "姜"]
    
    # 检查关键词是否在查询中
    for keyword in fruit_keywords:
        if keyword in query_lower:
            print(f"--- 通过水果关键词识别到产品类别: 水果 (关键词: {keyword}) ---")
            return "水果"
            
    for keyword in vegetable_keywords:
        if keyword in query_lower:
            print(f"--- 通过蔬菜关键词识别到产品类别: 蔬菜 (关键词: {keyword}) ---")
            return "蔬菜"
    
    # 1. 直接在查询中查找类别名称
    for category in PRODUCT_CATEGORIES.keys():
        if category.lower() in query_lower:
            return category
    
    # 2. 检查类别关键词
    category_scores = {}
    query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query_lower))
    
    for category, keywords_list in category_keywords.items():
        score = 0
        for keyword in keywords_list:
            if keyword in query_lower:
                score += 1
        if score > 0:
            category_scores[category] = score
    
    if category_scores:
        # 返回得分最高的类别
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    # 如果以上都没找到，使用一些启发式规则
    if any(word in query_lower for word in ["吃", "食", "鲜", "甜", "新鲜", "水果"]):
        return "水果"
    if any(word in query_lower for word in ["菜", "素", "绿色", "蔬菜"]):
        return "蔬菜"
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global last_identified_product_key_for_context
    print("--- Chat route entered ---")
    user_input = request.json.get('message', '')
    user_id = request.json.get('user_id', 'anonymous')  # 可选的用户ID跟踪
    user_input_for_processing = user_input.lower()
    calculation_done = False
    final_response = ""

    # --- 意图识别关键词 ---
    buy_intent_keywords = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只"]
    price_query_keywords = ["多少钱", "价格是", "什么价", "价钱"]
    what_do_you_sell_keywords = ["卖什么", "有什么产品", "商品列表", "菜单", "有哪些东西", "有什么卖"]
    recommend_keywords = ["推荐", "介绍点", "什么好吃", "什么值得买", "有什么好", "当季", "新鲜"]
    # category_keywords 字典可以保留，用于辅助LLM的上下文筛选，或者如果硬编码的分类回复仍需它
    category_keywords = {
        "水果": ["果", "莓", "橙", "桃", "芒", "龙眼", "荔枝", "凤梨", "葡萄", "石榴", "山楂", "芭乐", "瓜"],
        "蔬菜": ["菜", "瓜", "菇", "笋", "姜", "菠菜", "花苔", "萝卜", "南瓜", "玉米", "花生"],
        "禽类": ["鸡", "鸭"],
        "海鲜": ["鱼", "虾", "螺", "蛏", "蛤"],
        "熟食面点": ["饺", "饼", "爪", "包子", "花卷", "生煎", "燕丸", "火烧", "馄炖", "粽", "面"],
        "蛋类": ["蛋"]
    }

    is_what_do_you_sell_request = any(keyword in user_input_for_processing for keyword in what_do_you_sell_keywords)
    is_recommend_request = any(keyword in user_input_for_processing for keyword in recommend_keywords)
    
    print(f"--- DEBUG INTENT FLAGS --- is_what_do_you_sell_request: {is_what_do_you_sell_request}, is_recommend_request: {is_recommend_request}") # DEBUG PRINT

    # 0. 尝试处理纯数量追问 (例如 "那两箱呢？" "五个呢？")
    # 正则表达式匹配纯数量和可选单位，不含产品名
    # ([\d一二三四五六七八九十百千万俩两]+) 匹配数字 (包括中文数字)
    # (?:份|个|条|...) 是可选的单位词列表
    quantity_follow_up_match = re.fullmatch(r'\s*([\d一二三四五六七八九十百千万俩两]+)\s*(份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*(?:呢|呀|啊|吧|多少钱|总共)?\s*', user_input_for_processing)
    if quantity_follow_up_match and last_identified_product_key_for_context:
        print(f"--- Detected quantity follow-up for product: {last_identified_product_key_for_context} ---")
        try:
            quantity_str = quantity_follow_up_match.group(1)
            # (需要一个中文数字转阿拉伯数字的函数，暂时简化为只处理阿拉伯数字)
            try:
                quantity = int(quantity_str)
            except ValueError:
                # 尝试转换常见中文数字 (非常简化)
                num_map = {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
                if quantity_str in num_map:
                    quantity = num_map[quantity_str]
                else:
                    quantity = 1 # 转换失败则默认为1
            
            product_details = PRODUCT_CATALOG.get(last_identified_product_key_for_context)
            if product_details:
                item_price = product_details['price']
                original_display_name = product_details['original_display_name']
                original_unit_desc = product_details['specification']
                item_total = quantity * item_price
                
                final_response = f"好的，{quantity} ({original_unit_desc}) 的 {original_display_name} 总共是 ${item_total:.2f}。"
                calculation_done = True
            else:
                # 理论上 last_identified_product_key_for_context 应该总是在目录中
                print(f"错误: last_identified_product_key \'{last_identified_product_key_for_context}\' not found in PRODUCT_CATALOG.")
                last_identified_product_key_for_context = None # 清除无效的上下文
        except Exception as e:
            print(f"处理数量追问时出错: {e}")
            # 出错则不处理，让后续逻辑或LLM处理

    # --- 1. 处理"你们卖什么东西"的请求 ---
    if not calculation_done and is_what_do_you_sell_request:
        if PRODUCT_CATALOG:
            response_parts = ["我们主要提供以下生鲜和美食："]
            categories_from_catalog = {}
            for key, details in PRODUCT_CATALOG.items():
                cat = details.get('category', '未分类') # 使用CSV中的Category
                if cat not in categories_from_catalog:
                    categories_from_catalog[cat] = []
                if len(categories_from_catalog[cat]) < 4: # 每个类别列举稍多一些
                    categories_from_catalog[cat].append(details['original_display_name'])
            
            if not categories_from_catalog:
                response_parts.append("我们的产品种类丰富，例如：")
                count = 0
                for key, details in PRODUCT_CATALOG.items():
                    response_parts.append(f"- {details['original_display_name']}")
                    count += 1
                    if count >= 5: break
            else:
                for cat_name, items in categories_from_catalog.items():
                    response_parts.append(f"\n【{cat_name}】")
                    for item_display_name in items:
                        response_parts.append(f"- {item_display_name}")
            response_parts.append("\n您可以问我具体想了解哪一类，或者直接问某个产品的价格。")
            final_response = "\n".join(response_parts)
        else: 
            final_response = "抱歉，我们的产品列表暂时还没有加载好。"
        calculation_done = True
        last_identified_product_key_for_context = None

    # --- 2. 处理推荐请求 ---
    elif not calculation_done and is_recommend_request:
        if PRODUCT_CATALOG:
            # 识别用户是否询问特定类别的推荐
            target_category = find_related_category(user_input_for_processing)
            if not target_category:
                for cat_name in set(details.get('category', '') for details in PRODUCT_CATALOG.values()):
                    if cat_name.lower() in user_input_for_processing:
                        target_category = cat_name
                        break
                        
            print(f"--- 推荐请求的目标类别: {target_category} ---")
                    
            # 更智能的推荐算法
            response_parts = []
            if target_category:
                response_parts.append(f"为您推荐几款我们这里不错的{target_category}：")
            else:
                response_parts.append("为您推荐几款我们这里的优选好物：")
            
            # 获取推荐产品列表
            recommended_products = []
            
            # 1. 首先尝试获取当季产品
            seasonal = get_seasonal_products(3, target_category)
            for key, details in seasonal:
                recommended_products.append((key, details, "当季新鲜"))
                
            # 2. 不够再补充热门产品
            if len(recommended_products) < 3:
                popular = get_popular_products(3 - len(recommended_products), target_category)
                for key, details in popular:
                    if key not in [p[0] for p in recommended_products]:
                        recommended_products.append((key, details, "热门好评"))
            
            # 如果没有足够的当季或热门产品，随机选择一些该类别的产品
            if len(recommended_products) < 3 and target_category:
                category_products = get_products_by_category(target_category, 3 - len(recommended_products))
                for key, details in category_products:
                    if key not in [p[0] for p in recommended_products]:
                        recommended_products.append((key, details, "精选"))
            
            # 如果推荐列表仍然为空，随机选择
            if not recommended_products:
                num_to_recommend = min(len(PRODUCT_CATALOG), 3)
                if num_to_recommend > 0:
                    product_items = list(PRODUCT_CATALOG.items())
                    random.shuffle(product_items)
                    for i in range(num_to_recommend):
                        key, details = product_items[i]
                        recommended_products.append((key, details, "精选"))
            
            # 生成推荐文本
            if recommended_products:
                for key, details, tag in recommended_products:
                    # 添加产品描述
                    product_desc = ""
                    if details.get('description'):
                        product_desc = f" - {details['description']}"
                    
                    response_parts.append(f"- 【{tag}】{details['original_display_name']}: ${details['price']:.2f}/{details['specification']}{product_desc}")
                
                # 为推荐的产品增加热度计数
                for key, _, _ in recommended_products:
                    update_product_popularity(key)
                    
                response_parts.append("\n您对哪个感兴趣，想了解更多，还是需要其他推荐？")
            else:
                response_parts.append("我们的产品正在准备中，暂时无法为您推荐，非常抱歉！")
            
            final_response = "\n".join(response_parts)
        else: 
            final_response = "我们的产品正在准备中，暂时无法为您推荐，非常抱歉！"
        
        calculation_done = True
        last_identified_product_key_for_context = None

    # --- 3. 尝试算账或查询价格 ---
    if not calculation_done and PRODUCT_CATALOG:
        ordered_items = []
        total_price = 0.0
        identified_products_for_calculation = []

        is_buy_action = any(keyword in user_input_for_processing for keyword in buy_intent_keywords)
        is_price_action = any(keyword in user_input_for_processing for keyword in price_query_keywords)
        
        # 使用模糊匹配识别产品
        possible_matches = fuzzy_match_product(user_input_for_processing)
        
        for catalog_key, similarity in possible_matches:
            product_details = PRODUCT_CATALOG.get(catalog_key)
            if not product_details:
                continue
                
            # 确定数量
            quantity = 1
            try_names = [product_details['original_display_name'], product_details['name']]
            best_match_pos = -1
            search_term_for_qty = catalog_key # 默认用最精确的key来定位数量
            
            for name_variant in try_names:
                pos = user_input_for_processing.find(name_variant.lower())
                if pos != -1:
                    best_match_pos = pos
                    search_term_for_qty = name_variant.lower()
                    break
                    
            if best_match_pos == -1: # 如果上面没匹配到，尝试用 catalog_key
                pos = user_input_for_processing.find(catalog_key)
                if pos != -1:
                    best_match_pos = pos
                    search_term_for_qty = catalog_key
            
            # 检查用户是否明确指定了数量，或者是纯价格/重量查询
            weight_query_keywords = ["多重", "多少重", "什么重量", "称重", "多大"]
            price_only_query = is_price_action and not is_buy_action
            weight_only_query = any(keyword in user_input_for_processing for keyword in weight_query_keywords)
            
            # 如果是纯价格或重量查询，不要处理数量
            if not price_only_query and not weight_only_query and best_match_pos != -1:
                text_before_product = user_input_for_processing[:best_match_pos]
                qty_search = re.search(r'([\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*$', text_before_product.strip())
                if qty_search:
                    num_str = qty_search.group(1)
                    try: quantity = int(num_str)
                    except ValueError: 
                        num_map = {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10} # 简单中文数字
                        if num_str in num_map: quantity = num_map[num_str]
                        else: quantity = 1
            
            identified_products_for_calculation.append({
                'catalog_key': catalog_key, # 存储catalog_key用于上下文
                'details': product_details,
                'quantity': quantity,
                'is_price_query': price_only_query,
                'is_weight_query': weight_only_query,
                'similarity': similarity
            })
            
            # 增加该产品的热度
            update_product_popularity(catalog_key)

        if identified_products_for_calculation:
            # 去重和合并数量 (基于catalog_key)
            merged_items_dict = {}
            for item_data in identified_products_for_calculation:
                ckey = item_data['catalog_key']
                if ckey in merged_items_dict:
                    merged_items_dict[ckey]['quantity'] += item_data['quantity']
                    # 合并查询类型标记
                    merged_items_dict[ckey]['is_price_query'] = merged_items_dict[ckey]['is_price_query'] or item_data['is_price_query']
                    merged_items_dict[ckey]['is_weight_query'] = merged_items_dict[ckey]['is_weight_query'] or item_data['is_weight_query']
                else:
                    merged_items_dict[ckey] = item_data
            
            processed_ordered_items = []
            for ckey, item_data in merged_items_dict.items():
                details = item_data['details']
                qty = item_data['quantity']
                item_total = qty * details['price']
                total_price += item_total
                processed_ordered_items.append({
                    'name': details['original_display_name'].capitalize(),
                    'quantity': qty,
                    'unit_price': details['price'], 
                    'unit_desc': details['specification'],
                    'total': item_total,
                    'catalog_key': ckey, # 把key也加入，方便后续设置上下文
                    'is_price_query': item_data.get('is_price_query', False),
                    'is_weight_query': item_data.get('is_weight_query', False)
                })
            
            # 判断是单个产品的价格/重量查询
            single_item_query = len(processed_ordered_items) == 1
            if single_item_query:
                item = processed_ordered_items[0]
                
                # 重量查询
                if item['is_weight_query']:
                    product_details = PRODUCT_CATALOG.get(item['catalog_key'])
                    response_parts = []
                    
                    # 添加产品信息
                    seasonal_tag = ""
                    if item['catalog_key'] in SEASONAL_PRODUCTS:
                        seasonal_tag = "【当季新鲜】"
                    
                    response_parts.append(f"{seasonal_tag}{item['name']} ({item['unit_desc']}) 的规格重量如您所见。")
                    
                    # 添加详细描述
                    if product_details and product_details.get('description'):
                        response_parts.append(f"{product_details['description']}")
                    
                    response_parts.append(f"单价是 ${item['unit_price']:.2f}/{item['unit_desc']}。")
                    
                    final_response = "\n".join(response_parts)
                    last_identified_product_key_for_context = item['catalog_key']
                    calculation_done = True
                    
                # 价格查询
                elif item['is_price_query'] or (is_price_action and not is_buy_action):
                    product_details = PRODUCT_CATALOG.get(item['catalog_key'])
                    description = ""
                    if product_details and product_details.get('description'):
                        description = f"\n\n{product_details['description']}"
                    
                    seasonal_tag = ""
                    if item['catalog_key'] in SEASONAL_PRODUCTS:
                        seasonal_tag = "【当季新鲜】"
                    
                    final_response = f"{seasonal_tag}{item['name']} ({item['unit_desc']}) 的价格是 ${item['unit_price']:.2f}。{description}"
                    last_identified_product_key_for_context = item['catalog_key']
                    calculation_done = True
                    
                # 购买意图
                elif is_buy_action:
                    response_parts = ["好的，这是您的订单详情："]
                    for item in processed_ordered_items:
                        product_details = PRODUCT_CATALOG.get(item['catalog_key'])
                        seasonal_tag = ""
                        if item['catalog_key'] in SEASONAL_PRODUCTS:
                            seasonal_tag = "【当季新鲜】"
                        
                        response_parts.append(f"- {seasonal_tag}{item['name']} x {item['quantity']} ({item['unit_desc']}): ${item['unit_price']:.2f} x {item['quantity']} = ${item['total']:.2f}")
                    if total_price > 0: response_parts.append(f"\n总计：${total_price:.2f}")
                    final_response = "\n".join(response_parts)
                    if processed_ordered_items: last_identified_product_key_for_context = processed_ordered_items[-1]['catalog_key']
                    calculation_done = True
            # 多个商品
            elif processed_ordered_items and is_buy_action: 
                response_parts = ["好的，这是您的订单详情："]
                for item in processed_ordered_items:
                    product_details = PRODUCT_CATALOG.get(item['catalog_key'])
                    seasonal_tag = ""
                    if item['catalog_key'] in SEASONAL_PRODUCTS:
                        seasonal_tag = "【当季新鲜】"
                    
                    response_parts.append(f"- {seasonal_tag}{item['name']} x {item['quantity']} ({item['unit_desc']}): ${item['unit_price']:.2f} x {item['quantity']} = ${item['total']:.2f}")
                if total_price > 0: response_parts.append(f"\n总计：${total_price:.2f}")
                final_response = "\n".join(response_parts)
                if processed_ordered_items: last_identified_product_key_for_context = processed_ordered_items[-1]['catalog_key']
                calculation_done = True
            # 价格比较或其他情况
            else:
                response_parts = ["您询问的产品信息如下："]
                for item in processed_ordered_items:
                    product_details = PRODUCT_CATALOG.get(item['catalog_key'])
                    seasonal_tag = ""
                    if item['catalog_key'] in SEASONAL_PRODUCTS:
                        seasonal_tag = "【当季新鲜】"
                    
                    response_parts.append(f"- {seasonal_tag}{item['name']}: ${item['unit_price']:.2f}/{item['unit_desc']}")
                final_response = "\n".join(response_parts)
                calculation_done = True
        
        elif is_buy_action or is_price_action or is_what_do_you_sell_request or is_recommend_request:
            # 尝试提取查询的产品关键词
            query_product = None
            best_match = 0
            
            # 提取用户查询中可能的产品名称
            user_words = set(re.findall(r'[\w\u4e00-\u9fff]+', user_input_for_processing))
            
            for word in user_words:
                if len(word) < 2:
                    continue
                for key, details in PRODUCT_CATALOG.items():
                    product_name = details['name'].lower()
                    if word in product_name and len(word) > best_match:
                        query_product = word
                        best_match = len(word)
            
            # 找到相关类别
            related_category = find_related_category(user_input)
            print(f"查询相关类别: {related_category}, 查询产品关键词: {query_product}")
            
            # 获取相关推荐
            recommendation_items = []
            
            # 1. 如果有查询产品，尝试找同类产品
            if query_product:
                for key, details in PRODUCT_CATALOG.items():
                    # 检查产品名称是否包含查询关键词的部分
                    product_name = details['name'].lower()
                    if query_product in product_name:
                        recommendation_items.append((key, details, f"与'{query_product}'相关"))
            
            # 2. 如果通过关键词没找到足够推荐，但能识别类别，则使用类别推荐
            if len(recommendation_items) < 2 and related_category:
                # 确保该类别存在于产品目录中
                category_exists = False
                for _, details in PRODUCT_CATALOG.items():
                    if details.get('category', '').lower() == related_category.lower():
                        category_exists = True
                        break
                
                # 如果产品目录中存在此类别，使用该类别的产品
                if category_exists:
                    category_products = get_products_by_category(related_category, 3)
                    for key, details in category_products:
                        if all(key != rec[0] for rec in recommendation_items):
                            recommendation_items.append((key, details, f"{related_category}类商品"))
                # 如果产品目录中没有此类别，但类别是"水果"或"蔬菜"，尝试找近似类别
                elif related_category in ["水果", "蔬菜"]:
                    fruit_categories = ["水果", "新鲜水果", "时令水果", "进口水果"]
                    veg_categories = ["蔬菜", "新鲜蔬菜", "时令蔬菜", "绿叶蔬菜"]
                    
                    target_categories = fruit_categories if related_category == "水果" else veg_categories
                    
                    print(f"尝试从相似类别中查找产品: {target_categories}")
                    # 尝试从相似类别中获取产品
                    for cat in target_categories:
                        for key, details in PRODUCT_CATALOG.items():
                            if details.get('category', '').lower() == cat.lower():
                                if all(key != rec[0] for rec in recommendation_items):
                                    recommendation_items.append((key, details, f"{related_category}类商品"))
                                if len(recommendation_items) >= 3:
                                    break
                        if len(recommendation_items) >= 3:
                            break
            
            # 3. 如果关键词和类别都没有找到足够推荐，使用当季产品补充
            if len(recommendation_items) < 3:
                seasonal_products = []
                for key in SEASONAL_PRODUCTS:
                    if key in PRODUCT_CATALOG and all(key != rec[0] for rec in recommendation_items):
                        # 如果有类别限制，则只添加相同类别的产品
                        if related_category:
                            details = PRODUCT_CATALOG[key]
                            if details.get('category', '').lower() == related_category.lower():
                                seasonal_products.append((key, details, "当季推荐"))
                        else:
                            seasonal_products.append((key, PRODUCT_CATALOG[key], "当季推荐"))
                
                # 添加适量的当季产品
                for i in range(min(3 - len(recommendation_items), len(seasonal_products))):
                    recommendation_items.append(seasonal_products[i])
            
            # 4. 如果当季产品也不够，使用热门产品补充
            if len(recommendation_items) < 3:
                popular_products = get_popular_products(3 - len(recommendation_items))
                for key, details in popular_products:
                    if all(key != rec[0] for rec in recommendation_items):
                        recommendation_items.append((key, details, "热门商品"))
            
            # 准备回复
            if query_product or related_category:
                query_desc = f"'{query_product}'" if query_product else f"{related_category}类产品"
                final_response = f"抱歉，我们目前没有您查询的{query_desc}。不过，您可能对以下商品感兴趣：\n\n"
            else:
                final_response = f"为您推荐几款我们这里的优选好物：\n\n"
                
            for key, details, tag in recommendation_items[:3]:
                seasonal_tag = ""
                if key in SEASONAL_PRODUCTS:
                    seasonal_tag = "【当季新鲜】"
                description = details.get('description', '')
                desc_text = f" - {description}" if description else ""
                final_response += f"- {seasonal_tag}{details['original_display_name']}: ${details['price']:.2f}/{details['specification']}{desc_text}\n"
            
            final_response += "\n您对哪个感兴趣，想了解更多，还是需要其他推荐？"
            last_identified_product_key_for_context = None
            calculation_done = True

    # 如果以上逻辑都未处理，则交由LLM处理
    if not calculation_done:
        if llm_client: # Changed from gemini_model to llm_client
            try:
                system_prompt = (
                    "你是一位专业的生鲜产品客服。你的回答应该友好、自然且专业。"
                    "主要任务是根据顾客的询问，结合我提供的产品列表（如果本次对话提供了的话）来回答问题。"
                    "1. 当被问及我们有什么产品、特定类别的产品（如水果、时令水果、蔬菜等）或推荐时，你必须首先且主要参考我提供给你的产品列表上下文。请从该列表中选择相关的产品进行回答。"
                    "2. 如果产品列表上下文中没有用户明确询问的产品，请礼貌地告知，例如：'抱歉，您提到的XX我们目前可能没有，不过我们有这些相关的产品：[列举列表中的1-2个相关产品]'。不要虚构我们没有的产品。"
                    "3. 如果用户只是打招呼（如'你好'），请友好回应。"
                    "4. 对于算账和精确价格查询，我会尽量自己处理。如果我处理不了，或者你需要补充信息，请基于我提供的产品列表（如果有）进行回答。"
                    "5. 避免使用过于程序化或模板化的AI语言。"
                    "6. 专注于水果、蔬菜及相关生鲜产品。如果用户询问完全无关的话题，请委婉地引导回我们的产品和服务。"
                    "7. 推荐产品时，请着重突出当季新鲜产品，并尽量提供产品特点、口感或用途等信息，让推荐更有说服力。"
                    "8. 如果用户询问某个特定类别的产品，请专注于提供该类别的产品信息，并根据产品描述给出个性化建议。"
                )
                
                messages = [{"role": "system", "content": system_prompt}]
                
                # 为LLM准备更相关的产品列表上下文
                context_catalog_for_llm = ""
                if PRODUCT_CATALOG:
                    relevant_items = []
                    user_asked_category_name = None
                    
                    # 尝试从用户输入中识别类别(优先使用find_related_category)
                    related_category = find_related_category(user_input)
                    if related_category:
                        user_asked_category_name = related_category
                        print(f"--- LLM Context: User query related to category from find_related_category: {user_asked_category_name} ---")
                    
                    # 如果上面没找到，尝试从用户输入中识别明确的类别名称 (与CSV中的Category列匹配)
                    if not user_asked_category_name:
                        for cat_in_catalog in set(details.get('category', '未分类') for details in PRODUCT_CATALOG.values()):
                            if cat_in_catalog.lower() in user_input_for_processing:
                                user_asked_category_name = cat_in_catalog
                                break
                    
                    if user_asked_category_name:
                        print(f"--- LLM Context: User asked for category: {user_asked_category_name} ---")
                        # 尝试添加精确类别匹配
                        for key, details in PRODUCT_CATALOG.items():
                            if details.get('category', '').lower() == user_asked_category_name.lower():
                                relevant_items.append(details)
                        
                        # 如果识别为"水果"或"蔬菜"但找不到精确匹配，尝试更广泛的匹配
                        if not relevant_items and user_asked_category_name in ["水果", "蔬菜"]:
                            broader_categories = []
                            if user_asked_category_name == "水果":
                                broader_categories = ["水果", "新鲜水果", "时令水果", "进口水果"]
                            else:
                                broader_categories = ["蔬菜", "新鲜蔬菜", "时令蔬菜", "绿叶蔬菜"]
                            
                            for cat in broader_categories:
                                for key, details in PRODUCT_CATALOG.items():
                                    if details.get('category', '').lower() == cat.lower():
                                        relevant_items.append(details)
                                        if len(relevant_items) >= 5:  # 限制数量
                                            break
                                if relevant_items:
                                    break
                            
                            # 如果仍然找不到相关类别产品，打印调试信息
                            if not relevant_items:
                                print(f"警告：未能找到类别'{user_asked_category_name}'的相关产品")
                    
                    # 如果仍然没有找到相关项目，但用户查询中包含"水果"、"蔬菜"等泛类别关键词
                    if not relevant_items and any(keyword in user_input_for_processing for keyword in ["水果", "蔬菜", "肉", "禽", "海鲜"]):
                        category_hints = {
                            "水果": ["水果", "新鲜水果", "时令水果", "进口水果"],
                            "蔬菜": ["蔬菜", "新鲜蔬菜", "时令蔬菜", "绿叶蔬菜"],
                            "肉": ["肉类", "新鲜肉类"],
                            "禽": ["禽类", "禽类产品"],
                            "海鲜": ["海鲜", "海鲜河鲜", "水产"]
                        }
                        
                        for keyword, categories in category_hints.items():
                            if keyword in user_input_for_processing:
                                for cat in categories:
                                    for key, details in PRODUCT_CATALOG.items():
                                        if details.get('category', '').lower() == cat.lower():
                                            relevant_items.append(details)
                                            if len(relevant_items) >= 5:  # 限制数量
                                                break
                                    if len(relevant_items) >= 5:
                                        break
                                if relevant_items:
                                    break

                    if not relevant_items: # 如果没有特定分类匹配
                        print(f"--- LLM Context: No category match, using general products ---")
                        # 优先选择当季和热门产品
                        seasonal_items = []
                        for key in SEASONAL_PRODUCTS:
                            if key in PRODUCT_CATALOG:
                                seasonal_items.append(PRODUCT_CATALOG[key])
                        
                        # 添加热门产品
                        popular_items = []
                        sorted_by_popularity = sorted(PRODUCT_CATALOG.values(), key=lambda x: x.get('popularity', 0), reverse=True)
                        for item in sorted_by_popularity[:5]:  # 取前5个热门
                            if item not in seasonal_items:
                                popular_items.append(item)
                        
                        relevant_items = seasonal_items + popular_items
                        # 如果仍然不够，添加随机产品
                        if len(relevant_items) < 7:
                            remaining_items = [item for item in PRODUCT_CATALOG.values() 
                                              if item not in seasonal_items and item not in popular_items]
                            random.shuffle(remaining_items)
                            relevant_items.extend(remaining_items[:7-len(relevant_items)])

                    if relevant_items:
                        context_catalog_for_llm += "\n\n作为参考，这是我们目前的部分相关产品列表和价格（价格单位以实际规格为准）：\n"
                        count = 0
                        # 不再随机打乱，保持推荐优先级
                        for details in relevant_items: # 使用筛选后或全部的 relevant_items
                            display_name = details.get('original_display_name', details['name'].capitalize())
                            category_info = f" (类别: {details.get('category', '未分类')})" # 添加类别信息
                            seasonal_tag = ""
                            if details.get('is_seasonal'):
                                seasonal_tag = "【当季新鲜】"
                            
                            description = ""
                            if details.get('description'):
                                description = f" - {details['description']}"
                                
                            context_catalog_for_llm += f"- {seasonal_tag}{display_name}{category_info}: ${details['price']:.2f}/{details['specification']}{description}\n"
                            count += 1
                            if count >= 7: # 限制传递给LLM的条目数量
                                context_catalog_for_llm += "...还有更多相关产品...\n"
                                break
                        if count == 0: # 如果 relevant_items 为空或筛选后为空
                            context_catalog_for_llm = "（目前相关的产品列表信息未能加载或为空）\n"
                        messages.append({"role": "system", "content": "产品参考信息：" + context_catalog_for_llm})
                
                messages.append({"role": "user", "content": user_input})
                
                print(f"Messages to DeepSeek: {messages}")
                chat_completion = llm_client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=messages,
                    max_tokens=1500, # 稍微增加max_tokens以允许更详细的列表
                    temperature=0.5 # 可以尝试降低一点温度，使其更专注于事实
                )
                
                print(f"DeepSeek response object: {chat_completion}") # 调试信息
                if chat_completion.choices and chat_completion.choices[0].message and chat_completion.choices[0].message.content:
                    final_response = chat_completion.choices[0].message.content.strip()
                    print(f"DeepSeek response text: {final_response}") 
                else:
                    print("DeepSeek response structure not as expected or content is empty.")
                    final_response = "抱歉，AI助手暂时无法给出回复，请稍后再试。"

            except Exception as e:
                print(f"调用 DeepSeek API 失败: {e}")
                final_response = "抱歉，AI助手暂时遇到问题，请稍后再试。"
        else: 
            final_response = "抱歉，我现在无法处理您的请求，AI服务未连接。请稍后再试。"
        last_identified_product_key_for_context = None

    # 记录用户查询历史和更新热门商品
    if last_identified_product_key_for_context:
        if user_id not in USER_HISTORY:
            USER_HISTORY[user_id] = []
        if last_identified_product_key_for_context not in USER_HISTORY[user_id]:
            USER_HISTORY[user_id].append(last_identified_product_key_for_context)

    return jsonify({'response': final_response})

if __name__ == '__main__':
    # For local development, Gunicorn will be used on Render
    # Ensure DEEPSEEK_API_KEY is set in your local environment for testing
    if not DEEPSEEK_API_KEY:
        print("本地运行警告：未设置 DEEPSEEK_API_KEY 环境变量，DeepSeek API 调用将失败。")
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
