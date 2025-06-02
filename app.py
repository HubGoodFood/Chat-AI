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
last_identified_product_key_for_context = None # 用于存储上一个明确处理的产品的key
# 添加用户历史记录和热门商品跟踪
USER_HISTORY = {} # 简单的用户历史记录 {user_id: [product_keys]}
POPULAR_PRODUCTS = {} # 热门商品计数 {product_key: count}
SEASONAL_PRODUCTS = [] # 当季/推荐商品列表

def load_product_data(file_path="products.csv"): 
    print(f"Attempting to load product data from {file_path}...") 
    global PRODUCT_CATALOG
    PRODUCT_CATALOG = {}
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
            target_category = None
            for cat_name in set(details.get('category', '') for details in PRODUCT_CATALOG.values()):
                if cat_name.lower() in user_input_for_processing:
                    target_category = cat_name
                    break
                    
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
        identified_products_for_calculation = [] # 用于存储本次明确识别并用于计算的产品

        is_buy_action = any(keyword in user_input_for_processing for keyword in buy_intent_keywords)
        is_price_action = any(keyword in user_input_for_processing for keyword in price_query_keywords)
        
        for catalog_key, product_details in PRODUCT_CATALOG.items():
            product_name_for_match = product_details['name'].lower()
            # 优先匹配 catalog_key (更精确，含规格)
            # 然后匹配 product_name_for_match (基础名)
            # 再尝试部分匹配 (用户说简称)
            matched_this_item = False
            if catalog_key in user_input_for_processing:
                matched_this_item = True
            elif product_name_for_match in user_input_for_processing:
                matched_this_item = True
            else:
                user_terms = [term for term in re.split(r'\s+|(?<=[\\u4e00-\\u9fa5])(?=[^\\u4e00-\\u9fa5])|(?<=[^\\u4e00-\\u9fa5])(?=[\\u4e00-\\u9fa5])', user_input) if len(term) > 1]
                for term in user_terms:
                    if term.lower() in product_name_for_match:
                        matched_this_item = True
                        break
            
            if matched_this_item:
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
                if best_match_pos == -1: # 如果上面没匹配到，尝试用 catalog_key (可能含括号)
                    pos = user_input_for_processing.find(catalog_key)
                    if pos != -1:
                        best_match_pos = pos
                        search_term_for_qty = catalog_key
                
                if best_match_pos != -1:
                    text_before_product = user_input_for_processing[:best_match_pos]
                    qty_search = re.search(r'([\\d一二三四五六七八九十百千万俩两]+)\\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\\s*$', text_before_product.strip())
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
                    'quantity': quantity
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
                    'catalog_key': ckey # 把key也加入，方便后续设置上下文
                })

            if len(processed_ordered_items) == 1 and is_price_action and not is_buy_action:
                item = processed_ordered_items[0]
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
            elif processed_ordered_items: # 购买意图或多个产品被提及的价格查询
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
        
        elif is_buy_action or is_price_action: # 有意图但没找到产品
            final_response = "抱歉，我没有在菜单中找到您提到的产品。您可以看看我们有什么产品，或者换个方式问我哦。"
            calculation_done = True
            last_identified_product_key_for_context = None # 清除上下文

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
                    # 尝试从用户输入中识别明确的类别名称 (与CSV中的Category列匹配)
                    for cat_in_catalog in set(details.get('category', '未分类') for details in PRODUCT_CATALOG.values()): # 使用 .get 避免KeyError
                        if cat_in_catalog.lower() in user_input_for_processing:
                            user_asked_category_name = cat_in_catalog
                            break
                    
                    if user_asked_category_name:
                        print(f"--- LLM Context: User asked for category: {user_asked_category_name} ---")
                        for key, details in PRODUCT_CATALOG.items():
                            if details.get('category', '').lower() == user_asked_category_name.lower():
                                relevant_items.append(details)
                    
                    if not relevant_items: # 如果没有特定分类匹配，或者用户没问分类，就取通用列表的前几个
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
