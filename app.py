from flask import Flask, request, jsonify, render_template
import os
import google.generativeai as genai
import re
import csv # 导入csv模块

app = Flask(__name__)
print(" Flask app script is starting up... ")
print(" Flask app object created. ")

# 从环境变量中获取 API 密钥
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
print(f"--- STARTUP CHECK: GOOGLE_API_KEY from env is {'SET' if GEMINI_API_KEY else 'NOT SET'} ---")
if not GEMINI_API_KEY:
    print("警告：未找到 GOOGLE_API_KEY 环境变量。Gemini API 将无法使用。")
else:
    print(f"--- API Key found. Attempting genai.configure() ---") # 新增
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("--- genai.configure() SUCCEEDED ---") # 新增
    except Exception as e:
        print(f"配置 Gemini API 失败: {e}")
        GEMINI_API_KEY = None # 配置失败则禁用

# 初始化 Gemini 模型 (如果API密钥有效)
gemini_model = None
print(f"--- Before model initialization: GEMINI_API_KEY is {'SET' if GEMINI_API_KEY else 'NOT SET (possibly due to configure failure or never set)'} ---") # 新增
if GEMINI_API_KEY:
    print(f"--- Attempting genai.GenerativeModel('gemini-1.5-flash') ---") # 更改模型名称
    try:
        gemini_model = genai.GenerativeModel('gemini-1.5-flash') # 更改为 'gemini-1.5-flash'
        print(f"--- genai.GenerativeModel() SUCCEEDED. gemini_model is now: {gemini_model} ---") # 新增
    except Exception as e:
        print(f"初始化 Gemini 模型失败: {e}")
        gemini_model = None
else:
    print("--- Skipping genai.GenerativeModel() because GEMINI_API_KEY is NOT SET ---") # 新增

# 全局变量来存储产品数据
PRODUCT_CATALOG = {}

