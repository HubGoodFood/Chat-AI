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
last_identified_product_details = None # 新增：存储上一个产品的完整详情
# 添加用户历史记录和热门商品跟踪
USER_HISTORY = {} # 简单的用户历史记录 {user_id: [product_keys]}
POPULAR_PRODUCTS = {} # 热门商品计数 {product_key: count}
SEASONAL_PRODUCTS = [] # 当季/推荐商品列表

# --- 全局常量定义 ---
BUY_INTENT_KEYWORDS = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只"]
PRICE_QUERY_KEYWORDS = ["多少钱", "价格是", "什么价", "价钱"]
WHAT_DO_YOU_SELL_KEYWORDS = ["卖什么", "有什么产品", "商品列表", "菜单", "有哪些东西", "有什么卖"]
RECOMMEND_KEYWORDS = ["推荐", "介绍点", "什么好吃", "什么值得买", "有什么好", "当季", "新鲜"]
FOLLOW_UP_KEYWORDS = ["它", "这个", "那个", "这", "那", "刚才", "刚刚"]

# 类别关键词映射字典，用于辅助分类识别 (这个也可以考虑移到配置文件或单独的模块)
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
# (fruit_keywords 和 vegetable_keywords 定义在 find_related_category 内部，可以考虑是否也移到全局)

def convert_chinese_number_to_int(text):
    """将中文数字（一到十）转换为整数。如果转换失败，返回1。"""
    num_map = {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    return num_map.get(text, 1)

def format_product_display(product_details, tag=""):
    """格式化产品信息以供显示，可选择添加标签。"""
    if not product_details:
        return ""

    name = product_details.get('original_display_name', product_details.get('name', '未知产品'))
    price = product_details.get('price', 0)
    specification = product_details.get('specification', 'N/A')
    description = product_details.get('description', '')
    is_seasonal = product_details.get('is_seasonal', False)

    display_tag = f"【{tag}】" if tag else ""
    seasonal_marker = "【当季新鲜】" if is_seasonal and not tag else "" # 如果已有tag，不再重复显示季节性
    desc_text = f" - {description}" if description else ""

    return f"{display_tag}{seasonal_marker}{name}: ${price:.2f}/{specification}{desc_text}"

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
                    product_name_lower = unique_product_key.lower() # 使用小写产品名进行关键词提取
                    # 添加完整产品名
                    if product_name_lower not in ALL_PRODUCT_KEYWORDS:
                        ALL_PRODUCT_KEYWORDS.append(product_name_lower)
                    # 添加单个词作为关键词
                    for word in re.findall(r'[\w\u4e00-\u9fff]+', product_name_lower):
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
        # 优化匹配逻辑：确保查询词是产品名的一部分，或者产品名是查询词的一部分（更宽松）
        # 或者查询词与产品名/key完全相等
        if query_lower == key or query_lower == details['name'].lower() or \
           query_lower in key or query_lower in details['name'].lower() or \
           key in query_lower or details['name'].lower() in query_lower:
            direct_matches.append((key, 1.0))  # 完全或高度相关匹配，相似度为1

    if direct_matches:
        direct_matches.sort(key=lambda x: len(x[0]), reverse=True) # 优先选择更长的（更精确的）匹配
        return direct_matches

    # 2. 尝试关键词部分匹配 (Jaccard相似度)
    query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query_lower))
    if not query_words: # 如果查询中没有有效词汇，则不进行部分匹配
        return []

    for key, details in PRODUCT_CATALOG.items():
        product_name_words = set(re.findall(r'[\w\u4e00-\u9fff]+', details['name'].lower()))
        product_key_words = set(re.findall(r'[\w\u4e00-\u9fff]+', key)) # 也考虑key中的词

        # 计算与产品名和产品key的Jaccard相似度
        intersection_name = query_words.intersection(product_name_words)
        union_name = query_words.union(product_name_words)
        similarity_name = len(intersection_name) / len(union_name) if union_name else 0

        intersection_key = query_words.intersection(product_key_words)
        union_key = query_words.union(product_key_words)
        similarity_key = len(intersection_key) / len(union_key) if union_key else 0
        
        # 取较高的相似度
        similarity = max(similarity_name, similarity_key)

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
    for category_name in PRODUCT_CATEGORIES.keys():
        if category_name.lower() in query_lower:
            return category_name

    # 2. 检查类别关键词 (使用全局 CATEGORY_KEYWORD_MAP)
    category_scores = {}
    # query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query_lower)) # query_lower 已经够用

    for cat, keywords_list in CATEGORY_KEYWORD_MAP.items():
        score = 0
        for keyword in keywords_list:
            if keyword in query_lower:
                score += 1
        if score > 0:
            category_scores[cat] = score

    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]

    if any(word in query_lower for word in ["吃", "食", "鲜", "甜", "新鲜", "水果"]):
        return "水果"
    if any(word in query_lower for word in ["菜", "素", "绿色", "蔬菜"]):
        return "蔬菜"

    return None

