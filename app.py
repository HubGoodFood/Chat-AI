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

    buy_keywords = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只", "多少钱", "价格"]
    # is_buy_or_price_request = any(keyword in user_input for keyword in buy_keywords)
    # 更宽松的匹配：如果用户提到了目录中的产品名，也可能是想问价格或下单
    mentioned_product_keys = [pk for pk in PRODUCT_CATALOG.keys() if pk.split(' (')[0] in user_input_for_processing or pk in user_input_for_processing]
    is_buy_or_price_request = any(keyword in user_input for keyword in buy_keywords) or bool(mentioned_product_keys)

    if is_buy_or_price_request and PRODUCT_CATALOG:
        ordered_items = []
        total_price = 0
        found_items_for_billing = False
        
        # 改进的产品和数量提取逻辑
        # 遍历产品目录的键（例如 "新鲜农场玉米 (箱)"）
        for catalog_key, product_details in PRODUCT_CATALOG.items():
            product_name_for_match = product_details['name'].lower() # 例如 "新鲜农场玉米"
            specification_for_match = product_details['specification'].lower() # 例如 "箱"

            # 构造几种可能的匹配模式
            # 1. 产品名 + 规格 (例如 "玉米箱", "玉米 半箱")
            # 2. 产品名 (如果规格不突出或用户可能省略)
            patterns_to_check = []
            if specification_for_match and specification_for_match != product_name_for_match:
                patterns_to_check.append(f"{product_name_for_match}.*?{specification_for_match}") # 允许中间有其他字符
                patterns_to_check.append(f"{product_name_for_match}{specification_for_match}") # 直接连接
            patterns_to_check.append(product_name_for_match) # 只匹配产品名

            for pattern in patterns_to_check:
                # 查找产品模式在用户输入中的所有匹配项
                for match_obj in re.finditer(pattern, user_input_for_processing):
                    # 尝试在匹配到的产品名前面提取数量
                    quantity = 1 # 默认数量
                    # 向前查找数字 (考虑中文数字和阿拉伯数字)
                    # (?P<num>[\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|瓶|片|块|卷|对|副|套|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*(?={re.escape(match_obj.group(0))})
                    # 这是一个非常复杂的正则，先简化
                    # 在匹配到的产品 (match_obj.group(0)) 前面找数字
                    # 我们需要从 match_obj.start() 向前搜索
                    search_before_product = user_input_for_processing[:match_obj.start()]
                    # 从后往前匹配数字和可选的单位词
                    qty_match_groups = re.search(r'([\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|瓶|片|块|卷|对|副|套|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*$', search_before_product.strip())
                    
                    if qty_match_groups:
                        num_str = qty_match_groups.group(1)
                        # (这里可以加入中文数字转阿拉伯数字的逻辑，暂时简化)
                        try:
                            quantity = int(num_str)
                        except ValueError: # 如果是中文数字等，暂时无法转换，默认为1
                            quantity = 1 
                    
                    # 确保我们使用的是匹配到的 catalog_key
                    item_price = product_details['price']
                    original_display_name = product_details['original_display_name']
                    original_unit_desc = product_details['specification'] # CSV中的Specification列

                    ordered_items.append({
                        'name': original_display_name.capitalize(),
                        'quantity': quantity,
                        'unit_price': item_price,
                        'unit_desc': original_unit_desc,
                        'total': quantity * item_price
                    })
                    total_price += quantity * item_price
                    found_items_for_billing = True
                    # 找到一个匹配后，可以跳出内部pattern循环，避免对同一用户输入段重复添加同一产品
                    # 但如果用户说“我要玉米，还要一箱玉米”，我们可能需要更复杂的逻辑来去重或合并
                    # 暂时简化：只要匹配到就添加
        
        # 去重 ordered_items (基于 name 和 unit_desc 组合，并合并数量)
        if found_items_for_billing:
            merged_items = {}
            for item in ordered_items:
                key = (item['name'], item['unit_desc'])
                if key in merged_items:
                    merged_items[key]['quantity'] += item['quantity']
                    merged_items[key]['total'] += item['total'] # 这里应该是 item_price * 新quantity，或者直接累加total
                else:
                    merged_items[key] = item
            ordered_items = list(merged_items.values())
            # 重新计算总价，因为数量可能合并了
            total_price = sum(item['quantity'] * item['unit_price'] for item in ordered_items)

            response_parts = ["好的，这是您的订单详情："]
            for item in ordered_items:
                # 更新小计的计算方式
                item_total = item['quantity'] * item['unit_price']
                response_parts.append(f"- {item['name']} x {item['quantity']} ({item['unit_desc']}): ${item['unit_price']:.2f} x {item['quantity']} = ${item_total:.2f}")
            response_parts.append(f"总计：${total_price:.2f}")
            final_response = "\\n".join(response_parts)
            calculation_done = True

        elif is_buy_or_price_request: # 尝试了算账但没找到具体物品
            final_response = "抱歉，我需要更明确一些您想买什么或想查询哪个产品的价格。您可以说例如“我要1箱苹果和2袋香蕉”，或者问“苹果多少钱一箱？”"
            calculation_done = True

    if not calculation_done:
        if gemini_model:
            try:
                system_prompt = (
                    "你是一位经验丰富的果蔬营养顾问和生鲜采购专家。请用自然、亲切且专业的口吻与用户交流，就像与一位朋友分享专业的果蔬知识一样。"
                    "请避免使用过于刻板或程序化的语言，也不要主动提及自己是AI或模型。你的目标是提供准确、有用的信息，同时让对话感觉轻松愉快。"
                    "专注于水果和蔬菜相关的话题。如果用户询问无关内容，请委婉地引导回果蔬主题。"
                    "如果用户询问具体产品的价格或想下单，请告知你可以帮忙查询价格和计算总额，并引导用户说出想买的产品和数量。"
                    "如果用户只是打招呼，比如“你好”，请友好回应。"
                )
                full_prompt = f"{system_prompt}\\n\\n这是我们目前的产品列表和价格（部分，供你参考）：\\n"
                limited_catalog_for_prompt = ""
                count = 0
                if PRODUCT_CATALOG: # 检查产品目录是否为空
                    for name_key, details in PRODUCT_CATALOG.items(): # 使用 .items() 遍历字典
                        # 使用 original_display_name 进行显示
                        display_name = details.get('original_display_name', name_key.capitalize())
                        limited_catalog_for_prompt += f"- {display_name}: ${details['price']:.2f} / {details['specification']}\\n"
                        count += 1
                        if count >= 10:
                            limited_catalog_for_prompt += "...还有更多产品...\\n"
                            break
                if not PRODUCT_CATALOG or not limited_catalog_for_prompt.strip(): # 再次检查，如果循环后仍然为空
                    limited_catalog_for_prompt = "（目前产品列表为空或未能成功加载）\\n"

                full_prompt += limited_catalog_for_prompt
                full_prompt += f"\\n用户问：{user_input}"
                
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
        else:
            final_response = "抱歉，我现在无法处理您的请求，也无法连接到我的知识库。请稍后再试。"

    return jsonify({'response': final_response})

if __name__ == '__main__':
    app.run(debug=True)
