from flask import Flask, request, jsonify, render_template
import os
import google.generativeai as genai
import re

app = Flask(__name__)
print(" Flask app script is starting up... ")
print(" Flask app object created. ")

# 从环境变量中获取 API 密钥
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GEMINI_API_KEY:
    print("警告：未找到 GOOGLE_API_KEY 环境变量。Gemini API 将无法使用。")
    # 你可以在这里决定是完全禁用 Gemini 功能，还是允许应用在没有 API 密钥的情况下运行（但会报错）
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"配置 Gemini API 失败: {e}")
        GEMINI_API_KEY = None # 配置失败则禁用

# 初始化 Gemini 模型 (如果API密钥有效)
gemini_model = None
# 全局变量来存储产品数据
PRODUCT_CATALOG = {}

def parse_price_unit(price_str, unit_str):
    """尝试解析价格和单位，处理多种格式"""
    try:
        price = float(re.findall(r"\d+\.?\d*", price_str)[0])
        unit = unit_str.strip().lower()
        # 尝试标准化单位，例如 '2磅' -> '磅'
        unit_match = re.search(r"([a-zA-Z\u4e00-\u9fa5]+)", unit) # 匹配字母和中文字符作为单位
        if unit_match:
            unit = unit_match.group(1)
        
        quantity_match = re.search(r"(\d+)\s*" + re.escape(unit), price_str, re.IGNORECASE)
        if not quantity_match: # 如果价格字符串中没有数量，尝试从单位字符串中找
             quantity_match = re.search(r"(\d+)\s*" + re.escape(unit), unit_str, re.IGNORECASE)

        quantity = 1 # 默认为1个单位
        if quantity_match:
            # This part is tricky due to varied formats like "25个", "2包x400g"
            # For now, let's try a simple extraction if the format is like "25个"
            simple_qty_match = re.match(r"(\d+)", unit_str)
            if simple_qty_match:
                try:
                    quantity = int(simple_qty_match.group(1))
                except ValueError:
                    pass #保持quantity为1
        
        # 对于 "23/2只" 这样的格式，尝试提取数量和单位
        if '/' in price_str and '只' in price_str: #非常特定的规则
            parts = price_str.split('/')
            if len(parts) == 2:
                try:
                    price = float(parts[0])
                    if '只' in parts[1]:
                        unit = '只'
                        quantity = int(re.findall(r"\d+", parts[1])[0])
                except ValueError:
                    pass


        return price, unit, quantity
    except:
        return None, None, 1 #解析失败