# --- 新增：意图处理函数 ---
def handle_quantity_follow_up(user_input_processed, last_product_key):
    """处理纯数量追问。"""
    quantity_follow_up_match = re.fullmatch(r'\s*([\d一二三四五六七八九十百千万俩两]+)\s*(份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*(?:呢|呀|啊|吧|多少钱|总共)?\s*', user_input_processed)
    if quantity_follow_up_match and last_product_key:
        print(f"--- Detected quantity follow-up for product: {last_product_key} ---")
        try:
            quantity_str = quantity_follow_up_match.group(1)
            try:
                quantity = int(quantity_str)
            except ValueError:
                quantity = convert_chinese_number_to_int(quantity_str)

            product_details = PRODUCT_CATALOG.get(last_product_key)
            if product_details:
                item_price = product_details['price']
                original_display_name = product_details['original_display_name']
                original_unit_desc = product_details['specification']
                item_total = quantity * item_price
                return f"好的，{quantity} ({original_unit_desc}) 的 {original_display_name} 总共是 ${item_total:.2f}。"
            else:
                print(f"错误: last_identified_product_key '{last_product_key}' not found in PRODUCT_CATALOG.")
        except Exception as e:
            print(f"处理数量追问时出错: {e}")
    return None

def handle_what_do_you_sell():
    """处理"你们卖什么"的请求。"""
    if PRODUCT_CATALOG:
        response_parts = ["我们主要提供以下生鲜和美食："]
        categories_from_catalog = {}
        for key, details in PRODUCT_CATALOG.items():
            cat = details.get('category', '未分类')
            if cat not in categories_from_catalog:
                categories_from_catalog[cat] = []
            if len(categories_from_catalog[cat]) < 4:
                categories_from_catalog[cat].append(details['original_display_name'])

        if not categories_from_catalog:
            response_parts.append("我们的产品种类丰富，例如：")
            count = 0
            sorted_products = sorted(PRODUCT_CATALOG.items(), key=lambda item: item[1].get('popularity', 0), reverse=True)
            for key, details in sorted_products:
                response_parts.append(f"- {details['original_display_name']}")
                count += 1
                if count >= 5: break
        else:
            for cat_name, items in categories_from_catalog.items():
                response_parts.append(f"\n【{cat_name}】")
                for item_display_name in items:
                    response_parts.append(f"- {item_display_name}")
        response_parts.append("\n您可以问我具体想了解哪一类，或者直接问某个产品的价格。")
        return "\n".join(response_parts)
    else:
        return "抱歉，我们的产品列表暂时还没有加载好。"

