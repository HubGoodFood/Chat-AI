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
    buy_keywords = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只"]
    price_query_keywords = ["多少钱", "价格是", "什么价", "价钱"]
    what_do_you_sell_keywords = ["卖什么", "有什么产品", "商品列表", "菜单"]

    # 检查是否是“卖什么”的请求
    is_what_do_you_sell_request = any(keyword in user_input_for_processing for keyword in what_do_you_sell_keywords)

    if is_what_do_you_sell_request:
        if PRODUCT_CATALOG:
            response_parts = ["我们主要提供以下类别的生鲜和美食："]
            # 简单分类或列举几个例子
            # 这里可以根据你的产品特点做得更智能，例如按水果、蔬菜、肉类、熟食等分类
            # 目前简单列举前几个作为示例
            count = 0
            categories = set()
            example_items = []
            for key, details in PRODUCT_CATALOG.items():
                # 尝试从产品名中提取类别 (非常粗略的示例)
                if "鸡" in details['name'] or "鸭" in details['name']: categories.add("禽类")
                elif "鱼" in details['name'] or "虾" in details['name'] or "螺" in details['name'] or "蛏" in details['name'] or "蛤" in details['name']: categories.add("海鲜河鲜")
                elif "菜" in details['name'] or "瓜" in details['name'] or "菇" in details['name'] or "笋" in details['name'] or "姜" in details['name'] or "白" in details['name'] or "菠菜" in details['name'] or "花苔" in details['name'] or "萝卜" in details['name']: categories.add("新鲜蔬菜")
                elif "果" in details['name'] or "莓" in details['name'] or "橙" in details['name'] or "桃" in details['name'] or "芒" in details['name'] or "龙眼" in details['name'] or "荔枝" in details['name'] or "凤梨" in details['name'] or "葡萄" in details['name'] or "石榴" in details['name'] or "山楂" in details['name'] or "芭乐" in details['name']: categories.add("时令水果")
                elif "饺" in details['name'] or "饼" in details['name'] or "爪" in details['name'] or "包子" in details['name'] or "花卷" in details['name'] or "生煎" in details['name'] or "燕丸" in details['name'] or "火烧" in details['name'] or "馄炖" in details['name'] or "粽" in details['name'] or "面" in details['name'] : categories.add("美味熟食/面点")
                
                if count < 5: # 列举几个例子
                    example_items.append(details['original_display_name'])
                count += 1
            
            if categories:
                response_parts.append("主要类别包括：" + "、".join(list(categories)) + "。")
            if example_items:
                response_parts.append("例如我们有：" + "、".join(example_items) + " 等。")
            response_parts.append("您可以问我具体想了解哪一类，或者直接问某个产品的价格哦！")
            final_response = "\\n".join(response_parts)
        else:
            final_response = "抱歉，我们的产品列表暂时还没有加载好，请稍后再问我有什么产品吧！"
        calculation_done = True # 标记为已处理

    # 算账逻辑 (在非“卖什么”请求之后)
    if not calculation_done:
        # 改进：区分纯价格查询和多项购买
        mentioned_products_in_query = []
        for catalog_key, product_details in PRODUCT_CATALOG.items():
            # 匹配产品名（不含规格）或完整带规格的产品名
            product_base_name_for_match = product_details['name'].lower()
            if product_base_name_for_match in user_input_for_processing or catalog_key in user_input_for_processing:
                mentioned_products_in_query.append(catalog_key)
        
        is_multi_item_buy_request = any(keyword in user_input_for_processing for keyword in buy_keywords) and len(mentioned_products_in_query) > 1
        is_single_item_price_query = any(keyword in user_input_for_processing for keyword in price_query_keywords) and len(mentioned_products_in_query) == 1
        is_single_item_buy_request = any(keyword in user_input_for_processing for keyword in buy_keywords) and len(mentioned_products_in_query) == 1

        if (is_multi_item_buy_request or is_single_item_buy_request) and PRODUCT_CATALOG:
            ordered_items = []
            total_price = 0.0
            found_items_for_billing = False
            
            for catalog_key in PRODUCT_CATALOG.keys(): # 使用完整的 key 来匹配
                product_details = PRODUCT_CATALOG[catalog_key]
                product_name_for_match = product_details['name'].lower()
                # 检查用户输入是否包含产品名（不含规格）或完整带规格的产品名
                # catalog_key 已经是小写了
                if product_name_for_match in user_input_for_processing or catalog_key in user_input_for_processing:
                    quantity = 1 # 默认数量
                    # 数量提取逻辑 (可以复用或改进之前的qty_match)
                    # 简化版：在产品名前找数字
                    # 注意：这里的product_name_for_match可能不包含规格，而catalog_key包含
                    # 我们应该基于更明确的匹配来提取数量
                    
                    # 尝试匹配 "数字 (可选单位) 产品名(含规格)" 或 "数字 (可选单位) 产品基础名"
                    # 优先匹配更具体的 catalog_key (如 "新鲜农场玉米 (箱)")
                    qty_pattern_specific = f"(\\d+)\\s*(?:个|箱|磅|斤|袋|只|把|条|盒|包)?\\s*(?:{re.escape(catalog_key)})"
                    qty_pattern_base = f"(\\d+)\\s*(?:个|箱|磅|斤|袋|只|把|条|盒|包)?\\s*(?:{re.escape(product_name_for_match)})"
                    
                    qty_match = re.search(qty_pattern_specific, user_input_for_processing, re.IGNORECASE)
                    if not qty_match:
                        qty_match = re.search(qty_pattern_base, user_input_for_processing, re.IGNORECASE)

                    if qty_match:
                        try:
                            quantity = int(qty_match.group(1))
                        except ValueError:
                            quantity = 1
                    
                    item_price = product_details['price']
                    original_display_name = product_details['original_display_name']
                    original_unit_desc = product_details['specification']

                    ordered_items.append({
                        'name': original_display_name.capitalize(),
                        'quantity': quantity,
                        'unit_price': item_price,
                        'unit_desc': original_unit_desc,
                        'total': quantity * item_price
                    })
                    total_price += quantity * item_price
                    found_items_for_billing = True
            
            if found_items_for_billing:
                # 去重和合并逻辑 (与之前类似)
                merged_items = {}
                for item in ordered_items:
                    key = (item['name'], item['unit_desc'])
                    if key in merged_items:
                        merged_items[key]['quantity'] += item['quantity']
                    else:
                        merged_items[key] = item
                ordered_items = list(merged_items.values())
                total_price = sum(item['quantity'] * item['unit_price'] for item in ordered_items)

                if len(ordered_items) == 1 and is_single_item_price_query and not is_single_item_buy_request: # 单品价格查询
                    item = ordered_items[0]
                    final_response = f"{item['name']} ({item['unit_desc']}) 的价格是 ${item['unit_price']:.2f}。"
                else: # 订单汇总
                    response_parts = ["好的，这是您的订单详情："]
                    for item in ordered_items:
                        item_total = item['quantity'] * item['unit_price']
                        response_parts.append(f"- {item['name']} x {item['quantity']} ({item['unit_desc']}): ${item['unit_price']:.2f} x {item['quantity']} = ${item_total:.2f}")
                    response_parts.append(f"总计：${total_price:.2f}")
                    final_response = "\\n".join(response_parts)
                calculation_done = True
            elif is_multi_item_buy_request or is_single_item_buy_request or is_single_item_price_query: # 尝试了但没找到
                final_response = "抱歉，我没有在菜单中找到您提到的所有产品。您可以看看我们的产品列表，或者换个方式问我哦。"
                calculation_done = True
        
        elif is_single_item_price_query and PRODUCT_CATALOG: # 单独处理只问价格但没匹配到产品的情况
            # 检查是否提到了某个产品，但该产品不在目录中
            product_mentioned_but_not_found = True # 假设提到了但没找到
            if not mentioned_products_in_query: # 如果根本没提到任何已知产品词根
                 product_mentioned_but_not_found = False

            if product_mentioned_but_not_found:
                final_response = "抱歉，我没有找到您查询的产品。您可以看看我们的产品列表，或者问问其他产品？"
            else:
                 final_response = "您想查询哪个产品的价格呢？可以说出产品名称哦。"
            calculation_done = True

    # 如果没有完成算账，或者不是算账请求，则走通用问答或Gemini
    if not calculation_done:
        if gemini_model:
            try:
                system_prompt = (
                    "你是一位经验丰富的果蔬营养顾问和生鲜采购专家。请用自然、亲切且专业的口吻与用户交流。"
                    "避免刻板的AI语言。你的目标是提供准确、有用的信息，让对话感觉轻松愉快。"
                    "专注于水果、蔬菜及相关农产品。如果用户询问无关内容，请委婉引导回主题。"
                    "如果用户问你有什么产品，你可以简单介绍一下主要类别，并鼓励用户问具体产品。"
                    "如果用户询问具体产品的价格或想下单，请根据产品目录信息准确回答。如果产品不在目录中，请礼貌告知。"
                    "如果用户只是打招呼，比如“你好”，请友好回应。"
                )
                full_prompt = f"{system_prompt}"
                
                # 只有在非明确的“卖什么”请求，且产品目录非空时，才附加产品列表给Gemini
                if not is_what_do_you_sell_request and PRODUCT_CATALOG:
                    full_prompt += "\\n\\n作为参考，这是我们目前的部分产品列表和价格：\\n"
                    limited_catalog_for_prompt = ""
                    count = 0
                    for name_key, details in PRODUCT_CATALOG.items():
                        display_name = details.get('original_display_name', name_key.capitalize())
                        limited_catalog_for_prompt += f"- {display_name}: ${details['price']:.2f} / {details['specification']}\\n"
                        count += 1
                        if count >= 5: # 减少给Gemini的列表长度
                            limited_catalog_for_prompt += "...还有更多产品...\\n"
                            break
                    if not limited_catalog_for_prompt.strip():
                        limited_catalog_for_prompt = "（目前产品列表参考信息未能加载）\\n"
                    full_prompt += limited_catalog_for_prompt
                
                full_prompt += f"\\n\\n用户的问题是：\\\"{user_input}\\\""
                
                print(f"Prompt to Gemini: {full_prompt}")
                gemini_response = gemini_model.generate_content(full_prompt)
                print(f"Gemini response object: {gemini_response}")

                if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text:
                    final_response = gemini_response.text
                    print(f"Gemini response text: {final_response}")
                else:
                    print("Gemini response does not have .text attribute or .text is empty.")
                    final_response = "抱歉，AI助手暂时无法给出回复，请稍后再试。"
                    if hasattr(gemini_response, 'prompt_feedback'):
                        print(f"Gemini prompt feedback: {gemini_response.prompt_feedback}")
                    if hasattr(gemini_response, 'candidates') and gemini_response.candidates:
                        print(f"Gemini candidates: {gemini_response.candidates}")
                        if gemini_response.candidates[0].content and gemini_response.candidates[0].content.parts:
                             final_response = "".join(part.text for part in gemini_response.candidates[0].content.parts if hasattr(part, 'text'))
                             print(f"Extracted text from Gemini candidates: {final_response}")
                             if not final_response.strip():
                                 final_response = "AI助手收到了回复但内容为空，请尝试换个问法。"
                        else:
                            final_response = "AI助手返回了无法直接解析的回复结构。"
                    else:
                        final_response = "AI助手没有返回预期的文本回复结构。"
            except Exception as e:
                print(f"调用 Gemini API 失败: {e}")
                final_response = "抱歉，AI助手暂时遇到问题，请稍后再试。"
        else: # Gemini不可用，且不是算账
            final_response = "抱歉，我现在无法处理您的请求，也无法连接到我的知识库。请稍后再试。"

    return jsonify({'response': final_response})

if __name__ == '__main__':
    app.run(debug=True)