def load_product_data(file_path="products.txt"):
    print("Attempting to load product data...")
    global PRODUCT_CATALOG
    PRODUCT_CATALOG = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("🌸") or line.startswith("🪷") or line.startswith("💥") or "===" in line or "本周蔬菜水果" in line or "保证质量" in line:
                    continue

                # 尝试更灵活地匹配产品名称、价格和单位
                # 这个正则表达式需要根据实际文件格式不断调整和优化
                # 基本思路：(产品名) ($价格) (/单位描述) (可选的第二个价格/单位)
                # 例如: 农场素食散养走地萨松母鸡$23.99/只
                #       谭头水饺$25/袋
                #       新鲜农场玉米$30/箱，18/半箱
                #       农场新鲜平菇 $23/3磅，35/5磅
                
                # 先移除行号和特殊标记如 "1. ✨"
                line = re.sub(r"^\d+\.\\s*✨?\\s*", "", line).strip()
                line = re.sub(r"✨", "", line).strip() # 移除所有✨
                line = re.sub(r"💕", "", line).strip() # 移除所有💕
                line = re.sub(r"❗️", "", line).strip() # 移除所有❗️

                # 分割多种规格的产品
                items = re.split(r'[，]\s*|\s+-\s+', line) # 用中文逗号或 " - " 分割
                
                base_product_name = ""

                for i, item_part in enumerate(items):
                    item_part = item_part.strip()
                    if not item_part:
                        continue

                    # 匹配 "产品名$价格/单位" 或 "产品名 价格/单位"
                    match = re.match(r"(.+?)(?:\\s*\\$|\\s+)(\\d+\\.?\\d+)\\s*/\\s*(.+)", item_part)
                    
                    if not match: # 尝试另一种格式 "产品名$价格单位" (例如 $29/2版)
                        match = re.match(r"(.+?)(?:\\s*\\$|\\s+)(\\d+\\.?\\d+)([a-zA-Z\u4e00-\u9fa5\\d/磅]+)", item_part)


                    if match:
                        product_name_full = match.group(1).strip()
                        price_str = match.group(2).strip()
                        unit_desc_full = match.group(3).strip()

                        # 如果是多规格的第一部分，设定为基础产品名
                        if i == 0:
                            base_product_name = product_name_full
                        else: # 如果是后续规格，且没有明确产品名，则使用基础产品名
                            # 检查后续部分是否也包含一个看起来像产品名的部分
                            # 这是一个简化处理，可能需要更复杂的逻辑来判断是否是全新的产品名
                            if not any(char.isdigit() or char == '$' for char in product_name_full.split()[0]): # 如果第一部分不像价格
                                base_product_name = product_name_full # 更新基础产品名

                        price, unit, quantity_in_unit_desc = parse_price_unit(price_str, unit_desc_full)

                        if price is not None and unit is not None:
                            # 构建一个唯一的key，结合基础产品名和单位描述（处理"半箱"等情况）
                            # 对于 "农场新鲜玉米$30/箱，18/半箱"，unit_desc_full 会是 "箱" 和 "半箱"
                            # 我们希望产品名能区分它们
                            current_item_name = base_product_name
                            if "半" in unit_desc_full and "箱" in unit_desc_full : #特定处理半箱
                                current_item_name = f"{base_product_name} (半箱)"
                                unit = "半箱"
                            elif "半" in unit_desc_full and "磅" in unit_desc_full:
                                current_item_name = f"{base_product_name} (半磅)"
                                unit = "半磅"
                            # 更多类似规则可以添加

                            # 如果单位描述中已经包含了数量，例如 "25个"，则price是这25个的总价
                            # 我们需要计算单个的价格
                            # single_item_price = price / quantity_in_unit_desc if quantity_in_unit_desc > 0 else price
                            
                            # 存储时，我们存储的是 unit_desc_full 这个单位的价格
                            PRODUCT_CATALOG[current_item_name.lower()] = {'price': price, 'unit': unit, 'original_unit_desc': unit_desc_full}
                            # print(f"Loaded: {current_item_name.lower()} - Price: {price}, Unit: {unit}, Original Unit Desc: {unit_desc_full}")

    except FileNotFoundError:
        print(f"错误: 产品文件 {file_path} 未找到。")
    except Exception as e:
        print(f"加载产品数据时出错: {e}")