def handle_recommendation(user_input_processed):
    """处理推荐请求。"""
    if PRODUCT_CATALOG:
        target_category = find_related_category(user_input_processed)
        if not target_category:
            for cat_name_from_csv in PRODUCT_CATEGORIES.keys():
                if cat_name_from_csv.lower() in user_input_processed:
                    target_category = cat_name_from_csv
                    break
        print(f"--- 推荐请求的目标类别: {target_category} ---")

        response_parts = []
        if target_category:
            response_parts.append(f"为您推荐几款我们这里不错的{target_category}：")
        else:
            response_parts.append("为您推荐几款我们这里的优选好物：")

        recommended_products = []
        seasonal = get_seasonal_products(3, target_category)
        for key, details in seasonal:
            recommended_products.append((key, details, "当季新鲜"))

        if len(recommended_products) < 3:
            popular = get_popular_products(3 - len(recommended_products), target_category)
            for key, details in popular:
                if key not in [p[0] for p in recommended_products]:
                    recommended_products.append((key, details, "热门好评"))

        if len(recommended_products) < 3 and target_category:
            category_prods_all = get_products_by_category(target_category, limit=10)
            category_prods_filtered = [(k,d) for k,d in category_prods_all if k not in [p[0] for p in recommended_products]]
            needed = 3 - len(recommended_products)
            for key, details in category_prods_filtered[:needed]:
                 recommended_products.append((key, details, "精选"))

        if not recommended_products:
            num_to_recommend = min(len(PRODUCT_CATALOG), 3)
            if num_to_recommend > 0:
                all_potential_recs = get_seasonal_products(3) + get_popular_products(3)
                temp_recs_dict = {}
                for key, details in all_potential_recs:
                    if key not in temp_recs_dict:
                        temp_recs_dict[key] = details
                final_fallback_keys = list(temp_recs_dict.keys())
                random.shuffle(final_fallback_keys)
                for key in final_fallback_keys[:num_to_recommend]:
                    recommended_products.append((key, temp_recs_dict[key], "为您优选"))

        if not recommended_products and PRODUCT_CATALOG:
            num_to_recommend = min(len(PRODUCT_CATALOG), 3)
            product_items = list(PRODUCT_CATALOG.items())
            random.shuffle(product_items)
            for i in range(num_to_recommend):
                key, details = product_items[i]
                recommended_products.append((key, details, "随机精选"))

        if recommended_products:
            for key, details, tag in recommended_products:
                response_parts.append(f"- {format_product_display(details, tag=tag)}")
            for key, _, _ in recommended_products:
                update_product_popularity(key)
            response_parts.append("\n您对哪个感兴趣，想了解更多，还是需要其他推荐？")
        else:
            response_parts.append("我们的产品正在精心准备中，暂时无法为您提供具体推荐，非常抱歉！")
        return "\n".join(response_parts)
    else:
        return "我们的产品正在准备中，暂时无法为您推荐，非常抱歉！"