def load_product_data(file_path="products.csv"): # 更改文件名为 products.csv
    print(f"Attempting to load product data from {file_path}...") # 更新打印信息
    global PRODUCT_CATALOG
    PRODUCT_CATALOG = {}
    try:
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile: # 使用 utf-8-sig 编码
            reader = csv.DictReader(csvfile)
            print(f"--- DEBUG: CSV Headers read by DictReader: {reader.fieldnames} ---") # 新增调试打印
            if not reader.fieldnames or not all(col in reader.fieldnames for col in ['ProductName', 'Specification', 'Price', 'Unit']):
                print(f"错误: CSV文件 {file_path} 的列标题不正确。应包含 'ProductName', 'Specification', 'Price', 'Unit'")
                return
            
            for row_num, row in enumerate(reader, 1): # 从1开始计数行号，方便调试
                try:
                    product_name = row['ProductName'].strip()
                    specification = row['Specification'].strip()
                    price_str = row['Price'].strip()
                    unit = row['Unit'].strip()

                    if not product_name or not price_str or not specification or not unit:
                        print(f"警告: CSV文件第 {row_num+1} 行数据不完整，已跳过: {row}")
                        continue

                    price = float(price_str)
                    
                    # 创建一个唯一的键，例如 "产品名称 (规格)"
                    # 如果规格已经是产品名的一部分（例如 "产品名称 半箱"），则直接用产品名
                    # 这里我们假设 ProductName 列已经是唯一的，或者 ProductName + Specification 是唯一的
                    # 为了简单起见，我们先用 ProductName + Specification 作为组合键的基础
                    # 如果 Specification 为空或与 Unit 相同，可以只用 ProductName
                    
                    # 让key更具描述性，例如 "新鲜农场玉米 (箱)" 或 "新鲜农场玉米 (半箱)"
                    # 我们将使用 ProductName 和 Specification 来构建一个唯一的 key
                    # 如果 Specification 已经能很好地区分，比如 “箱” vs “半箱”，那么可以这样组合
                    # 如果 Specification 只是 “只”，而 ProductName 已经是 “萨松母鸡”，那么key可以是 “萨松母鸡 (只)"
                    # 或者，如果希望用户直接说 “萨松母鸡”，就能匹配到，那么key应该是小写的 “萨松母鸡”
                    # 考虑到用户可能会说 “玉米 箱” 或 “玉米 半箱”，我们将产品名和规格组合起来作为key
                    
                    # 修正：使用产品名和规格来构建唯一的key，并转为小写
                    # 例如，如果CSV中有两行：
                    # 新鲜农场玉米,箱,30,箱
                    # 新鲜农场玉米,半箱,18,半箱
                    # 对应的key会是 "新鲜农场玉米 (箱)" 和 "新鲜农场玉米 (半箱)"
                    # 这样用户说“我要一箱玉米”或“我要半箱玉米”时，我们可以尝试匹配
                    
                    # 为了让用户输入匹配更容易，我们将产品名和规格组合起来
                    # 如果规格已经是产品名的一部分（例如，产品名是“玉米 半箱”），则直接用产品名
                    # 否则，如果规格有意义，则组合
                    unique_product_key = product_name
                    if specification and specification.lower() != unit.lower() and specification not in product_name:
                        unique_product_key = f"{product_name} ({specification})"
                    
                    PRODUCT_CATALOG[unique_product_key.lower()] = {
                        'name': product_name, # 原始产品名，用于显示
                        'specification': specification, # 规格
                        'price': price, 
                        'unit': unit, # 价格对应的单位
                        'original_display_name': unique_product_key # 用于显示给用户的完整名称
                    }
                    # print(f"Loaded: {unique_product_key.lower()} -> Price: {price}, Unit: {unit}, Spec: {specification}")

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
    print("--- Chat route entered ---")
    user_input = request.json.get('message', '')
    user_input_for_processing = user_input.lower()
    
    print(f"--- New chat request --- User input: {user_input}")
    print(f"Gemini model object: {gemini_model}")
    print(f"PRODUCT_CATALOG size: {len(PRODUCT_CATALOG)}") # 调试：打印产品目录大小
    # if PRODUCT_CATALOG: # 调试：打印一些产品看看是否加载正确
    #     print(f"Sample product from catalog: {list(PRODUCT_CATALOG.items())[0] if PRODUCT_CATALOG else 'Catalog is empty'}")

    calculation_done = False
    final_response = ""

    # 意图识别关键词
    buy_intent_keywords = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只"] # 明确的购买意图
    price_query_keywords = ["多少钱", "价格是", "什么价", "价钱"]
    what_do_you_sell_keywords = ["卖什么", "有什么产品", "商品列表", "菜单", "有哪些东西"]
    recommend_keywords = ["推荐", "介绍点", "什么好吃", "什么值得买"]

    is_what_do_you_sell_request = any(keyword in user_input_for_processing for keyword in what_do_you_sell_keywords)
    is_recommend_request = any(keyword in user_input_for_processing for keyword in recommend_keywords)

    # 1. 处理“你们卖什么东西”的请求
    if is_what_do_you_sell_request:
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

    # 2. 处理推荐请求 (如果上面没处理)
    elif is_recommend_request: # 使用 elif 确保意图不重叠
        if PRODUCT_CATALOG:
            import random
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

    # 3. 尝试算账或查询价格 (如果上面都没处理)
    if not calculation_done and PRODUCT_CATALOG:
        ordered_items = []
        total_price = 0.0
        found_items_for_billing = False
        # 重新定义意图判断，使其更侧重于产品匹配和购买/价格关键词的组合
        is_buy_action = any(keyword in user_input_for_processing for keyword in buy_intent_keywords)
        is_price_action = any(keyword in user_input_for_processing for keyword in price_query_keywords)
        
        # 提取用户提到的产品
        extracted_user_items = [] # 存储用户提到的 (产品名, 数量)
        # 这是一个非常简化的提取，实际应用中需要更强的NLP
        for catalog_key, product_details in PRODUCT_CATALOG.items():
            product_name_for_match = product_details['name'].lower()
            # 尝试匹配 "数量 产品名" 或 "产品名"
            # 这里的数量提取非常基础
            qty = 1
            # 尝试匹配 "数字 产品名"
            m = re.search(f'([\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*({re.escape(product_name_for_match)}|{re.escape(product_details["original_display_name"].lower())})', user_input_for_processing)
            if m:
                try: qty = int(m.group(1)) # 假设中文数字已转换为阿拉伯数字
                except: qty = 1
                extracted_user_items.append({'key': catalog_key, 'name': product_details['original_display_name'], 'qty': qty, 'details': product_details})
                found_items_for_billing = True
            elif product_name_for_match in user_input_for_processing or product_details["original_display_name"].lower() in user_input_for_processing:
                 extracted_user_items.append({'key': catalog_key, 'name': product_details['original_display_name'], 'qty': 1, 'details': product_details})
                 found_items_for_billing = True

        if found_items_for_billing:
            # 去重和合并数量
            merged_items_dict = {}
            for item in extracted_user_items:
                item_key = item['key']
                if item_key in merged_items_dict:
                    merged_items_dict[item_key]['qty'] += item['qty']
                else:
                    merged_items_dict[item_key] = item
            
            processed_ordered_items = []
            for key, item_data in merged_items_dict.items():
                details = item_data['details']
                qty = item_data['qty']
                item_total = qty * details['price']
                total_price += item_total
                processed_ordered_items.append({
                    'name': details['original_display_name'].capitalize(),
                    'quantity': qty,
                    'unit_price': details['price'],
                    'unit_desc': details['specification'],
                    'total': item_total
                })

            if processed_ordered_items: # 确保真的有处理过的物品
                if len(processed_ordered_items) == 1 and is_price_action and not is_buy_action:
                    item = processed_ordered_items[0]
                    final_response = f"{item['name']} ({item['unit_desc']}) 的价格是 ${item['unit_price']:.2f}。"
                else:
                    response_parts = ["好的，这是您的订单详情："]
                    for item in processed_ordered_items:
                        response_parts.append(f"- {item['name']} x {item['quantity']} ({item['unit_desc']}): ${item['unit_price']:.2f} x {item['quantity']} = ${item['total']:.2f}")
                    if total_price > 0:
                        response_parts.append(f"\n总计：${total_price:.2f}")
                    final_response = "\n".join(response_parts)
                calculation_done = True
            elif is_buy_action or is_price_action: # 有意图但没匹配到
                final_response = "抱歉，我没有在菜单中准确识别到您提到的产品。您可以试试说出更完整的产品名称吗？"
                calculation_done = True
        elif is_buy_action or is_price_action: # 有意图但目录中完全没匹配到任何词
             final_response = "您好！请问您想买些什么或者查询什么价格呢？可以说出具体的产品名称哦。"
             calculation_done = True

    # 如果以上逻辑都未处理，则交由Gemini处理
    if not calculation_done:
        if gemini_model:
            try:
                system_prompt = (
                    "你是一位经验丰富的果蔬营养顾问和生鲜采购专家。请用自然、亲切且专业的口吻与用户交流。"
                    "避免刻板的AI语言。你的目标是提供准确、有用的信息，让对话感觉轻松愉快。"
                    "专注于水果、蔬菜及相关农产品。如果用户询问无关内容，请委婉引导回主题。"
                    "如果用户问你有什么产品，请友好地介绍我们有多种生鲜，并鼓励用户问具体类别或产品。"
                    "如果用户询问具体产品的价格或想下单，请根据产品目录信息准确回答。如果产品不在目录中，请礼貌告知。"
                    "如果用户只是打招呼，比如“你好”，请友好回应。"
                )
                full_prompt = f"{system_prompt}"
                
                # 只有在非明确的“卖什么”或“推荐”请求，且产品目录非空时，才附加产品列表给Gemini
                if PRODUCT_CATALOG and not is_what_do_you_sell_request and not is_recommend_request:
                    full_prompt += "\n\n作为参考，这是我们目前的部分产品列表和价格（价格单位以实际规格为准）：\n"
                    limited_catalog_for_prompt = ""
                    count = 0
                    for name_key, details in PRODUCT_CATALOG.items():
                        display_name = details.get('original_display_name', name_key.capitalize())
                        limited_catalog_for_prompt += f"- {display_name}: ${details['price']:.2f} / {details['specification']}\n"
                        count += 1
                        if count >= 5: # 减少给Gemini的列表长度
                            limited_catalog_for_prompt += "...还有更多产品...\n"
                            break
                    if not limited_catalog_for_prompt.strip():
                        limited_catalog_for_prompt = "（目前产品列表参考信息未能加载）\n"
                    full_prompt += limited_catalog_for_prompt
                
                full_prompt += f"\n\n用户的问题是：\"{user_input}\""
                
                print(f"Prompt to Gemini: {full_prompt}")
                gemini_response = gemini_model.generate_content(full_prompt)
                print(f"Gemini response object: {gemini_response}")

                if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text:
                    final_response = gemini_response.text
                    print(f"Gemini response text: {final_response}")
                else:
                    print("Gemini response does not have .text attribute or .text is empty.")
                    final_response = "抱歉，AI助手暂时无法给出回复，请稍后再试。"
                    if hasattr(gemini_response, 'prompt_feedback') and gemini_response.prompt_feedback:
                        print(f"Gemini prompt feedback: {gemini_response.prompt_feedback}")
                    elif hasattr(gemini_response, 'candidates') and gemini_response.candidates and len(gemini_response.candidates) > 0:
                        print(f"Gemini candidates: {gemini_response.candidates}")
                        # Try to extract from candidates if .text was missing
                        try:
                            final_response = "".join(part.text for part in gemini_response.candidates[0].content.parts if hasattr(part, 'text'))
                            if not final_response.strip(): final_response = "AI助手收到了回复但内容为空。"
                        except Exception:
                            final_response = "AI助手返回了无法解析的回复结构。"
                    else:
                        final_response = "AI助手没有返回预期的文本回复结构。"
            except Exception as e:
                print(f"调用 Gemini API 失败: {e}")
                final_response = "抱歉，AI助手暂时遇到问题，请稍后再试。"
        else: # Gemini不可用
            final_response = "抱歉，我现在无法处理您的请求，也无法连接到我的知识库。请稍后再试。"

    return jsonify({'response': final_response})

if __name__ == '__main__':
    app.run(debug=True)
