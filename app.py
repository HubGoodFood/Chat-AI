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

def load_product_data(file_path="products.csv"): 
    print(f"Attempting to load product data from {file_path}...") 
    global PRODUCT_CATALOG
    PRODUCT_CATALOG = {}
    try:
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile: 
            reader = csv.DictReader(csvfile)
            print(f"--- DEBUG: CSV Headers read by DictReader: {reader.fieldnames} ---") 
            if not reader.fieldnames or not all(col in reader.fieldnames for col in ['ProductName', 'Specification', 'Price', 'Unit']):
                print(f"错误: CSV文件 {file_path} 的列标题不正确。应包含 'ProductName', 'Specification', 'Price', 'Unit'")
                return
            
            for row_num, row in enumerate(reader, 1): 
                try:
                    product_name = row['ProductName'].strip()
                    specification = row['Specification'].strip()
                    price_str = row['Price'].strip()
                    unit = row['Unit'].strip()

                    if not product_name or not price_str or not specification or not unit:
                        print(f"警告: CSV文件第 {row_num+1} 行数据不完整，已跳过: {row}")
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
                        'original_display_name': unique_product_key 
                    }
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

# 应用启动时加载产品数据 (确保在定义路由之前)
load_product_data() # 默认加载 products.csv

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global last_identified_product_key_for_context
    print("--- Chat route entered ---")
    user_input = request.json.get('message', '')
    user_input_for_processing = user_input.lower()
    
    print(f"--- New chat request --- User input: {user_input}")
    print(f"DeepSeek client object: {llm_client}")
    print(f"PRODUCT_CATALOG size: {len(PRODUCT_CATALOG)}")
    print(f"Current last_identified_product_key_for_context: {last_identified_product_key_for_context}")

    calculation_done = False
    final_response = ""

    # 意图识别关键词
    buy_intent_keywords = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只"]
    price_query_keywords = ["多少钱", "价格是", "什么价", "价钱"]
    what_do_you_sell_keywords = ["卖什么", "有什么产品", "商品列表", "菜单", "有哪些东西"]
    recommend_keywords = ["推荐", "介绍点", "什么好吃", "什么值得买"]

    is_what_do_you_sell_request = any(keyword in user_input_for_processing for keyword in what_do_you_sell_keywords)
    is_recommend_request = any(keyword in user_input_for_processing for keyword in recommend_keywords)
    
    print(f"--- DEBUG INTENT FLAGS --- is_what_do_you_sell_request: {is_what_do_you_sell_request}, is_recommend_request: {is_recommend_request}") # DEBUG PRINT

    # 0. 尝试处理纯数量追问 (例如 “那两箱呢？” “五个呢？”)
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

    # 1. 处理“你们卖什么东西”的请求 (如果不是数量追问)
    if not calculation_done and is_what_do_you_sell_request:
        if PRODUCT_CATALOG:
            response_parts = ["我们主要提供以下类别的生鲜和美食："]
            categories = {}
            for key, details in PRODUCT_CATALOG.items():
                name = details['name']
                cat = "其他"
                if any(k in name for k in ["鸡", "鸭"]): cat = "禽类产品"
                elif any(k in name for k in ["鱼", "虾", "螺", "蛏", "蛤"]): cat = "海鲜河鲜"
                elif any(k in name for k in ["菜", "瓜", "菇", "笋", "姜", "菠菜", "花苔", "萝卜", "南瓜", "玉米", "花生"]): cat = "新鲜蔬菜"
                elif any(k in name for k in ["果", "莓", "橙", "桃", "芒", "龙眼", "荔枝", "凤梨", "葡萄", "石榴", "山楂", "芭乐"]): cat = "时令水果"
                elif any(k in name for k in ["饺", "饼", "爪", "包子", "花卷", "生煎", "燕丸", "火烧", "馄炖", "粽", "面"]): cat = "美味熟食/面点"
                elif any(k in name for k in ["蛋"]): cat = "蛋类"
                if cat not in categories: categories[cat] = []
                if len(categories[cat]) < 3: categories[cat].append(details['original_display_name'])
            for cat_name, items in categories.items():
                response_parts.append(f"\n【{cat_name}】")
                for item_display_name in items: response_parts.append(f"- {item_display_name}")
            response_parts.append("\n您可以问我具体想了解哪一类，或者直接问某个产品的价格。")
            final_response = "\n".join(response_parts)
        else: final_response = "抱歉，我们的产品列表暂时还没有加载好，您可以稍后再问我有什么产品。"
        calculation_done = True
        last_identified_product_key_for_context = None # 清除产品上下文，因为这是通用查询

    # 2. 处理推荐请求 (如果不是数量追问或卖什么)
    elif not calculation_done and is_recommend_request:
        if PRODUCT_CATALOG:
            response_parts = ["为您推荐几样我们这里不错的商品："]
            num_to_recommend = min(len(PRODUCT_CATALOG), 3)
            if num_to_recommend > 0:
                recommended_keys = random.sample(list(PRODUCT_CATALOG.keys()), num_to_recommend)
                for key in recommended_keys:
                    details = PRODUCT_CATALOG[key]
                    response_parts.append(f"- {details['original_display_name']}: ${details['price']:.2f} / {details['specification']}")
                response_parts.append("\n您对哪个感兴趣，或者想了解更多吗？")
            else:
                response_parts.append("我们的产品正在准备中，暂时无法为您推荐，非常抱歉！")
            final_response = "\n".join(response_parts)
        else: final_response = "我们的产品正在准备中，暂时无法为您推荐，非常抱歉！"
        calculation_done = True
        last_identified_product_key_for_context = None # 清除产品上下文

    # 3. 尝试算账或查询价格 (如果以上都没处理)
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
                final_response = f"{item['name']} ({item['unit_desc']}) 的价格是 ${item['unit_price']:.2f}。"
                last_identified_product_key_for_context = item['catalog_key'] # 更新上下文
                calculation_done = True
            elif processed_ordered_items: # 购买意图或多个产品被提及的价格查询
                response_parts = ["好的，这是您的订单详情："]
                for item in processed_ordered_items:
                    response_parts.append(f"- {item['name']} x {item['quantity']} ({item['unit_desc']}): ${item['unit_price']:.2f} x {item['quantity']} = ${item['total']:.2f}")
                if total_price > 0:
                    response_parts.append(f"\n总计：${total_price:.2f}")
                final_response = "\n".join(response_parts)
                # 如果是多项订单，更新上下文为最后处理的那个，或者不更新/清除？暂时更新为最后一个
                if processed_ordered_items:
                    last_identified_product_key_for_context = processed_ordered_items[-1]['catalog_key']
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
                    "你是一位经验丰富的果蔬生鲜客服。请用自然、亲切且专业的口吻与用户交流。"
                    "避免刻板的AI语言。你的目标是提供准确、有用的信息，让对话感觉轻松愉快。"
                    "专注于水果、蔬菜及相关农产品。如果用户询问无关内容，请委婉引导回主题。"
                    "如果用户问你有什么产品，请友好地介绍我们有多种生鲜，并鼓励用户问具体类别或产品。"
                    "如果用户询问具体产品的价格或想下单，但你无法从对话中解析出明确的产品和数量，请引导用户说出更具体的信息，例如“请问您想查询哪个产品的价格？”或“您想买多少呢？”。"
                    "如果用户只是打招呼，比如“你好”，请友好回应。"
                )
                
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                if PRODUCT_CATALOG and not is_what_do_you_sell_request and not is_recommend_request:
                    catalog_context = "\n\n作为参考，这是我们目前的部分产品列表和价格（价格单位以实际规格为准）：\n"
                    count = 0
                    for name_key, details in PRODUCT_CATALOG.items():
                        display_name = details.get('original_display_name', name_key.capitalize())
                        catalog_context += f"- {display_name}: ${details['price']:.2f} / {details['specification']}\n"
                        count += 1
                        if count >= 5:
                            catalog_context += "...还有更多产品...\n"
                            break
                    if not catalog_context.strip().endswith("...还有更多产品...\n") and count == 0:
                         catalog_context = "（目前产品列表参考信息未能加载或为空）\n"
                    messages.append({"role": "system", "content": "产品参考信息：" + catalog_context})
                
                messages.append({"role": "user", "content": user_input})
                
                print(f"Messages to DeepSeek: {messages}") # 调试信息
                chat_completion = llm_client.chat.completions.create(
                    model="deepseek-chat", # As per user info
                    messages=messages,
                    max_tokens=1024, # Adjust as needed
                    temperature=0.7 # Adjust as needed
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
        else: # llm_client is None
            final_response = "抱歉，我现在无法处理您的请求，AI服务未连接。请稍后再试。"
        last_identified_product_key_for_context = None # 如果走了LLM，清除产品上下文

    return jsonify({'response': final_response})

if __name__ == '__main__':
    # For local development, Gunicorn will be used on Render
    # Ensure DEEPSEEK_API_KEY is set in your local environment for testing
    if not DEEPSEEK_API_KEY:
        print("本地运行警告：未设置 DEEPSEEK_API_KEY 环境变量，DeepSeek API 调用将失败。")
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