# 应用启动时加载产品数据
load_product_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    print("--- Chat route entered ---")
    user_input = request.json.get('message', '')
    user_input_for_processing = user_input.lower() # 用于本地处理转小写
    
    print(f"--- New chat request --- User input: {user_input}") # 调试信息
    print(f"Gemini model object: {gemini_model}") # 调试信息：检查模型对象

    response_from_local_kb = None
    calculation_done = False
    
    # 尝试解析算账请求
    # 简化版：寻找 "买/要/订单" 和 "多少钱/总价/一共" 等关键词
    buy_keywords = ["买", "要", "订单", "来一份", "来一", "一份", "一个", "一箱", "一磅", "一袋", "一只"]
    price_keywords = ["多少钱", "总价", "一共", "结算", "算一下"]

    is_buy_request = any(keyword in user_input for keyword in buy_keywords)
    is_price_request = any(keyword in user_input for keyword in price_keywords)

    if is_buy_request or (is_price_request and any(prod.lower() in user_input_for_processing for prod in PRODUCT_CATALOG.keys())):
        # 这是一个可能的算账请求
        # 提取物品和数量 (这是一个非常简化的提取，实际需要更复杂的NLP)
        ordered_items = []
        total_price = 0
        found_items_for_billing = False

        # 尝试从用户输入中提取数量和产品
        # 例如: "我要1箱玉米和2个苹果"
        # 这个正则表达式需要非常小心地构建和测试
        # (数量) (单位/可选) (产品名)
        # \s*([0-9.]+)\s*(箱|个|磅|lb|袋|只|把|版|斤|条)?\s*([一-龥a-zA-Z\s]+(?:（半箱）|（半磅）)?)
        # (?:(?P<quantity>[0-9.]+)\s*(?P<unit>箱|个|磅|lb|袋|只|把|版|斤|条|盒|包)?\s*)?(?P<name>[一-龥a-zA-Z\s()（）]+)
        
        # 更简单的逐个产品匹配
        potential_order_details = []
        for product_key in PRODUCT_CATALOG.keys():
            # 尝试匹配 "数字+单位+产品名" 或 "数字+产品名" 或 "产品名"
            # 这里的product_key是小写的
            # 为了匹配 "1箱玉米", product_key 应该是 "农场新鲜玉米" 或 "农场新鲜玉米 (半箱)"
            # 我们需要从 product_key 中去掉括号里的描述部分来做初步匹配
            
            product_base_name_for_match = product_key.split(' (')[0]

            # 1. 尝试匹配 "数字 单位 产品名" (例如 "1 箱 玉米")
            # 2. 尝试匹配 "数字产品名" (例如 "1玉米", "1个玉米") - 这比较难，因为单位可能嵌入
            # 3. 尝试匹配 "产品名" (默认数量为1)
            
            # 简化逻辑：如果用户输入包含产品名(小写)
            if product_base_name_for_match in user_input_for_processing:
                # 尝试提取数量，默认为1
                quantity = 1
                # 尝试匹配 "数字(可选的小数) + (可选的空格) + (可选的单位) + (可选的空格) + 产品名"
                # 例如 "我要 2 箱 农场新鲜玉米" 或 "我要 两 箱 农场新鲜玉米"
                # 或者 "2农场新鲜玉米"
                # 这个正则非常复杂，先用一个简化的
                
                # 查找产品名前面的数字
                # (?:^|\s+|和|与)([0-9一二三四五六七八九十百千万俩两]+)\s*(?:个|箱|磅|袋|只|把|条|盒|包|斤)?\s*(?={product_base_name_for_match})
                # (?P<quantity_num>[0-9一二三四五六七八九十百千万俩两]+)\s*(?P<unit_word>个|箱|磅|袋|只|把|条|盒|包|斤)?\s*(?={product_base_name_for_match})
                
                # 简化：直接在产品名前面找数字，忽略单位词匹配
                # \b(\d+)\s*(?:个|箱|磅|斤|袋|只|把|条|盒|包)?\s*{product_base_name_for_match}
                qty_match = re.search(f"(\\d+)\\s*(?:个|箱|磅|斤|袋|只|把|条|盒|包)?\\s*(?:{re.escape(product_base_name_for_match)})", user_input_for_processing, re.IGNORECASE)
                if qty_match:
                    try:
                        quantity = int(qty_match.group(1))
                    except ValueError:
                        quantity = 1 # 如果转换失败，默认为1
                
                # 检查是否是特定规格，如 "半箱"
                current_product_lookup_key = product_key # 默认使用完整key (可能包含 " (半箱)")
                if f"{product_base_name_for_match} (半箱)" in PRODUCT_CATALOG and "半箱" in user_input_for_processing and product_base_name_for_match in user_input_for_processing:
                    current_product_lookup_key = f"{product_base_name_for_match} (半箱)"
                elif f"{product_base_name_for_match} (半磅)" in PRODUCT_CATALOG and "半磅" in user_input_for_processing and product_base_name_for_match in user_input_for_processing:
                     current_product_lookup_key = f"{product_base_name_for_match} (半磅)"
                # ...可以为其他规格添加更多elif

                if current_product_lookup_key in PRODUCT_CATALOG:
                    item_price = PRODUCT_CATALOG[current_product_lookup_key]['price']
                    item_unit = PRODUCT_CATALOG[current_product_lookup_key]['unit']
                    original_unit_desc = PRODUCT_CATALOG[current_product_lookup_key]['original_unit_desc']

                    # 如果用户明确指定了单位，且该单位与产品目录中的单位不同，但价格是基于目录单位的
                    # 例如用户说 "1个苹果"，但价格是 "苹果 $5/磅" -> 这种情况目前难以处理
                    # 我们假设用户说的单位和数量是针对产品目录中记录的那个单位的
                    
                    # 修正：如果original_unit_desc包含数量，例如 "25个"，那么item_price是这25个的总价
                    # 我们需要的是单个的平均价格，或者说，如果用户要“1份”，那就是这个总价
                    # 这里的逻辑是，如果用户说 "1份小笼包"，而小笼包是 "$20/25个"，那么价格是20
                    # 如果用户说 "50个小笼包"，我们需要识别出 "2份"
                    
                    # 简化：目前假设用户说的数量是针对 listed unit_desc 的数量
                    # 例如，用户说 "2箱玉米"，如果玉米是 "$30/箱"，则总价是 2*30
                    # 用户说 "1份小笼包"，如果小笼包是 "$20/25个"，则总价是 1*20 (这里的单位是 "25个")

                    ordered_items.append({
                        'name': current_product_lookup_key.capitalize(), # 显示时首字母大写
                        'quantity': quantity,
                        'unit_price': item_price, # 这是 original_unit_desc 的价格
                        'unit_desc': original_unit_desc, # 例如 "只", "袋", "25个"
                        'total': quantity * item_price
                    })
                    total_price += quantity * item_price
                    found_items_for_billing = True

        if found_items_for_billing:
            response_parts = ["好的，这是您的订单详情："]
            for item in ordered_items:
                response_parts.append(f"- {item['name']} x {item['quantity']} ({item['unit_desc']}): ${item['unit_price']:.2f} x {item['quantity']} = ${item['total']:.2f}")
            response_parts.append(f"总计：${total_price:.2f}")
            final_response = "\\n".join(response_parts)
            calculation_done = True
        elif is_buy_request or is_price_request: # 尝试了算账但没找到具体物品
            final_response = "抱歉，我需要更明确一些您想买什么。您可以说例如“我要1箱苹果和2袋香蕉”，或者问“苹果多少钱一箱？”"
            calculation_done = True # 也算处理了，只是没成功

    # 如果没有完成算账，或者不是算账请求，则走通用问答或Gemini
    if not calculation_done:
        # ... (原有的 knowledge_base 查找逻辑) ...
        # (这个 knowledge_base 主要是关于果蔬营养、挑选、储存的，不是价格)
        # 我们可以保留它，或者如果算账优先，则可以注释掉这部分，完全依赖Gemini处理非算账问题

        # 决定是否调用Gemini
        # 如果本地知识库（非价格）有答案，并且用户不是明确问价格/买东西，可以用本地答案
        # 否则，如果Gemini可用，用Gemini
        
        # 简化：如果不是算账，直接走Gemini（如果可用）
        if gemini_model:
            try:
                system_prompt = (
                    "你是一位经验丰富的果蔬营养顾问和生鲜采购专家。请用自然、亲切且专业的口吻与用户交流，就像与一位朋友分享专业的果蔬知识一样。"
                    "请避免使用过于刻板或程序化的语言，也不要主动提及自己是AI或模型。你的目标是提供准确、有用的信息，同时让对话感觉轻松愉快。"
                    "专注于水果和蔬菜相关的话题。如果用户询问无关内容，请委婉地引导回果蔬主题。"
                    "如果用户询问具体产品的价格或想下单，请告知你可以帮忙查询价格和计算总额，并引导用户说出想买的产品和数量。"
                )
                full_prompt = f"{system_prompt}\\n\\n这是我们目前的产品列表和价格（部分，供你参考）：\\n"
                limited_catalog_for_prompt = ""
                count = 0
                for name, details in PRODUCT_CATALOG.items():
                    limited_catalog_for_prompt += f"- {name.capitalize()}: ${details['price']:.2f} / {details['original_unit_desc']}\\n"
                    count += 1
                    if count >= 10: 
                        limited_catalog_for_prompt += "...还有更多产品...\\n"
                        break
                if not PRODUCT_CATALOG:
                    limited_catalog_for_prompt = "（目前产品列表为空）\\n"

                full_prompt += limited_catalog_for_prompt
                full_prompt += f"\\n用户问：{user_input}"
                
                print(f"Prompt to Gemini: {full_prompt}") # 调试信息

                gemini_response = gemini_model.generate_content(full_prompt)
                
                print(f"Gemini response object: {gemini_response}") # 调试信息
                if gemini_response and hasattr(gemini_response, 'text') and gemini_response.text:
                    final_response = gemini_response.text
                    print(f"Gemini response text: {final_response}") 
                else:
                    print("Gemini response does not have .text attribute or .text is empty.")
                    final_response = "抱歉，AI助手暂时无法给出回复，请稍后再试。" # 更具体的错误
                    if hasattr(gemini_response, 'prompt_feedback'):
                        print(f"Gemini prompt feedback: {gemini_response.prompt_feedback}")
                    if hasattr(gemini_response, 'candidates') and gemini_response.candidates:
                        print(f"Gemini candidates: {gemini_response.candidates}")
                        if gemini_response.candidates[0].content and gemini_response.candidates[0].content.parts:
                             final_response = "".join(part.text for part in gemini_response.candidates[0].content.parts if hasattr(part, 'text'))
                             print(f"Extracted text from Gemini candidates: {final_response}")
                             if not final_response.strip(): # 如果从candidates提取的文本也是空的
                                 final_response = "AI助手收到了回复但内容为空，请尝试换个问法。"
                        else:
                            final_response = "AI助手返回了无法直接解析的回复结构。"
                    else:
                        final_response = "AI助手没有返回预期的文本回复结构。"

            except Exception as e:
                print(f"调用 Gemini API 失败: {e}")
                final_response = "抱歉，AI助手暂时遇到问题，请稍后再试。"
        else: # Gemini不可用，且不是算账
            final_response = "抱歉，我现在无法处理您的请求，也无法连接到我的知识库。请稍后再试。" # 已修正此处的冒号

    return jsonify({'response': final_response})

if __name__ == '__main__':
    app.run(debug=True)
