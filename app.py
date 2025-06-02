from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI # ADDED for DeepSeek (OpenAI compatible)
import re
import csv
import random # Ensure random is imported for recommendations

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
    print("--- Chat route entered ---")
    user_input = request.json.get('message', '')
    user_input_for_processing = user_input.lower()
    
    print(f"--- New chat request --- User input: {user_input}")
    print(f"DeepSeek client object: {llm_client}") # Updated print
    print(f"PRODUCT_CATALOG size: {len(PRODUCT_CATALOG)}")

    calculation_done = False
    final_response = ""

    # 意图识别关键词
    buy_intent_keywords = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只"]
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
        is_buy_action = any(keyword in user_input_for_processing for keyword in buy_intent_keywords)
        is_price_action = any(keyword in user_input_for_processing for keyword in price_query_keywords)
        
        extracted_user_items = [] 
        for catalog_key, product_details in PRODUCT_CATALOG.items():
            product_name_for_match = product_details['name'].lower()
            qty = 1
            m = re.search(f'([\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*({re.escape(product_name_for_match)}|{re.escape(product_details["original_display_name"].lower())})', user_input_for_processing)
            if m:
                try: qty = int(m.group(1)) 
                except: qty = 1
                extracted_user_items.append({'key': catalog_key, 'name': product_details['original_display_name'], 'qty': qty, 'details': product_details})
            elif product_name_for_match in user_input_for_processing or product_details["original_display_name"].lower() in user_input_for_processing:
                 extracted_user_items.append({'key': catalog_key, 'name': product_details['original_display_name'], 'qty': 1, 'details': product_details})

        if extracted_user_items: # If any product was potentially identified
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

            if processed_ordered_items: 
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
            elif is_buy_action or is_price_action: 
                final_response = "抱歉，我没有在菜单中准确识别到您提到的产品。您可以试试说出更完整的产品名称吗？"
                calculation_done = True
        elif is_buy_action or is_price_action: 
             final_response = "您好！请问您想买些什么或者查询什么价格呢？可以说出具体的产品名称哦。"
             calculation_done = True

    # 如果没有完成本地处理 (算账、卖什么、推荐)，则调用LLM
    if not calculation_done:
        if llm_client: # Check if DeepSeek client is initialized
            try:
                system_message_content = (
                    "你是一位经验丰富的果蔬生鲜客服。请用自然、亲切且专业的口吻与用户交流。"
                    "避免刻板的AI语言。你的目标是提供准确、有用的信息，让对话感觉轻松愉快。"
                    "专注于水果、蔬菜及相关农产品。如果用户询问无关内容，请委婉引导回主题。"
                    "如果用户问你有什么产品，请友好地介绍我们有多种生鲜，并鼓励用户问具体类别或产品。"
                    "如果用户询问具体产品的价格或想下单，请告知你可以帮忙查询价格和计算总额，并引导用户说出想买的产品和数量。"
                    "如果用户只是打招呼，比如“你好”，请友好回应。"
                )
                
                messages = [
                    {"role": "system", "content": system_message_content}
                ]

                # 只有在非明确的“卖什么”或“推荐”请求，且产品目录非空时，才附加产品列表给LLM
                if PRODUCT_CATALOG and not is_what_do_you_sell_request and not is_recommend_request:
                    catalog_context = "\n\n作为参考，这是我们目前的部分产品列表和价格（价格单位以实际规格为准）：\n"
                    count = 0
                    for name_key, details in PRODUCT_CATALOG.items():
                        display_name = details.get('original_display_name', name_key.capitalize())
                        catalog_context += f"- {display_name}: ${details['price']:.2f} / {details['specification']}\n"
                        count += 1
                        if count >= 7: # 减少给LLM的列表长度
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
        else: # llm_client (DeepSeek) 不可用
            final_response = "抱歉，我现在无法处理您的请求，AI服务未连接。请稍后再试。"

    return jsonify({'response': final_response})

if __name__ == '__main__':
    # For local development, Gunicorn will be used on Render
    # Ensure DEEPSEEK_API_KEY is set in your local environment for testing
    if not DEEPSEEK_API_KEY:
        print("本地运行警告：未设置 DEEPSEEK_API_KEY 环境变量，DeepSeek API 调用将失败。")
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