def handle_price_or_buy(user_input_processed, user_input_original):
    """处理价格查询或购买意图。"""
    global last_identified_product_key_for_context # 声明需要修改全局变量
    final_response = None
    calculation_done = False

    if PRODUCT_CATALOG:
        total_price = 0.0
        identified_products_for_calculation = []

        is_buy_action = any(keyword in user_input_processed for keyword in BUY_INTENT_KEYWORDS)
        is_price_action = any(keyword in user_input_processed for keyword in PRICE_QUERY_KEYWORDS)

        possible_matches = fuzzy_match_product(user_input_processed)

        for catalog_key, similarity in possible_matches:
            product_details = PRODUCT_CATALOG.get(catalog_key)
            if not product_details: continue

            quantity = 1
            try_names = [product_details['original_display_name'], product_details['name']]
            best_match_pos = -1
            # search_term_for_qty = catalog_key # 这行似乎未被有效使用，可以考虑移除

            for name_variant in try_names:
                pos = user_input_processed.find(name_variant.lower())
                if pos != -1:
                    best_match_pos = pos
                    # search_term_for_qty = name_variant.lower()
                    break
            if best_match_pos == -1:
                pos = user_input_processed.find(catalog_key)
                if pos != -1:
                    best_match_pos = pos
                    # search_term_for_qty = catalog_key

            weight_query_keywords = ["多重", "多少重", "什么重量", "称重", "多大"]
            price_only_query = is_price_action and not is_buy_action
            weight_only_query = any(keyword in user_input_processed for keyword in weight_query_keywords)

            if not price_only_query and not weight_only_query and best_match_pos != -1:
                text_before_product = user_input_processed[:best_match_pos]
                qty_search = re.search(r'([\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*$', text_before_product.strip())
                if qty_search:
                    num_str = qty_search.group(1)
                    try: quantity = int(num_str)
                    except ValueError:
                        quantity = convert_chinese_number_to_int(num_str)

            identified_products_for_calculation.append({
                'catalog_key': catalog_key,
                'details': product_details,
                'quantity': quantity,
                'is_price_query': price_only_query,
                'is_weight_query': weight_only_query,
                'similarity': similarity
            })
            update_product_popularity(catalog_key)

        if identified_products_for_calculation:
            merged_items_dict = {}
            for item_data in identified_products_for_calculation:
                ckey = item_data['catalog_key']
                if ckey in merged_items_dict:
                    merged_items_dict[ckey]['quantity'] += item_data['quantity']
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
                    'catalog_key': ckey,
                    'is_price_query': item_data.get('is_price_query', False),
                    'is_weight_query': item_data.get('is_weight_query', False)
                })

            single_item_query = len(processed_ordered_items) == 1
            if single_item_query:
                item = processed_ordered_items[0]
                product_details_context = PRODUCT_CATALOG.get(item['catalog_key'])

                if item['is_weight_query']:
                    response_parts = [f"{format_product_display(product_details_context)} 的规格重量如您所见。"]
                    response_parts.append(f"单价是 ${item['unit_price']:.2f}/{item['unit_desc']}。")
                    final_response = "\n".join(response_parts)
                    last_identified_product_key_for_context = item['catalog_key']
                    calculation_done = True
                elif item['is_price_query'] or (is_price_action and not is_buy_action):
                    base_info = format_product_display(product_details_context)
                    final_response = f"{base_info.split(':')[0]} 的价格是 ${product_details_context['price']:.2f}/{product_details_context['specification']}。"
                    if product_details_context.get('description'):
                        final_response += f"\n\n{product_details_context['description']}"
                    last_identified_product_key_for_context = item['catalog_key']
                    calculation_done = True
                elif is_buy_action:
                    response_parts = ["好的，这是您的订单详情："]
                    for item_detail in processed_ordered_items:
                        pd = PRODUCT_CATALOG.get(item_detail['catalog_key'])
                        formatted_name_price_spec = format_product_display(pd).split(' - ')[0]
                        response_parts.append(f"- {formatted_name_price_spec} x {item_detail['quantity']} = ${item_detail['total']:.2f}")
                    if total_price > 0: response_parts.append(f"\n总计：${total_price:.2f}")
                    final_response = "\n".join(response_parts)
                    if processed_ordered_items: last_identified_product_key_for_context = processed_ordered_items[-1]['catalog_key']
                    calculation_done = True
            elif processed_ordered_items and is_buy_action:
                response_parts = ["好的，这是您的订单详情："]
                for item_detail in processed_ordered_items:
                    pd = PRODUCT_CATALOG.get(item_detail['catalog_key'])
                    formatted_name_price_spec = format_product_display(pd).split(' - ')[0]
                    response_parts.append(f"- {formatted_name_price_spec} x {item_detail['quantity']} = ${item_detail['total']:.2f}")
                if total_price > 0: response_parts.append(f"\n总计：${total_price:.2f}")
                final_response = "\n".join(response_parts)
                if processed_ordered_items: last_identified_product_key_for_context = processed_ordered_items[-1]['catalog_key']
                calculation_done = True
            else: # 价格比较或其他情况 (多个产品，但不是明确购买)
                response_parts = ["您询问的产品信息如下："]
                for item_detail in processed_ordered_items:
                    pd = PRODUCT_CATALOG.get(item_detail['catalog_key'])
                    response_parts.append(f"- {format_product_display(pd)}")
                final_response = "\n".join(response_parts)
                if processed_ordered_items: last_identified_product_key_for_context = processed_ordered_items[-1]['catalog_key'] # 更新上下文为最后一个识别的产品
                calculation_done = True

        # 如果之前的逻辑没有识别出产品，但用户意图是购买或查询价格，或者之前有上下文产品
        elif is_buy_action or is_price_action or last_identified_product_key_for_context:
            query_product = None
            best_match_len = 0 # 使用匹配长度而非简单计数
            user_words = set(re.findall(r'[\w\u4e00-\u9fff]+', user_input_processed))
            for word in user_words:
                if len(word) < 2: continue
                # 简单检查词是否在产品名中
                for key, details in PRODUCT_CATALOG.items():
                    if word in details['name'].lower() and len(word) > best_match_len:
                        query_product = details['name'] # 使用完整的产品名以获得更好的类别匹配
                        best_match_len = len(word)

            related_category = find_related_category(user_input_original) # 使用原始输入获取更准确的类别
            print(f"Fallback: 查询相关类别: {related_category}, 查询产品关键词: {query_product}")

            recommendation_items = []
            # (推荐逻辑与 handle_recommendation 中的部分相似，但此处是作为找不到产品时的补充)
            # 1. 如果有识别出的产品词或类别，优先推荐相关
            if query_product or related_category:
                temp_recs = []
                if query_product:
                    for key, details in PRODUCT_CATALOG.items():
                        if query_product.lower() in details['name'].lower() or query_product.lower() in key:
                            temp_recs.append((key, details, f"与'{query_product}'相关"))
                if related_category and len(temp_recs) < 3:
                    cat_prods = get_products_by_category(related_category, 3 - len(temp_recs))
                    for k, d in cat_prods:
                        if all(k != r[0] for r in temp_recs):
                             temp_recs.append((k,d, f"{related_category}类推荐"))
                recommendation_items.extend(temp_recs)

            # 2. 补充当季和热门
            if len(recommendation_items) < 3:
                seasonal = get_seasonal_products(3 - len(recommendation_items), related_category)
                for key, details in seasonal:
                    if all(key != rec[0] for rec in recommendation_items):
                        recommendation_items.append((key, details, "当季推荐"))
            if len(recommendation_items) < 3:
                popular = get_popular_products(3 - len(recommendation_items), related_category)
                for key, details in popular:
                    if all(key != rec[0] for rec in recommendation_items):
                        recommendation_items.append((key, details, "热门推荐"))

            if recommendation_items:
                query_desc = f"'{query_product if query_product else user_input_original}'" if (query_product or user_input_original) else "您查询的产品"
                final_response = f"抱歉，我们目前没有找到完全匹配 {query_desc} 的产品。不过，您可能对以下商品感兴趣：\n\n"
                for key, details, tag in recommendation_items[:3]:
                    final_response += f"- {format_product_display(details, tag=tag)}\n"
                final_response += "\n您对哪个感兴趣，想了解更多，还是需要其他推荐？"
                # last_identified_product_key_for_context = None # 清除，因为是推荐新东西
                calculation_done = True
            # 如果连推荐都找不到，这里暂时不回复，让LLM处理

    if calculation_done:
        return final_response, True, last_identified_product_key_for_context # 返回响应, 是否处理完成, 新的上下文key
    return None, False, last_identified_product_key_for_context # 未处理

