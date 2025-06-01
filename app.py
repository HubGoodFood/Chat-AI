from flask import Flask, request, jsonify, render_template
import os
import google.generativeai as genai

app = Flask(__name__)

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
if GEMINI_API_KEY:
    try:
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest') # 更改模型名称
    except Exception as e:
        print(f"初始化 Gemini 模型失败: {e}")
        gemini_model = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '') # 保持小写转换，但 Gemini 可能对大小写敏感，具体看模型
    response_from_local_kb = None

    # 1. 首先尝试从本地知识库查找答案
    # 更智能的果蔬知识库
    knowledge_base = {
        "苹果": {
            "营养": "苹果富含维生素C和纤维，有助于消化和增强免疫力。",
            "挑选": "挑选苹果时，应选择表皮光滑、色泽均匀、握起来比较硬实的。",
            "储存": "苹果可以在室温下保存几天，或者在冰箱冷藏可以保存更长时间。"
        },
        "香蕉": {
            "营养": "香蕉是钾的良好来源，有助于维持心脏健康和肌肉功能。",
            "挑选": "选择表皮金黄、没有太多黑斑的香蕉。如果想放久一点，可以选稍青一些的。",
            "储存": "香蕉应在室温下保存，避免放入冰箱，否则表皮会变黑。"
        },
        "橘子": {
            "营养": "橘子含有丰富的维生素C，可以帮助预防感冒。",
            "挑选": "挑选时选择果皮有光泽，果蒂新鲜，拿在手里有分量的橘子。",
            "储存": "橘子可以在阴凉通风处保存，也可以放入冰箱冷藏。"
        },
        "葡萄": {
            "营养": "葡萄含有抗氧化剂，对皮肤和心脏都有好处。",
            "挑选": "选择果粒饱满、颜色鲜艳、果梗新鲜的葡萄串。",
            "储存": "葡萄最好放入冰箱冷藏，并在几天内食用完毕。"
        },
        "草莓": {
            "营养": "草莓是维生素C和锰的良好来源，味道也很棒！",
            "挑选": "选择颜色鲜红、有光泽、果蒂新鲜的草莓，避免选择过软或有损伤的。",
            "储存": "草莓非常娇嫩，最好放入冰箱冷藏，并尽快食用。"
        },
        "蓝莓": {
            "营养": "蓝莓富含抗氧化剂，对大脑健康有益。",
            "挑选": "选择果实饱满、颜色呈深蓝色或蓝紫色、表面有一层白色果粉的蓝莓。",
            "储存": "蓝莓应放入冰箱冷藏，食用前再清洗。"
        },
        "西瓜": {
            "营养": "西瓜水分充足，是夏天解暑的好选择。",
            "挑选": "挑选西瓜时，可以看瓜皮纹路清晰、瓜蒂新鲜卷曲、拍起来声音清脆的。",
            "储存": "完整的西瓜可以在室温下保存，切开后需用保鲜膜包好放入冰箱。"
        },
        "白菜": {
            "营养": "白菜富含维生素K和维生素C，是一种非常健康的蔬菜。",
            "挑选": "选择叶片完整、颜色鲜嫩、根部结实的白菜。",
            "储存": "白菜可以在阴凉通风处保存，或者用保鲜膜包裹后放入冰箱冷藏。"
        },
        "胡萝卜": {
            "营养": "胡萝卜富含β-胡萝卜素，对眼睛健康非常有益。",
            "挑选": "选择表面光滑、颜色鲜艳、形状规整、有一定硬度的胡萝卜。",
            "储存": "胡萝卜可以去除顶部的叶子后，放入冰箱冷藏。"
        },
        "西兰花": {
            "营养": "西兰花是一种营养丰富的十字花科蔬菜，含有多种维生素和矿物质。",
            "挑选": "选择花球紧密、颜色鲜绿、没有黄化或开花的西兰花。",
            "储存": "西兰花可以用保鲜袋装好放入冰箱冷藏。"
        },
        "菠菜": {
            "营养": "菠菜富含铁质和维生素A，有助于补血和保护视力。",
            "挑选": "选择叶片鲜嫩、颜色深绿、没有黄叶或腐烂的菠菜。",
            "储存": "菠菜可以用湿纸巾包裹后放入保鲜袋，再放入冰箱冷藏。"
        },
        "番茄": {
            "营养": "番茄（西红柿）富含番茄红素，是一种强大的抗氧化剂。",
            "挑选": "选择颜色鲜红、果形圆润、表面有光泽的番茄。",
            "储存": "未完全成熟的番茄可以在室温下催熟，成熟后放入冰箱冷藏。"
        },
        "黄瓜": {
            "营养": "黄瓜水分含量高，热量低，非常适合夏天食用。",
            "挑选": "选择表皮鲜绿、有光泽、瓜身挺直、带有小刺的黄瓜。",
            "储存": "黄瓜可以用保鲜膜包裹后放入冰箱冷藏。"
        }
    }

    found_specific_in_local_kb = False
    user_input_lower = user_input.lower()
    for item_name, item_info in knowledge_base.items():
        if item_name.lower() in user_input_lower:
            if "挑选" in user_input_lower or "怎么选" in user_input_lower:
                response_from_local_kb = f"关于{item_name}的挑选技巧：{item_info.get('挑选', '我暂时还没有这方面的信息。')}"
            elif "储存" in user_input_lower or "怎么保存" in user_input_lower:
                response_from_local_kb = f"关于{item_name}的储存方法：{item_info.get('储存', '我暂时还没有这方面的信息。')}"
            else:
                response_from_local_kb = f"{item_name}是很棒的选择！{item_info.get('营养', '它是一种健康的食物。')}"
            found_specific_in_local_kb = True
            break

    if not found_specific_in_local_kb:
        if '水果' in user_input_lower:
            response_from_local_kb = "水果美味又健康！你最喜欢什么水果？或者可以问我一些具体的水果，比如苹果、香蕉，也可以问我它们的挑选或储存方法。"
        elif '蔬菜' in user_input_lower:
            response_from_local_kb = "蔬菜对身体很好！你最喜欢什么蔬菜？或者可以问我一些具体的蔬菜，比如白菜、胡萝卜，也可以问我它们的挑选或储存方法。"
        # 如果本地知识库没有找到特定答案，我们将依赖 Gemini

    # 2. 如果本地知识库没有答案，或者我们想让 Gemini 补充，则调用 Gemini API
    final_response = "抱歉，我暂时无法回答这个问题。"
    if gemini_model: # 检查模型是否成功初始化
        try:
            # 构建给 Gemini 的提示
            system_prompt = (
                "你是一位经验丰富的果蔬营养顾问和生鲜采购专家。请用自然、亲切且专业的口吻与用户交流，就像与一位朋友分享专业的果蔬知识一样。"
                "请避免使用过于刻板或程序化的语言，也不要主动提及自己是AI或模型。你的目标是提供准确、有用的信息，同时让对话感觉轻松愉快。"
                "专注于水果和蔬菜相关的话题。如果用户询问无关内容，请委婉地引导回果蔬主题。"
            )
            full_prompt = f"{system_prompt}\n\n用户问：{user_input}"
            
            # 如果本地知识库有初步答案，可以将其作为上下文提供给 Gemini (可选)
            if response_from_local_kb and response_from_local_kb != "我现在只能聊水果和蔬菜。跟我说说水果或蔬菜吧！或者问我某种果蔬的挑选技巧或储存方法。":
                 full_prompt += f"\n\n（我这里有一些关于此话题的基础信息：{response_from_local_kb} 你可以参考这个，并用更自然、更专业的方式来丰富和解答。）"

            gemini_response = gemini_model.generate_content(full_prompt)
            final_response = gemini_response.text
        except Exception as e:
            print(f"调用 Gemini API 失败: {e}")
            # 如果 Gemini 调用失败，可以回退到本地知识库的答案（如果有）或通用错误信息
            if response_from_local_kb:
                final_response = response_from_local_kb + " (Gemini AI 暂时无法连接，以上是本地信息)"
            else:
                final_response = "抱歉，AI助手暂时遇到问题，请稍后再试。"
    elif response_from_local_kb: # 如果 Gemini 未配置或初始化失败，但本地有答案
        final_response = response_from_local_kb
    # else: final_response 保持为初始的“抱歉...”

    return jsonify({'response': final_response})

if __name__ == '__main__':
    app.run(debug=True)