def handle_llm_fallback(user_input, user_input_processed):
    """如果其他逻辑未处理，则交由LLM处理。"""
    global last_identified_product_key_for_context, last_identified_product_details # 确保能修改全局变量
    final_response = ""
    if llm_client:
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
                "9. 如果用户提到'刚才'、'刚刚'等词，请注意可能是在询问上一个提到的产品。"
                "10. 如果上文提到过某个产品 (last_identified_product_details), 而当前用户问题不清晰，可以优先考虑与该产品相关。"
            )
            messages = [{"role": "system", "content": system_prompt}]

            # 为LLM准备上下文
            context_for_llm = ""
            if last_identified_product_details: # 优先使用精确的上下文产品
                context_for_llm += f"用户上一次明确提到的或我为您识别出的产品是：{format_product_display(last_identified_product_details)}\n"

            if PRODUCT_CATALOG:
                relevant_items_for_llm = []
                user_asked_category_name = find_related_category(user_input) # 使用原始输入

                if user_asked_category_name:
                    print(f"--- LLM Context: Category found: {user_asked_category_name} ---")
                    # 精确类别匹配
                    for key, details in PRODUCT_CATALOG.items():
                        if details.get('category', '').lower() == user_asked_category_name.lower():
                            relevant_items_for_llm.append(details)
                    # 广泛匹配 (如果精确的太少)
                    if len(relevant_items_for_llm) < 2 and user_asked_category_name in ["水果", "蔬菜"]:
                        broader_categories = ["水果", "新鲜水果", "时令水果", "进口水果"] if user_asked_category_name == "水果" else ["蔬菜", "新鲜蔬菜", "时令蔬菜", "绿叶蔬菜"]
                        for cat in broader_categories:
                            for key, details in PRODUCT_CATALOG.items():
                                if details.get('category', '').lower() == cat.lower() and details not in relevant_items_for_llm:
                                    relevant_items_for_llm.append(details)
                                    if len(relevant_items_for_llm) >= 5: break
                            if len(relevant_items_for_llm) >= 5: break

                # 如果没有类别匹配或类别产品不足，补充泛类别、季节性、热门
                if len(relevant_items_for_llm) < 5:
                    # (与之前LLM上下文构建逻辑类似，此处简化)
                    general_keywords = {"水果": ["水果"], "蔬菜": ["蔬菜"], "肉":["肉"], "禽":["禽"], "海鲜":["海鲜"]}
                    for gk, gv_list in general_keywords.items():
                        if any(kw in user_input_processed for kw in gv_list) and len(relevant_items_for_llm) < 5:
                            for key, details in PRODUCT_CATALOG.items():
                                if details.get('category','').lower().startswith(gk) and details not in relevant_items_for_llm:
                                    relevant_items_for_llm.append(details)
                                    if len(relevant_items_for_llm) >=5: break
                            if len(relevant_items_for_llm) >=5: break
                
                if len(relevant_items_for_llm) < 7:
                    # 补充当季和热门 (确保不重复)
                    temp_seasonal_popular = []
                    for key in SEASONAL_PRODUCTS:
                        if key in PRODUCT_CATALOG and PRODUCT_CATALOG[key] not in relevant_items_for_llm:
                            temp_seasonal_popular.append(PRODUCT_CATALOG[key])
                    
                    sorted_popular = sorted(PRODUCT_CATALOG.values(), key=lambda x: x.get('popularity',0), reverse=True)
                    for item in sorted_popular:
                        if item not in relevant_items_for_llm and item not in temp_seasonal_popular and len(temp_seasonal_popular) < (7-len(relevant_items_for_llm)):
                            temp_seasonal_popular.append(item)
                    relevant_items_for_llm.extend(temp_seasonal_popular)
                
                # 如果还是不够，随机补充
                if len(relevant_items_for_llm) < 7:
                    all_product_details = list(PRODUCT_CATALOG.values())
                    random.shuffle(all_product_details)
                    for item in all_product_details:
                        if item not in relevant_items_for_llm:
                            relevant_items_for_llm.append(item)
                            if len(relevant_items_for_llm) >=7: break

                if relevant_items_for_llm:
                    context_for_llm += "\n\n作为参考，这是我们目前的部分相关产品列表和价格（价格单位以实际规格为准）：\n"
                    for i, details in enumerate(relevant_items_for_llm[:7]): # 最多7条
                        context_for_llm += f"- {format_product_display(details)}\n"
                    if len(relevant_items_for_llm) > 7: context_for_llm += "...还有更多相关产品...\n"
            
            if not context_for_llm: # 如果完全没有上下文信息
                 context_for_llm = "（目前相关的产品列表信息未能加载或为空）\n"
            
            messages.append({"role": "system", "content": "产品参考信息：" + context_for_llm})
            messages.append({"role": "user", "content": user_input}) # 使用原始用户输入给LLM

            print(f"Messages to DeepSeek: {messages}")
            chat_completion = llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=1500,
                temperature=0.5
            )
            if chat_completion.choices and chat_completion.choices[0].message and chat_completion.choices[0].message.content:
                final_response = chat_completion.choices[0].message.content.strip()
                print(f"DeepSeek response text: {final_response}")
            else:
                final_response = "抱歉，AI助手暂时无法给出回复，请稍后再试。"
        except Exception as e:
            print(f"调用 DeepSeek API 失败: {e}")
            final_response = "抱歉，AI助手暂时遇到问题，请稍后再试。"
    else:
        final_response = "抱歉，我现在无法处理您的请求，AI服务未连接。请稍后再试。"
    
    # LLM处理后，通常认为之前的特定产品上下文可能不再适用，除非LLM的回复明确指向它
    # last_identified_product_key_for_context = None 
    # last_identified_product_details = None
    # ^^ 决定暂时不在这里清除，让主循环的末尾逻辑统一处理或依赖新的意图识别
    return final_response


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global last_identified_product_key_for_context, last_identified_product_details
    print("--- Chat route entered ---")
    print(f" entrada - 上一次查询的产品KEY: {last_identified_product_key_for_context}")
    if last_identified_product_details:
        print(f" entrada - 上一次查询的产品详情: {last_identified_product_details.get('original_display_name')}")


    user_input_original = request.json.get('message', '')
    user_id = request.json.get('user_id', 'anonymous')
    user_input_processed = user_input_original.lower()
    
    final_response = None
    calculation_done = False # 重命名为 intent_handled

    # 1. 处理上下文追问，扩展 user_input_processed
    is_follow_up = any(keyword in user_input_processed for keyword in FOLLOW_UP_KEYWORDS)
    if is_follow_up and last_identified_product_details: # 检查详情是否存在
        print(f"检测到对产品 '{last_identified_product_details.get('original_display_name')}' 的追问")
        product_name_context = last_identified_product_details['original_display_name']
        if product_name_context.lower() not in user_input_processed: # 避免重复添加
            user_input_processed = f"{product_name_context} {user_input_processed}" # 将产品名放在前面，可能更利于匹配
        print(f"扩展后的查询 (追问): {user_input_processed}")

    # 2. 意图识别与处理
    response_from_handler = None

    # 2.0 纯数量追问 (优先级最高，因为它非常特定且依赖上下文)
    response_from_handler = handle_quantity_follow_up(user_input_processed, last_identified_product_key_for_context)
    if response_from_handler:
        final_response = response_from_handler
        calculation_done = True
        # last_identified_product_key_for_context 保持不变，因为是针对它的操作

    # 2.1 "你们卖什么"
    if not calculation_done and any(keyword in user_input_processed for keyword in WHAT_DO_YOU_SELL_KEYWORDS):
        final_response = handle_what_do_you_sell()
        calculation_done = True
        # last_identified_product_key_for_context = None # 清除上下文，因为是通用查询
        # last_identified_product_details = None

    # 2.2 推荐请求
    elif not calculation_done and any(keyword in user_input_processed for keyword in RECOMMEND_KEYWORDS):
        final_response = handle_recommendation(user_input_processed)
        calculation_done = True
        # last_identified_product_key_for_context = None # 清除上下文，因为是推荐新东西
        # last_identified_product_details = None

    # 2.3 价格查询或购买意图 (这个函数内部会处理上下文的更新)
    if not calculation_done:
        response_from_price_buy, handled, new_context_key = handle_price_or_buy(user_input_processed, user_input_original)
        if handled:
            final_response = response_from_price_buy
            calculation_done = True
            if new_context_key: # handle_price_or_buy 可能会更新上下文
                last_identified_product_key_for_context = new_context_key
            # else: # 如果没返回新的key，但处理成功，可能也需要清除旧的，或者依赖后续的LLM判断
                # last_identified_product_key_for_context = None
                # last_identified_product_details = None

    # 3. 如果规则无法处理，则交由LLM
    if not calculation_done:
        print("--- 규칙 기반으로 처리되지 않아 LLM으로 폴백합니다 ---")
        final_response = handle_llm_fallback(user_input_original, user_input_processed)
        # LLM 处理后，一般认为上下文可能已改变或不清晰，清除旧的特定产品上下文
        # 除非LLM的回复能被解析并用于更新上下文，目前简单清除
        last_identified_product_key_for_context = None 
        last_identified_product_details = None

    # 4. 更新最终的上下文信息 (基于 last_identified_product_key_for_context)
    if last_identified_product_key_for_context:
        last_identified_product_details = PRODUCT_CATALOG.get(last_identified_product_key_for_context)
        if last_identified_product_details:
             print(f" salida - 更新后的上下文产品: {last_identified_product_details.get('original_display_name')}")
        else:
            # 如果key对应的details找不到了（理论上不应发生），则清除key
            print(f"警告: 更新上下文时未找到KEY '{last_identified_product_key_for_context}' 的详情，清除上下文。")
            last_identified_product_key_for_context = None
            last_identified_product_details = None
    elif not calculation_done: # 如果是由LLM处理的，并且上面LLM fallback清除了key
        pass # 保持 key 和 details 为 None
    # else: # 如果是规则处理且清除了上下文(如推荐)，key和details也应为None
        # if not (any(keyword in user_input_processed for keyword in WHAT_DO_YOU_SELL_KEYWORDS) or \ 
        #           any(keyword in user_input_processed for keyword in RECOMMEND_KEYWORDS)):
        #     # 对于非推荐和非"卖什么"的场景，如果calculation_done为True但key被清了，这里可能需要重新评估
        #     pass 

    # 记录用户查询历史 (可以考虑移到handle_price_or_buy等具体操作之后)
    if last_identified_product_key_for_context: # 只在明确识别出产品时记录
        if user_id not in USER_HISTORY:
            USER_HISTORY[user_id] = []
        if last_identified_product_key_for_context not in USER_HISTORY[user_id]:
            USER_HISTORY[user_id].append(last_identified_product_key_for_context)

    print(f"最终回复: {final_response}")
    return jsonify({'response': final_response if final_response is not None else "抱歉，我暂时无法理解您的意思，请换个说法试试？"})

if __name__ == '__main__':
    if not DEEPSEEK_API_KEY:
        print("本地运行警告：未设置 DEEPSEEK_API_KEY 环境变量，DeepSeek API 调用将失败。")
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
