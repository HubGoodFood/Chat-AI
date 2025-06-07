import sys
import os
# Add the project root directory to sys.path to allow for absolute imports from src
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')) # Three levels up from src/app/chat
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import re
import logging
from src.config import settings as config
from typing import Tuple, Optional, Dict, Any, Union
from src.core.cache import CacheManager
from src.app.products.manager import ProductManager
from src.app.policy.manager import PolicyManager
from src.app.intent.classifier import IntentClassifier
import random

# 配置日志
logger = logging.getLogger(__name__)

class ChatHandler:
    """聊天处理类，负责处理用户输入和意图识别"""
    
    def __init__(self, product_manager: ProductManager,
                 policy_manager: PolicyManager = None,
                 cache_manager: CacheManager = None):
        """初始化聊天处理器
        
        Args:
            product_manager (ProductManager): 产品管理器实例
            cache_manager (CacheManager, optional): 缓存管理器实例
        """
        self.product_manager = product_manager
        self.policy_manager = policy_manager or PolicyManager()
        self.cache_manager = cache_manager or CacheManager()
        self.intent_classifier = IntentClassifier(model_path="src/models/intent_model") # 初始化意图分类器
        
        # 用户会话状态
        self.user_sessions = {}  # {user_id: session_data}
        
        # 最后识别的产品上下文
        self._last_identified_product_key = None
        self._last_identified_product_details = None
        
        # 用于处理纯粹价格追问的关键词
        self.PURE_PRICE_QUERY_KEYWORDS = ["多少钱", "什么价", "价格是", "几多钱", "价格", "售价"]
        self.PURE_POLICY_QUERY_KEYWORDS = ["什么政策", "政策是", "规定是", "有啥规定"]
        # 可以继续添加其他纯粹查询的关键词列表，例如针对库存、描述等
        
    @property
    def last_identified_product_key(self):
        """获取最后识别的产品key"""
        return self._last_identified_product_key
        
    @last_identified_product_key.setter
    def last_identified_product_key(self, value):
        """设置最后识别的产品key，同时更新产品详情
        
        Args:
            value (str): 产品key
        """
        self._last_identified_product_key = value
        if value:
            self._last_identified_product_details = self.product_manager.product_catalog.get(value)
        else:
            self._last_identified_product_details = None
            
    @property
    def last_identified_product_details(self):
        """获取最后识别的产品详情"""
        return self._last_identified_product_details

    def get_user_session(self, user_id: str) -> Dict[str, Any]:
        """获取用户会话数据，如果不存在则创建新会话
        
        Args:
            user_id (str): 用户ID
            
        Returns:
            dict: 用户会话数据
        """
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'last_query': None,
                'last_product_key': None,
                'last_product_details': None,
                'last_bot_mentioned_product_payload': None, # 新增：存储机器人上一轮提及的产品信息
                'context': {},
                'history': [],
                'preferences': {
                    'categories': [],  # 用户偏好的产品类别
                    'products': []      # 用户偏好的具体产品
                }
            }
        return self.user_sessions[user_id]
        
    def update_user_session(self, user_id: str,
                          query: str = None,
                          product_key: str = None,
                          product_details: Dict = None,
                          context_updates: Dict = None,
                          bot_mentioned_product_payload_update: Optional[Dict] = None) -> None: # 新增参数
        """更新用户会话数据

        Args:
            user_id (str): 用户ID
            query (str, optional): 用户查询
            product_key (str, optional): 产品key
            product_details (dict, optional): 产品详情
            context_updates (dict, optional): 上下文更新
            bot_mentioned_product_payload_update (Optional[Dict], optional): 更新机器人提及的产品信息.
        """
        session = self.get_user_session(user_id)

        if query is not None:
            session['last_query'] = query
            # 避免过长的历史记录，可以限制长度
            if len(session['history']) > 20:
                session['history'].pop(0)
            session['history'].append(query)

        if product_key is not None: # Allow product_key to be explicitly set to None
            session['last_product_key'] = product_key
            session['last_product_details'] = product_details
        elif product_key is None and 'last_product_key' in session: # If product_key is explicitly None, clear it
            session['last_product_key'] = None
            session['last_product_details'] = None


        if context_updates:
            session['context'].update(context_updates)
        
        # 更新机器人提及的产品信息
        session['last_bot_mentioned_product_payload'] = bot_mentioned_product_payload_update

        # 更新用户偏好
        if product_key and product_details: # Use the general product_key and product_details for preferences
            category = product_details.get('category')
            if category:
                if category not in session['preferences']['categories']:
                    session['preferences']['categories'].append(category)
                    logger.debug(f"User {user_id} added category '{category}' to preferences.")
            if product_key not in session['preferences']['products']:
                session['preferences']['products'].append(product_key)
                logger.debug(f"User {user_id} added product '{product_key}' to preferences.")

        # 更新缓存
        self.cache_manager.set_user_session(user_id, session)
        
    def preprocess_user_input(self, user_input: str, user_id: str) -> Tuple[str, str]:
        """预处理用户输入，处理上下文追问
        
        Args:
            user_input (str): 原始用户输入
            user_id (str): 用户ID
            
        Returns:
            tuple: (处理后的用户输入, 原始用户输入)
        """
        user_input_original = user_input
        user_input_processed = user_input.lower().strip()
        
        # 获取用户会话
        session = self.get_user_session(user_id)
        last_product_details = session.get('last_product_details')

        # 1. 处理纯粹的查询追问 (例如，在识别出"草莓"后，用户直接问"多少钱？")
        if last_product_details:
            product_name_for_context = last_product_details.get('original_display_name')
            if not product_name_for_context:
                product_name_for_context = last_product_details.get('name')

            if product_name_for_context:
                # 构建一个正则表达式来匹配纯粹查询词，允许末尾有可选的语气词
                normalized_input = re.sub(r"([呢呀啊吧吗？?！!]$)|('s)", '', user_input_processed).strip() # 移除末尾语气词和's
                
                is_pure_price_query = any(keyword == normalized_input for keyword in self.PURE_PRICE_QUERY_KEYWORDS)
                # 可以为 PURE_POLICY_QUERY_KEYWORDS 等其他列表添加类似的检查
                # is_pure_policy_query = any(keyword == normalized_input for keyword in self.PURE_POLICY_QUERY_KEYWORDS)

                if is_pure_price_query: # 或者 is_pure_policy_query 等
                    user_input_processed = f"{product_name_for_context} {user_input_processed}"
                    logger.debug(f"扩展后的查询 (纯粹价格/政策等追问): {user_input_processed}")
                    # 一旦处理了这种纯粹追问，可以提前返回，避免后续的通用追问逻辑冲突
                    return user_input_processed, user_input_original

        # 2. 处理通用的上下文追问 (例如，在识别出"草莓"后，用户问"它新鲜吗？")
        is_follow_up = any(keyword in user_input_processed 
                          for keyword in config.FOLLOW_UP_KEYWORDS)
        
        if is_follow_up and last_product_details:
            product_name = last_product_details.get('original_display_name')
            if not product_name:
                 product_name = last_product_details.get('name')

            if product_name and product_name.lower() not in user_input_processed: # 确保产品名没在原始输入中，避免重复添加
                user_input_processed = f"{product_name} {user_input_processed}"
                logger.debug(f"扩展后的查询 (通用追问): {user_input_processed}")
                
        return user_input_processed, user_input_original

    def _extract_product_name_from_query(self, query: str) -> str:
        """
        从查询中提取产品名称，修复"卖不卖草莓"变成"不草莓"的bug

        Args:
            query: 用户查询文本

        Returns:
            str: 提取的产品名称或清洗后的查询
        """
        import re

        if not query:
            return ""

        # 首先尝试直接匹配已知产品名称
        if self.product_manager and self.product_manager.product_catalog:
            for product_key, product_details in self.product_manager.product_catalog.items():
                product_name = product_details.get('name', '')
                original_name = product_details.get('original_display_name', '')

                # 检查产品名称是否在查询中
                for name in [product_name, original_name]:
                    if name and name.lower() in query.lower():
                        logger.debug(f"直接匹配到产品名称: '{name}' 在查询 '{query}' 中")
                        return name

                # 反向匹配：检查查询中的产品关键词是否在产品名称中
                # 这对于"梨有？"匹配"雪花梨蜜梨"这种情况很有用
                query_clean = query.replace('有？', '').replace('有?', '').replace('有吗', '').replace('卖吗', '').replace('卖不卖', '').replace('有没有', '').strip()
                if query_clean and len(query_clean) >= 1:
                    for name in [product_name, original_name]:
                        if name and query_clean.lower() in name.lower():
                            logger.debug(f"反向匹配到产品名称: 查询关键词 '{query_clean}' 在产品名称 '{name}' 中")
                            # 返回用户查询中的关键词，而不是完整的产品名称
                            # 这样更符合用户的期望，例如"梨有？"应该提取出"梨"而不是"雪花梨蜜梨"
                            return query_clean

        # 如果没有直接匹配，使用正则表达式清洗
        cleaned_query = query

        # 定义需要移除的模式（使用正则表达式，避免部分匹配问题）
        patterns_to_remove = [
            r'^卖不卖\s*',      # 开头的"卖不卖"
            r'^有没有\s*',      # 开头的"有没有"
            r'^有不有\s*',      # 开头的"有不有"（口语化）
            r'^卖不\s*',        # 开头的"卖不"（口语化）
            r'^有不\s*',        # 开头的"有不"（口语化）
            r'^有\s*',          # 开头的"有"（但要小心不要移除产品名称中的"有"）
            r'\s*卖不卖[\?？!！。]*$',   # 结尾的"卖不卖"
            r'\s*有没有[\?？!！。]*$',   # 结尾的"有没有"
            r'\s*有不有[\?？!！。]*$',   # 结尾的"有不有"
            r'\s*卖不[\?？!！。]*$',     # 结尾的"卖不"
            r'\s*有不[\?？!！。]*$',     # 结尾的"有不"
            r'\s*卖吗[\?？!！。]*$',     # 结尾的"卖吗"
            r'\s*有吗[\?？!！。]*$',     # 结尾的"有吗"
            r'\s*有[\?？!！。]*$',       # 结尾的"有？"（新增：修复"草莓有？"问题）
            r'\s*吗[\?？!！。]*$',       # 结尾的"吗"
            r'\s*呢[\?？!！。]*$',       # 结尾的"呢"
            r'\s*啊[\?？!！。]*$',       # 结尾的"啊"
            r'\s*多少钱\s*',    # "多少钱"
            r'\s*价格\s*',      # "价格"
            r'^我要\s*',        # 开头的"我要"
            r'^你们\s*',        # 开头的"你们"
            r'\s*怎么卖\s*',    # "怎么卖"
            r'\s*一斤多少\s*',  # "一斤多少"
            r'\s*售价\s*',      # "售价"
        ]

        for pattern in patterns_to_remove:
            cleaned_query = re.sub(pattern, '', cleaned_query, flags=re.IGNORECASE)

        cleaned_query = cleaned_query.strip()

        # 如果清洗后为空或太短，返回原始查询
        if not cleaned_query or len(cleaned_query) < 2:
            return query

        logger.debug(f"查询清洗: '{query}' -> '{cleaned_query}'")
        return cleaned_query

    def detect_intent(self, user_input_processed: str) -> str:
        """
        使用微调后的模型检测用户意图。
        如果模型不可用，则回退到基于关键词的简单规则检测。
        """
        # --- 规则优先：首先检查明确的、高优先级的模式 ---
        
        # 1. 检查是否是纯粹的问候语 (高优先级)
        # 避免模型将 "你好" 错误地识别为对包含 "好" 字的产品的查询
        greeting_keywords = ["你好", "您好", "hi", "hello", "在吗"]
        if user_input_processed in greeting_keywords:
            return 'greeting'

        # 2. 检查是否是身份查询 (高优先级)
        # 使用更灵活的规则来捕获各种身份查询，避免模型误判
        identity_phrases = ["你是谁", "你叫什么", "你是什么", "介绍下自己"]
        if any(phrase in user_input_processed for phrase in identity_phrases):
            return 'identity_query'

        identity_triggers = ["你是", "你是不是"]
        identity_nouns = ["机器人", "ai", "chatgpt", "助手", "真人"]
        if any(trigger in user_input_processed for trigger in identity_triggers) and \
           any(noun in user_input_processed for noun in identity_nouns):
            return 'identity_query'

        # --- 模型预测：如果不是明确的规则匹配，则使用模型 ---
        if self.intent_classifier and self.intent_classifier.model:
            predicted_intent = self.intent_classifier.predict(user_input_processed)
            # 如果模型给出了一个明确的意图（不是unknown），则使用它
            if predicted_intent != 'unknown':
                return predicted_intent
        
        # --- 模型不可用或预测为 'unknown' 时的回退规则 ---
        logger.warning(f"模型无法预测意图或预测为unknown，回退到规则检测: '{user_input_processed}'")

        # 如果所有规则都未匹配，则返回 'unknown'，交由 LLM 兜底处理
        return 'unknown'
        
    def handle_chat_message(self, user_input: str, user_id: str) -> Union[str, Dict, None]:
        """处理用户的聊天消息"""
        if not user_input or not user_input.strip():
            return "抱歉，我没有听清您说什么。请再说一遍。"

        # 获取用户会话和上下文信息
        session = self.get_user_session(user_id)
        last_bot_mentioned_payload = session.get('last_bot_mentioned_product_payload')

        # 1. 检查是否是来自前端按钮的直接产品选择
        if user_input.startswith("product_selection:"):
            # 规范化从前端收到的key：去除首尾空格并转为小写
            product_key = user_input.split(":", 1)[1].strip().lower()
            logger.info(f"处理来自按钮的产品选择，规范化后的key: '{product_key}'")
            
            # 修正错误：直接从 product_catalog 字典中获取产品信息
            product_details = self.product_manager.product_catalog.get(product_key)
            
            if product_details:
                # 构建一个丰富、详细的回复
                response_parts = []
                product_name_display = product_details.get('original_display_name', product_details.get('name', '这款产品'))

                # 问候语
                greeting = random.choice([
                    f"好的，我们来看看「{product_name_display}」的详细信息：",
                    f"您选择了「{product_name_display}」，这是一个很棒的选择！",
                    f"「{product_name_display}」，为您介绍一下："
                ])
                response_parts.append(greeting)

                # 价格和规格
                price_info = f"价格是 ${product_details.get('price', 0):.2f}/{product_details.get('specification', 'N/A')}。"
                response_parts.append(price_info)

                # 其他详细信息
                details_map = {
                    'category': ("它属于我们的「{}」系列。", "这是我们「{}」分类中的精品。"),
                    'taste': ("说到口感，它{}，很多顾客都特别喜欢！", "这款产品的口感特点是{}，非常独特。"),
                    'origin': ("它来自{}，保证新鲜优质。", "产地是{}，品质有保障。"),
                    'benefits': ("对健康的好处包括：{}。", "它的营养价值很高，特别是{}。"),
                    'suitablefor': ("特别推荐给{}。", "很适合{}享用。"),
                    'description': ("另外，{}", "补充一点，{}")
                }
                for detail_key, phrases in details_map.items():
                    value = product_details.get(detail_key)
                    if value:
                        response_parts.append(random.choice(phrases).format(value))
                
                # 关键词
                keywords = product_details.get('keywords', [])
                if keywords:
                    keywords_str = "、".join(keywords)
                    response_parts.append(f"它的特点可以概括为：{keywords_str}。")

                # 结束语
                closing = random.choice([
                    "\n您有什么其他问题，或者需要了解其他产品吗？",
                    "\n需要我为您推荐搭配的其他商品吗？",
                    "\n还有其他想了解的吗？随时告诉我哦！"
                ])
                response_parts.append(closing)
                
                final_response = "\n".join(response_parts)
                
                # 更新会话上下文并增加产品热度
                self.update_user_session(user_id, query=user_input, product_key=product_key, product_details=product_details)
                self.product_manager.update_product_popularity(product_key)
                return final_response
            else:
                logger.error(f"产品选择失败：在目录中未找到key为 '{product_key}' 的产品。")
                return "抱歉，查找您选择的产品信息时出了一点问题，请稍后再试。"

        # 2. (原步骤1) 预处理用户输入，处理追问等
        user_input_processed, user_input_original = self.preprocess_user_input(user_input, user_id)

        # 3. (原步骤2) 识别用户意图
        intent = self.detect_intent(user_input_processed)
        logger.debug(f"用户 '{user_id}' 的意图被识别为: {intent}")

        # 3. 根据意图分发到不同的处理函数
        final_response = None
        extracted_product_payload = None # 用于存储从回复中提取的产品信息

        if intent == 'identity_query':
            final_response = "我是这里的生鲜小助手，专门为您挑选最新鲜的食材，有什么可以帮您的吗？"

        elif intent == 'greeting':
            final_response = random.choice([
                "您好！有什么可以帮您的吗？",
                "嗨！今天想来点什么新鲜的？",
                "您好，我是您的专属生鲜小助手，随时为您服务！"
            ])

        elif intent == 'quantity_follow_up': # 这个意图在新的分类器中没有，但可以保留规则作为回退
            final_response, product_key, product_details, _ = self.handle_quantity_follow_up(user_input_processed, user_id)
            if product_key and product_details:
                self.update_user_session(user_id, query=user_input_original, product_key=product_key, product_details=product_details)

        elif intent == 'what_do_you_sell':
            final_response = self.handle_what_do_you_sell()

        elif intent == 'request_recommendation' or intent == 'recommendation_follow_up': # 合并推荐意图
            # handle_recommendation 现在返回一个包含 'message' 和 'product_suggestions' 的字典
            direct_category = "其他" if intent == 'recommendation_follow_up' else None
            recommendation_result = self.handle_recommendation(user_input_processed, user_id, direct_category=direct_category)
            final_response = recommendation_result # 这将是一个字典
            # extracted_product_payload 的逻辑将在下面处理 product_suggestions 时更新
            if recommendation_result.get("product_suggestions"):
                first_suggestion = recommendation_result["product_suggestions"][0]
                product_details_for_payload = self.product_manager.product_catalog.get(first_suggestion.get('payload'))
                if product_details_for_payload:
                    extracted_product_payload = {
                        'key': first_suggestion.get('payload'),
                        'name': product_details_for_payload.get('original_display_name') or product_details_for_payload.get('name'),
                        'price': product_details_for_payload.get('price'),
                        'specification': product_details_for_payload.get('specification'),
                        'description': product_details_for_payload.get('description')
                    }

        elif intent == 'inquiry_policy':
            final_response = self.handle_policy_question(user_input_processed)

        # 将 price_or_buy 和新增加的 inquiry_availability 都指向 handle_price_or_buy
        # handle_price_or_buy 内部逻辑会处理找到和找不到产品的情况，这对于两种意图都适用
        elif intent == 'inquiry_price_or_buy' or intent == 'inquiry_availability':
            response, session_updated, product_key, product_details = self.handle_price_or_buy(user_input_processed, user_input_original, user_id, last_bot_mentioned_payload)
            if not session_updated and product_key: # 如果handle_price_or_buy内部没有更新会话
                self.update_user_session(user_id, query=user_input_original, product_key=product_key, product_details=product_details)
            final_response = response
        
        # 4. 如果没有特定意图，使用 LLM 进行兜底
        if final_response is None:
            logger.info(f"没有明确的意图匹配，为查询 '{user_input_original}' 启动 LLM 兜底。")
            final_response, extracted_product_payload = self.handle_llm_fallback(user_input, user_input_processed, user_id)

        # 5. 更新会话中机器人提及的产品信息
        # 注意：如果 final_response 是一个 dict (带有按钮)，我们需要从中提取信息
        if isinstance(final_response, dict) and "product_suggestions" in final_response:
             # 如果有多个建议，只记录第一个作为上下文
            if final_response["product_suggestions"]:
                first_suggestion_payload_str = final_response["product_suggestions"][0].get('payload')
                if first_suggestion_payload_str:
                    # Payload 存储的是产品key，我们需要产品详情
                    product_details_for_payload = self.product_manager.product_catalog.get(first_suggestion_payload_str)
                    if product_details_for_payload:
                         bot_mentioned_payload = {
                            'key': first_suggestion_payload_str,
                            'name': product_details_for_payload.get('original_display_name') or product_details_for_payload.get('name'),
                            'price': product_details_for_payload.get('price'),
                            'specification': product_details_for_payload.get('specification')
                        }
                         self.update_user_session(user_id, bot_mentioned_product_payload_update=bot_mentioned_payload)
        elif extracted_product_payload: # 如果LLM回复中提取了产品信息
            self.update_user_session(user_id, bot_mentioned_product_payload_update=extracted_product_payload)
        else:
             # 如果没有新的产品被提及，清除上一轮的记录
            self.update_user_session(user_id, bot_mentioned_product_payload_update=None)
            
        return final_response

    def handle_what_do_you_sell(self) -> str:
        """处理用户询问"你们卖什么"或类似请求。
        
        会展示产品的主要类别和部分热门产品。

        Returns:
            str: 回复字符串，列出产品类别和示例。
        """
        if self.product_manager.product_catalog:
            response_parts = ["我们主要提供以下生鲜和美食："]
            
            # 从 product_manager 获取类别和产品
            categories_from_catalog = {} 
            for key, details in self.product_manager.product_catalog.items():
                cat = details.get('category', '未分类')
                if cat not in categories_from_catalog:
                    categories_from_catalog[cat] = []
                if len(categories_from_catalog[cat]) < 4: # 每个类别最多显示4个
                    categories_from_catalog[cat].append(details['original_display_name'])
            
            if not categories_from_catalog:
                response_parts.append("我们的产品种类丰富，例如：")
                count = 0
                # 使用 product_manager 的方法获取热门产品
                sorted_products = self.product_manager.get_popular_products(limit=5)
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

    def handle_recommendation(self, user_input_processed: str, user_id: str, direct_category: Optional[str] = None) -> Dict[str, Any]:
        """处理用户的产品推荐请求。
        Args:
            user_input_processed (str): 处理过的用户输入（小写）。
            user_id (str): 用户ID。
            direct_category (Optional[str], optional): 直接指定的目标类别. Defaults to None.

        Returns:
            Dict[str, Any]: 包含 'message' (str) 和 'product_suggestions' (list of dict) 的字典。
                           product_suggestions 中的每个字典包含 'display_text' 和 'payload'。
        """
        response_message: str
        product_suggestions_list: list = []
        # new_bot_mention_payload 的逻辑将通过 product_suggestions 的第一个元素来处理

        if not self.product_manager.product_catalog:
            response_message = "我们的产品正在准备中，暂时无法为您推荐，非常抱歉！"
            return {"message": response_message, "product_suggestions": product_suggestions_list}

        target_category = None
        if direct_category:
            target_category = direct_category
            logger.info(f"Using direct_category for recommendation: {target_category}")
        else:
            category_from_input = self.product_manager.find_related_category(user_input_processed)
            if not category_from_input:
                for cat_name_from_csv in self.product_manager.product_categories.keys():
                    if cat_name_from_csv.lower() in user_input_processed:
                        category_from_input = cat_name_from_csv
                        logger.info(f"Found category '{category_from_input}' from product_categories in input.")
                        break
            if category_from_input:
                target_category = category_from_input
        
        logger.info(f"推荐请求最终的目标类别: {target_category}")

        response_parts = []
        if target_category:
            response_parts.append(f"为您推荐几款我们这里不错的{target_category}：")
        else:
            response_parts.append("为您推荐几款我们这里的优选好物：")

        recommended_products = [] # List of (key, details, tag)
        # ... (existing recommendation logic to populate recommended_products) ...
        # 使用 product_manager 的方法获取产品
        seasonal = self.product_manager.get_seasonal_products(3, target_category)
        for key, details in seasonal:
            recommended_products.append((key, details, "当季新鲜"))

        if len(recommended_products) < 3:
            popular = self.product_manager.get_popular_products(3 - len(recommended_products), target_category)
            for key, details in popular:
                if key not in [p[0] for p in recommended_products]: # 避免重复
                    recommended_products.append((key, details, "热门好评"))

        if len(recommended_products) < 3 and target_category:
            category_prods_all = self.product_manager.get_products_by_category(target_category, limit=10)
            category_prods_filtered = [(k,d) for k,d in category_prods_all if k not in [p[0] for p in recommended_products]]
            needed = 3 - len(recommended_products)
            for key, details in category_prods_filtered[:needed]:
                 recommended_products.append((key, details, "精选"))

        if not recommended_products or len(recommended_products) < 3:
            needed_fallback_count = 3 - len(recommended_products)
            potential_fallback_pool = {}
            for key, details in self.product_manager.get_seasonal_products(limit=5):
                if key not in [p[0] for p in recommended_products] and key not in potential_fallback_pool:
                    potential_fallback_pool[key] = (details, "当季推荐")
            for key, details in self.product_manager.get_popular_products(limit=5):
                if key not in [p[0] for p in recommended_products] and key not in potential_fallback_pool:
                    tag_to_use = "热门单品"
                    if key in self.product_manager.seasonal_products:
                        tag_to_use = "当季热门"
                    potential_fallback_pool[key] = (details, tag_to_use)

            fallback_candidates = list(potential_fallback_pool.items())
            random.shuffle(fallback_candidates)
            existing_categories_in_rec = {details['category'] for _, details, _ in recommended_products}
            added_count = 0
            for key, (details, tag) in fallback_candidates:
                if added_count >= needed_fallback_count: break
                if details['category'] not in existing_categories_in_rec:
                    recommended_products.append((key, details, tag))
                    existing_categories_in_rec.add(details['category'])
                    added_count += 1
            if added_count < needed_fallback_count:
                for key, (details, tag) in fallback_candidates:
                    if added_count >= needed_fallback_count: break
                    if key not in [p[0] for p in recommended_products]:
                        recommended_products.append((key, details, tag))
                        added_count += 1
            if len(recommended_products) < 3:
                all_product_keys = [k for k in self.product_manager.product_catalog.keys() if k not in [p[0] for p in recommended_products]]
                random.shuffle(all_product_keys)
                for key in all_product_keys:
                    if len(recommended_products) >= 3: break
                    details = self.product_manager.product_catalog[key]
                    tag = "为您甄选"
                    if key in self.product_manager.seasonal_products: tag = "当季鲜品"
                    elif self.product_manager.popular_products.get(key,0) > 0 : tag = "人气好物"
                    recommended_products.append((key, details, tag))
        # --- End of existing recommendation logic to populate recommended_products ---


        if recommended_products:
            final_recommendations = recommended_products[:config.MAX_PRODUCT_SUGGESTIONS_BUTTONS] # 使用配置的最大按钮数
            for i, (key, details, tag) in enumerate(final_recommendations):
                # 构建按钮的显示文本
                button_display_text = f"{details.get('original_display_name', details.get('name', '未知产品'))} (${details.get('price', 0):.2f})"
                product_suggestions_list.append({
                    "display_text": button_display_text,
                    "payload": key # payload 是产品键，用于后续处理
                })

                # 构建回复消息中的产品描述部分
                base_display_info = f"{details.get('original_display_name', details.get('name', '未知产品'))}: ${details.get('price', 0):.2f}/{details.get('specification', 'N/A')}"
                description = details.get('description', '')
                if description: base_display_info += f" - {description}"
                
                explanation = ""
                if tag == "当季新鲜": explanation = " (这款是当季的，保证新鲜！😋)"
                elif tag == "热门好评": explanation = " (这款特别受欢迎，很多朋友都推荐！👍)"
                elif tag == "精选": explanation = " (这是我们为您精心挑选的优质品！✨)"
                elif tag in ["为您优选", "当季推荐", "热门单品", "为您甄选", "当季鲜品", "人气好物"] and tag: explanation = f" ({tag}！)"
                response_parts.append(f"- {base_display_info}{explanation if explanation else ''}")
                self.product_manager.update_product_popularity(key)

            if product_suggestions_list:
                 response_parts.append("\n您可以点击上面的产品按钮直接选择，或者告诉我您对哪个感兴趣，想了解更多，还是需要其他推荐？")
            else: # 如果没有生成任何按钮（理论上不应该发生，因为前面有fallback）
                 response_parts.append("\n您对哪个感兴趣，想了解更多，还是需要其他推荐？")
        else:
            response_parts.append("我们的产品正在精心准备中，暂时无法为您提供具体推荐，非常抱歉！")
        
        response_message = "\n".join(response_parts)
        
        return {"message": response_message, "product_suggestions": product_suggestions_list}

    def handle_policy_question(self, user_input_processed: str) -> Optional[str]:
        """根据用户输入，使用语义搜索返回相关的政策语句。"""
        if not self.policy_manager or not self.policy_manager.model:
            logger.warning("PolicyManager or semantic model not available for policy question.")
            # Fallback to LLM if PolicyManager is not properly initialized
            return None # Let LLM handle it

        try:
            # 使用语义搜索查找最相关的政策句子
            relevant_sentences = self.policy_manager.find_policy_excerpt_semantic(user_input_processed, top_k=3)

            if relevant_sentences:
                # 将找到的句子格式化为回复
                response_parts = ["关于您的政策问题，以下信息可能对您有帮助："]
                for sentence in relevant_sentences:
                    response_parts.append(f"- {sentence}")
                
                # 可选：添加政策版本和更新日期
                version = self.policy_manager.get_policy_version()
                last_updated = self.policy_manager.get_policy_last_updated()
                response_parts.append(f"\n(政策版本: {version}, 最后更新: {last_updated})")

                return "\n".join(response_parts)
            else:
                # 如果语义搜索没有找到相关句子，可以尝试关键词搜索作为备用
                keyword_excerpt = self.policy_manager.find_policy_excerpt([user_input_processed])
                if keyword_excerpt:
                     return f"关于您的政策问题，以下信息可能对您有帮助：\n- {keyword_excerpt}"
                else:
                    # 如果关键词搜索也失败，返回一个通用的、引导性的回复
                    return "关于您提到的政策问题，我暂时没有找到非常具体的信息。您可以换个方式问我，比如“退货政策”或“运费”吗？"

        except Exception as e:
            logger.error(f"Error handling policy question with semantic search: {e}")
            # 如果发生异常，返回一个友好的错误提示
            return "抱歉，在查询政策信息时遇到了一点技术问题，我们正在尽快修复！"

    def _handle_price_or_buy_fallback_recommendation(self, user_input_original: str, user_input_processed: str, identified_query_product_name: Optional[str]) -> Optional[Union[str, Dict[str, Any]]]:
        """辅助函数：当handle_price_or_buy未找到精确产品时，生成相关的产品推荐。

        Args:
            user_input_original (str): 原始用户输入。
            user_input_processed (str): 处理过的用户输入（小写）。
            identified_query_product_name (str or None): 从用户输入中初步识别出的产品名关键词。

        Returns:
            Union[str, Dict[str, Any]] or None: 如果能生成推荐，则返回推荐字符串或包含product_suggestions的字典，否则返回None。
        """
        # 使用新的智能推荐引擎
        query_product_name = identified_query_product_name or user_input_original

        # 尝试推断相关类别
        related_category = self.product_manager.find_related_category(user_input_processed)

        # 生成智能回复
        try:
            response = self.product_manager.generate_unavailable_product_response(
                query_product_name, related_category
            )
            if response:  # 确保有有效回复
                return response  # 现在返回字典格式 {message, product_suggestions}
        except Exception as e:
            logger.error(f"智能推荐引擎出错: {e}")
            # 继续执行备用逻辑

        # --- 原有逻辑作为备用 ---
        query_desc_keyword = identified_query_product_name

        # 如果上游没有成功提取出关键词，或者提取出的就是整个句子，我们在这里尝试一次更保守的清洗
        if not query_desc_keyword or query_desc_keyword == user_input_processed:
            temp_cleaned_query = user_input_processed
            # 只移除最明确的查询意图词，保留可能是名词的部分
            fallback_stopwords = config.GENERAL_QUERY_KEYWORDS + config.PRICE_QUERY_KEYWORDS + ["你们", "我们", "的", "吗", "呢", "呀", "啊"]
            for word in fallback_stopwords:
                temp_cleaned_query = temp_cleaned_query.replace(word, "")

            temp_cleaned_query = temp_cleaned_query.strip()

            # 如果清洗后有意义（不为空且长度大于1），就用它
            if temp_cleaned_query and len(temp_cleaned_query) > 1:
                query_desc_keyword = temp_cleaned_query
        # --- 修改结束 ---

        recommendation_items = []
        logger.info(f"Fallback Recommendation (Legacy): Related category: {related_category}, Query product keyword: {query_desc_keyword}")

        # 1. 如果有识别出的产品词或类别，优先推荐相关
        if query_desc_keyword or related_category:
            temp_recs = []
            # 基于产品名关键词推荐
            if query_desc_keyword:
                for key, details in self.product_manager.product_catalog.items():
                    if query_desc_keyword.lower() in details['name'].lower() or query_desc_keyword.lower() in key.lower():
                        if len(temp_recs) < 2: # 最多2个直接相关
                            temp_recs.append((key, details, f"与'{query_desc_keyword}'相关"))
                        else:
                            break
            # 基于类别推荐
            if related_category and len(temp_recs) < 3:
                cat_prods = self.product_manager.get_products_by_category(related_category, 3 - len(temp_recs))
                for k, d in cat_prods:
                    if all(k != r[0] for r in temp_recs): # 避免重复
                         temp_recs.append((k,d, f"{related_category}类推荐"))
            recommendation_items.extend(temp_recs)

        # 2. 补充当季和热门 (确保总数不超过3，且不重复)
        MAX_RECOMMENDATIONS = 3
        current_rec_keys = {rec[0] for rec in recommendation_items}

        if len(recommendation_items) < MAX_RECOMMENDATIONS:
            seasonal = self.product_manager.get_seasonal_products(MAX_RECOMMENDATIONS - len(recommendation_items), related_category)
            for key, details in seasonal:
                if key not in current_rec_keys:
                    recommendation_items.append((key, details, "当季推荐"))
                    current_rec_keys.add(key)
                    if len(recommendation_items) >= MAX_RECOMMENDATIONS: break
        
        if len(recommendation_items) < MAX_RECOMMENDATIONS:
            popular = self.product_manager.get_popular_products(MAX_RECOMMENDATIONS - len(recommendation_items), related_category)
            for key, details in popular:
                if key not in current_rec_keys:
                    recommendation_items.append((key, details, "热门推荐"))
                    current_rec_keys.add(key)
                    if len(recommendation_items) >= MAX_RECOMMENDATIONS: break

        if recommendation_items:
            # 在生成回复时，也使用新的关键词
            query_desc = f"'{query_desc_keyword if query_desc_keyword else user_input_original}'"
            
            recommendations_text_list = []
            for key, details, tag in recommendation_items[:MAX_RECOMMENDATIONS]: # 确保不超过最大推荐数
                recommendations_text_list.append(f"- {self.product_manager.format_product_display(details, tag=tag)}")
            recommendations_list_str = "\n".join(recommendations_text_list)

            # 使用统一的推荐引擎格式
            # 尝试使用新的推荐引擎生成回复
            try:
                # 构建推荐对象列表
                recommendations = []
                for key, details, tag in recommendation_items[:3]:
                    from src.app.products.recommendation_engine import ProductRecommendation
                    recommendations.append(ProductRecommendation(
                        product_key=key,
                        product_details=details,
                        similarity_score=0.7,  # 默认相似度
                        recommendation_reason=tag,
                        category_group=details.get('category', '其他')
                    ))

                # 使用推荐引擎生成统一格式的回复
                if hasattr(self.product_manager, 'recommendation_engine'):
                    response_dict = self.product_manager.recommendation_engine.generate_unavailable_response(
                        query_desc_keyword if query_desc_keyword else user_input_original,
                        recommendations,
                        related_category
                    )
                    return response_dict  # 现在返回字典格式 {message, product_suggestions}
            except Exception as e:
                logger.error(f"使用推荐引擎生成回复时出错: {e}")
                # 回退到简化的统一格式
                pass

            # 备用的统一格式回复
            product_name = query_desc_keyword if query_desc_keyword else user_input_original
            category_type = "产品"
            if related_category:
                category_mapping = {
                    "时令水果": "水果", "新鲜蔬菜": "蔬菜", "禽类产品": "禽类",
                    "海鲜河鲜": "海鲜", "美味熟食/面点": "熟食", "蛋类": "蛋类"
                }
                category_type = category_mapping.get(related_category, related_category)

            # 备用的统一格式回复 - 返回字符串格式以保持兼容性
            response_str = (
                f"{product_name}确实是很受欢迎的{category_type}呢！\n"
                f"不过很抱歉，我们目前暂时没有{product_name}。\n\n"
                f"不过，如果您喜欢{category_type}，我们有这些很棒的选择：\n\n"
                f"{recommendations_list_str}\n\n"
                f"这些里面有您感兴趣的吗？或者您还有其他偏好，我可以再帮您找找看！"
            )
            return response_str
        else:
            # 如果没有任何推荐，使用推荐引擎的无推荐回复
            try:
                if hasattr(self.product_manager, 'recommendation_engine'):
                    product_name = query_desc_keyword if query_desc_keyword else user_input_original
                    response = self.product_manager.recommendation_engine._generate_no_recommendations_response(product_name)
                    return response  # 现在返回字典格式 {message, product_suggestions}
            except Exception as e:
                logger.error(f"生成无推荐回复时出错: {e}")

            # 备用的统一格式回复
            final_query_desc = query_desc_keyword if query_desc_keyword else user_input_original
            return {
                'message': (
                    f"您想要的{final_query_desc}确实是个不错的选择！\n"
                    f"很抱歉，我们目前暂时没有{final_query_desc}。\n\n"
                    f"不过，您可以告诉我您更偏好哪种类型的产品吗？比如是水果、蔬菜，还是其他特定的东西？"
                    f"这样我也许能帮您找到合适的替代品。"
                ),
                'product_suggestions': []
            }

    def handle_price_or_buy(self,
                            user_input_processed: str,
                            user_input_original: str,
                            user_id: str,
                            last_bot_mentioned_payload: Optional[Dict]  # 新增参数
                           ) -> Tuple[Optional[Union[str, Dict]], bool, Optional[str], Optional[Dict]]:
        """处理用户的价格查询或购买意图。
        Args:
            user_input_processed (str): 处理过的用户输入（小写）。
            user_input_original (str): 原始用户输入。
            user_id (str): 用户ID。
            last_bot_mentioned_payload (Optional[Dict]): 上一轮机器人提及的产品信息。
        Returns:
            tuple: (response_obj, handled_bool, new_general_context_key, new_bot_mention_payload_for_next_turn)
        """
        session = self.get_user_session(user_id)
        final_response: Optional[Union[str, Dict]] = None
        intent_handled = False
        new_general_context_key: Optional[str] = session.get('last_product_key') # Initialize with current general context
        new_bot_mention_payload_for_next_turn: Optional[Dict] = None


        # 1. 检查是否是针对上一轮机器人提及产品的纯粹价格追问
        normalized_input_for_price_check = re.sub(r"([呢呀啊吧吗？?！!]$)|('s)", '', user_input_processed).strip()
        is_pure_price_query = any(keyword == normalized_input_for_price_check for keyword in self.PURE_PRICE_QUERY_KEYWORDS)

        if last_bot_mentioned_payload and is_pure_price_query:
            # 从 payload 中获取所需信息
            product_key = last_bot_mentioned_payload.get('key')
            product_name = last_bot_mentioned_payload.get('name')
            price = last_bot_mentioned_payload.get('price')
            specification = last_bot_mentioned_payload.get('specification')
            description = last_bot_mentioned_payload.get('description')

            if product_key and product_name and price is not None and specification is not None:
                logger.info(f"Handling price query for last bot-mentioned product: {product_name} (key: {product_key})")
                final_response = f"{product_name} 的价格是 ${price:.2f}/{specification}。"
                if description:
                    final_response += f"\n\n{description}"
                
                intent_handled = True
                new_general_context_key = product_key # Update general context to this product
                # Context consumed, so new_bot_mention_payload_for_next_turn remains None (clearing it)
                self.product_manager.update_product_popularity(product_key) # Update popularity
                return final_response, True, new_general_context_key, None # Explicitly return None for next bot mention

        # 2. 如果不是上下文追问，或者上下文无效，则执行现有逻辑
        if not intent_handled and self.product_manager.product_catalog:
            is_buy_action = any(keyword in user_input_processed for keyword in config.BUY_INTENT_KEYWORDS)
            is_price_action = any(keyword in user_input_processed for keyword in config.PRICE_QUERY_KEYWORDS)

            # --- 核心修改：改进的查询清洗逻辑，修复"卖不卖草莓"变成"不草莓"的bug ---
            query_for_matching = self._extract_product_name_from_query(user_input_processed)

            # 如果提取失败，使用原始输入进行后续处理
            if not query_for_matching:
                query_for_matching = user_input_processed

            logger.debug(f"清洗后的查询，用于模糊匹配: '{query_for_matching}' (原始: '{user_input_processed}')")
            # --- 修改结束 ---

            possible_matches = self.product_manager.fuzzy_match_product(query_for_matching) # 使用清洗后的查询
            acceptable_matches = [(key, score) for key, score in possible_matches if score >= config.MIN_ACCEPTABLE_MATCH_SCORE]

            if not acceptable_matches:
                # 如果模糊匹配没有找到任何可接受的结果，
                # 我们将清理后的查询词 'query_for_matching' 作为最可能的产品关键词。
                # 这个词（例如从“有没有草莓”中提取的“草莓”）比原始的、未处理的输入更适合用于生成“未找到”的提示信息。
                query_product_name_keyword = query_for_matching
                
                # 使用统一的推荐引擎处理产品不可用场景
                try:
                    related_category = self.product_manager.find_related_category(user_input_processed)
                    final_response = self.product_manager.generate_unavailable_product_response(
                        query_product_name_keyword, related_category
                    )
                except Exception as e:
                    logger.error(f"推荐引擎处理失败: {e}")
                    # 备用简单回复
                    final_response = {
                        'message': (
                            f"您想要的{query_product_name_keyword}确实是个不错的选择！\n"
                            f"很抱歉，我们目前暂时没有{query_product_name_keyword}。\n\n"
                            f"您可以告诉我您更偏好哪种类型的产品吗？这样我也许能帮您找到合适的替代品。"
                        ),
                        'product_suggestions': []
                    }
                new_general_context_key = None # Fallback recommendation clears general product context
                new_bot_mention_payload_for_next_turn = None # Fallback rec usually doesn't set a single product context
                intent_handled = True
            else:
                acceptable_matches.sort(key=lambda x: x[1], reverse=True)
                top_match_key, top_score = acceptable_matches[0]
                
                # --- 新的澄清逻辑 ---
                # 默认进行澄清，除非我们非常确定只有一个最佳匹配
                needs_clarification = True

                if len(acceptable_matches) <= 1:
                    # 如果只有一个或没有可接受的匹配项，则无需澄清
                    needs_clarification = False
                else: # 有多个匹配项
                    top_score = acceptable_matches[0][1]
                    second_score = acceptable_matches[1][1]
                    
                    # 仅当最高分非常高（例如 > 0.9）且远超第二名时，才跳过澄清
                    if top_score > 0.9 and top_score > second_score * 1.5:
                        needs_clarification = False
                
                clarification_candidates = []
                if needs_clarification:
                    # 从 acceptable_matches 构建澄清候选项
                    added_candidate_display_names = set()
                    for key, score in acceptable_matches:
                        if len(clarification_candidates) >= config.MAX_CLARIFICATION_OPTIONS: break
                        
                        product_details_cand = self.product_manager.product_catalog.get(key)
                        if product_details_cand:
                            # 使用 original_display_name 来避免合并不同规格的同名产品
                            product_display_name = product_details_cand['original_display_name']
                            if product_display_name not in added_candidate_display_names:
                                clarification_candidates.append((key, product_details_cand, score))
                                added_candidate_display_names.add(product_display_name)
                    
                    # 如果过滤后（例如，所有匹配都是同一产品的不同规格）只剩一个或没有候选项，则也不需要澄清
                    if len(clarification_candidates) <= 1:
                        needs_clarification = False

                if needs_clarification:
                    clarification_options_list = [{"display_text": dtls['original_display_name'], "payload": k} for k, dtls, _ in clarification_candidates]
                    # 构建更友好的提问消息
                    product_names_for_clarification = "、".join([f"[{opt['display_text']}]" for opt in clarification_options_list])
                    clarification_message = f"您好，关于您咨询的产品，我找到了几个相似的：您是指 {product_names_for_clarification} 呢？请点击选择。"
                    final_response = {"message": clarification_message, "clarification_options": clarification_options_list}
                    new_general_context_key = None
                    new_bot_mention_payload_for_next_turn = None # Clarification awaits user, no bot mention yet
                    intent_handled = True
                else: # No clarification needed, process top_match_key
                    product_details = self.product_manager.product_catalog.get(top_match_key)
                    if not product_details:
                        final_response = "抱歉，查找产品信息时出了一点小问题。"
                        intent_handled = True
                        new_bot_mention_payload_for_next_turn = None
                    else:
                        quantity = 1
                        try_names = [product_details['original_display_name'], product_details['name']]
                        best_match_pos = -1
                        for name_variant in try_names:
                            pos = user_input_processed.find(name_variant.lower())
                            if pos != -1: best_match_pos = pos; break
                        if best_match_pos == -1:
                            pos = user_input_processed.find(top_match_key.lower()) # Match key case-insensitively
                            if pos != -1: best_match_pos = pos
                        
                        weight_query_keywords = ["多重", "多少重", "什么重量", "称重", "多大"]
                        price_only_query = is_price_action and not is_buy_action
                        weight_only_query = any(keyword in user_input_processed for keyword in weight_query_keywords)

                        if not price_only_query and not weight_only_query and best_match_pos != -1:
                            text_before_product = user_input_processed[:best_match_pos]
                            qty_search = re.search(r'([\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*$', text_before_product.strip())
                            if qty_search:
                                num_str = qty_search.group(1)
                                try: quantity = int(num_str)
                                except ValueError: quantity = self.product_manager.convert_chinese_number_to_int(num_str)
                        
                        item_total = quantity * product_details['price']
                        
                        self.product_manager.update_product_popularity(top_match_key)

                        # 构建包含所有产品信息的自然回复
                        response_parts = []
                        product_name_display = product_details.get('original_display_name', product_details.get('name', '这款产品'))

                        # 使用更自然的问候语开头
                        greeting_options = [
                            f"太好了！您选择的「{product_name_display}」真的很不错呢！",
                            f"好的，「{product_name_display}」是个很棒的选择！",
                            f"您挑选的「{product_name_display}」非常受欢迎呢！"
                        ]
                        response_parts.append(random.choice(greeting_options))
                        
                        # 价格信息
                        price_phrases = [
                            f"它的价格是每{product_details.get('unit', '份')} ${product_details.get('price', '未知'):.2f}，规格是{product_details.get('specification', '未注明')}。",
                            f"现在售价是 ${product_details.get('price', '未知'):.2f}/{product_details.get('specification', '未注明')}。"
                        ]
                        response_parts.append(random.choice(price_phrases))
                        
                        # 类别信息
                        category = product_details.get('category')
                        if category:
                            category_phrases = [
                                f"它属于我们的「{category}」系列。",
                                f"这是我们「{category}」分类中的精品。"
                            ]
                            response_parts.append(random.choice(category_phrases))

                        # 口感信息
                        taste = product_details.get('taste')
                        if taste:
                            taste_phrases = [
                                f"说到口感，它{taste}，很多顾客都特别喜欢！",
                                f"这款产品的口感特点是{taste}，非常独特。"
                            ]
                            response_parts.append(random.choice(taste_phrases))
                        
                        # 产地信息
                        origin = product_details.get('origin')
                        if origin:
                            origin_phrases = [
                                f"它来自{origin}，保证新鲜优质。",
                                f"产地是{origin}，品质有保障。"
                            ]
                            response_parts.append(random.choice(origin_phrases))
                            
                        # 益处信息
                        benefits = product_details.get('benefits')
                        if benefits:
                            benefits_phrases = [
                                f"对健康的好处包括：{benefits}，很适合注重健康的朋友。",
                                f"它的营养价值很高，特别是{benefits}。"
                            ]
                            response_parts.append(random.choice(benefits_phrases))
                            
                        # 适用人群
                        suitable_for = product_details.get('suitablefor')
                        if suitable_for:
                            suitable_phrases = [
                                f"特别推荐给{suitable_for}。",
                                f"很适合{suitable_for}享用。"
                            ]
                            response_parts.append(random.choice(suitable_phrases))
                        
                        # 关键词信息
                        keywords_list = product_details.get('keywords', [])
                        if keywords_list and isinstance(keywords_list, list) and len(keywords_list) > 0:
                            keywords_str = "、".join(keywords_list)
                            keywords_phrases = [
                                f"顾客们常用这些词来形容它：{keywords_str}。",
                                f"它的特点可以概括为：{keywords_str}。"
                            ]
                            response_parts.append(random.choice(keywords_phrases))
                        elif product_details.get('keywords') and isinstance(product_details.get('keywords'), str):
                            # 处理可能是字符串的情况
                            keywords_str = product_details.get('keywords')
                            if ';' in keywords_str:
                                keywords_list = [k.strip() for k in keywords_str.split(';')]
                            else:
                                keywords_list = [keywords_str]
                            if keywords_list:
                                keywords_display = "、".join(keywords_list)
                                response_parts.append(f"它的特点可以概括为：{keywords_display}。")

                        # 描述信息
                        description = product_details.get('description')
                        if description:
                            description_phrases = [
                                f"另外，{description}",
                                f"补充一点，{description}"
                            ]
                            response_parts.append(random.choice(description_phrases))

                        # 购买信息
                        if is_buy_action:
                            buy_phrases = [
                                f"\n如果您购买 {quantity} {product_details.get('unit', '份')}，总共是 ${item_total:.2f}。需要为您准备吗？",
                                f"\n{quantity} {product_details.get('unit', '份')}的总价是 ${item_total:.2f}。您想要购买吗？"
                            ]
                            response_parts.append(random.choice(buy_phrases))
                        else:
                            closing_phrases = [
                                "\n您有什么其他问题，或者需要了解其他产品吗？",
                                "\n需要我为您推荐搭配的其他商品吗？",
                                "\n还有其他想了解的吗？随时告诉我哦！"
                            ]
                            response_parts.append(random.choice(closing_phrases))
                        
                        final_response = "\n".join(response_parts)
                        
                        new_general_context_key = top_match_key
                        # Bot is "mentioning" this product by confirming its details/price
                        new_bot_mention_payload_for_next_turn = {
                            'key': top_match_key,
                            'name': product_details.get('original_display_name') or product_details.get('name'),
                            'price': product_details.get('price'),
                            'specification': product_details.get('specification'),
                            'description': product_details.get('description')
                        }
                        intent_handled = True
        
        if not intent_handled: # Should only be reached if product_catalog is empty initially
            logger.warning(f"Price_or_buy intent for '{user_input_processed}' could not be handled (e.g. empty catalog).")
            final_response = "抱歉，我们的产品信息似乎还没有准备好，请稍后再试。"
            intent_handled = True # Mark as handled to prevent LLM fallback on this specific error
            new_general_context_key = None
            new_bot_mention_payload_for_next_turn = None
        
        logger.debug(f"handle_price_or_buy is about to return: intent_handled={intent_handled}, final_response_type={type(final_response)}")
        return final_response, intent_handled, new_general_context_key, new_bot_mention_payload_for_next_turn

    def handle_llm_fallback(self, user_input: str, user_input_processed: str, user_id: str) -> Tuple[str, Optional[Dict]]:
        """当规则无法处理用户输入时，调用LLM进行回复。

        会构建包含系统提示、先前识别的产品（如有）和部分相关产品列表的上下文给LLM。
        现在还会尝试从LLM的回复中提取提及的产品信息。

        Args:
            user_input (str): 原始用户输入。
            user_input_processed (str): 处理过的用户输入（小写）。
            user_id (str): 用户ID。

        Returns:
            Tuple[str, Optional[Dict]]: (LLM生成的回复, 可能提取到的产品payload)
        """
        session = self.get_user_session(user_id)
        final_response = ""
        extracted_product_payload = None
        
        # 尝试从缓存获取LLM响应
        cached_llm_response = self.cache_manager.get_llm_cached_response(user_input, context=session.get('last_product_key'))
        if cached_llm_response:
            logger.info(f"LLM fallback response retrieved from cache for: {user_input[:30]}...")
            return cached_llm_response, None

        if not config.llm_client: # llm_client 现在从 config 模块获取
            logger.warning("LLM client is not available. Skipping LLM fallback.")
            return "抱歉，我现在无法深入理解您的问题，AI助手服务暂未连接。", None
        try:
            system_prompt = (
                "你是一位专业的生鲜产品客服。你的回答应该友好、自然且专业。"
                "请尽量让对话像和真人聊天一样自然、流畅。主要任务是根据顾客的询问，结合我提供的产品列表（如果本次对话提供了的话）来回答问题。"
                "1. 当被问及我们有什么产品、特定类别的产品（如水果、时令水果、蔬菜等）或推荐时，你必须首先且主要参考我提供给你的产品列表上下文。请从该列表中选择相关的产品进行回答。"
                "2. 如果产品列表上下文中没有用户明确询问的产品，请礼貌地告知，例如：'抱歉，您提到的XX我们目前可能没有，不过我们有这些相关的产品：[列举列表中的1-2个相关产品]'。不要虚构我们没有的产品。"
                "3. 如果用户只是打招呼（如'你好'），请友好回应。"
                "4. 对于算账和精确价格查询，我会尽量自己处理。如果我处理不了，或者你需要补充信息，请基于我提供的产品列表（如果有）进行回答。"
                "5. 避免使用过于程序化或模板化的AI语言。请注意变换您的句式和表达方式，避免多次使用相同的开头或结尾，让顾客感觉像在和机器人对话。"
                "6. 专注于水果、蔬菜及相关生鲜产品。如果用户询问完全无关的话题，请委婉地引导回我们的产品和服务。"
                "7. 推荐产品时，请着重突出当季新鲜产品，并尽量提供产品特点、口感或用途等信息，让推荐更有说服力。"
                "8. 如果用户询问某个特定类别的产品，请专注于提供该类别的产品信息，并根据产品描述给出个性化建议。"
                "9. 如果用户提到'刚才'、'刚刚'等词，请注意可能是在询问上一个提到的产品。"
                "10. 如果上文提到过某个产品 (session['last_product_details']), 而当前用户问题不清晰，可以优先考虑与该产品相关。"
                "11. (新增) 如果顾客的问题不是很明确（例如只说'随便看看'或者'有什么好的'），请主动提问来澄清他们的需求，比如询问他们偏好的品类（水果、蔬菜等）、口味（甜的、酸的）、或者用途（自己吃、送礼等）。"
                "12. (新增) 当顾客遇到问题或者对某些信息不满意时，请表现出同理心，并积极尝试帮助他们解决问题或找到替代方案。在对话中，可以适当运用一些亲和的语气词，但避免过度使用表情符号。"
                "13. (重要) 当告知用户某商品缺货时，你必须严格遵循以下统一的三步结构来回复，确保温暖、人性化的中文表达：\n"
                "    a. **共情与确认**: 首先，用一句话对用户想找的商品表示理解和认可。例如：'草莓确实是很受欢迎的水果呢！'或'您想要的鸡肉，眼光真好！'\n"
                "    b. **明确告知缺货**: 接着，用温暖、抱歉的语气告知我们暂时没有该商品。例如：'不过很抱歉，我们目前暂时没有草莓。'或'可惜的是，这款产品现在正好缺货呢。'\n"
                "    c. **智能推荐替代品**: 最后，从我提供的产品列表中，选择2-3个最相关的同类产品作为替代品，并说明推荐理由。格式为：'不过，如果您喜欢[类别]，我们有这些很棒的选择：\\n\\n• [产品1] - [特色描述]\\n• [产品2] - [特色描述]\\n\\n这些里面有您感兴趣的吗？或者您还有其他偏好，我可以再帮您找找看！'\n"
                "    请确保：1) 不要重复相同的内容；2) 推荐的产品来自同一类别；3) 突出产品特色；4) 语气温暖自然。"
            )
            messages = [{"role": "system", "content": system_prompt}]
            
            context_for_llm = ""
            if session['last_product_details']:
                context_for_llm += f"用户上一次明确提到的或我为您识别出的产品是：{self.product_manager.format_product_display(session['last_product_details'])}\n"

            if self.product_manager.product_catalog:
                relevant_items_for_llm = []
                added_product_keys = set()
                MAX_LLM_CONTEXT_ITEMS = 7

                # 1. 优先添加与上一个产品同类别的产品
                if session['last_product_details'] and len(relevant_items_for_llm) < MAX_LLM_CONTEXT_ITEMS:
                    last_product_category = session['last_product_details'].get('category')
                    last_product_key_ctx = session['last_product_details'].get('original_display_name', '').lower()
                    if last_product_category:
                        for key, details in self.product_manager.product_catalog.items():
                            if len(relevant_items_for_llm) >= MAX_LLM_CONTEXT_ITEMS // 2: break
                            if key == last_product_key_ctx: continue
                            if details.get('category', '').lower() == last_product_category.lower():
                                if key not in added_product_keys:
                                    relevant_items_for_llm.append(details)
                                    added_product_keys.add(key)
                
                # 2. 基于用户查询中识别的类别添加产品
                user_asked_category_name = self.product_manager.find_related_category(user_input)
                if user_asked_category_name and len(relevant_items_for_llm) < MAX_LLM_CONTEXT_ITEMS:
                    for key, cat_details in self.product_manager.product_catalog.items():
                        if len(relevant_items_for_llm) >= MAX_LLM_CONTEXT_ITEMS: break
                        if cat_details.get('category', '').lower() == user_asked_category_name.lower():
                            if key not in added_product_keys:
                                relevant_items_for_llm.append(cat_details)
                                added_product_keys.add(key)
                
                # 3. 添加基于关键词匹配的产品
                if len(relevant_items_for_llm) < MAX_LLM_CONTEXT_ITEMS:
                    # 提取用户查询中的关键词
                    query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', user_input_processed))
                    matched_products = []
                    
                    # 尝试进行关键词匹配
                    for key, details in self.product_manager.product_catalog.items():
                        if key in added_product_keys: continue
                        
                        # 检查产品名称和关键词
                        product_words = set(re.findall(r'[\w\u4e00-\u9fff]+', details['name'].lower()))
                        product_words.update(details.get('keywords', []))
                        
                        # 计算匹配度
                        intersection = query_words.intersection(product_words)
                        if intersection:
                            matched_products.append((key, details, len(intersection)))
                    
                    # 按匹配度排序并添加
                    matched_products.sort(key=lambda x: x[2], reverse=True)
                    for key, details, _ in matched_products:
                        if len(relevant_items_for_llm) >= MAX_LLM_CONTEXT_ITEMS: break
                        relevant_items_for_llm.append(details)
                        added_product_keys.add(key)
                
                # 4. 添加当季产品
                if len(relevant_items_for_llm) < MAX_LLM_CONTEXT_ITEMS:
                    seasonal_products = self.product_manager.get_seasonal_products(
                        limit=MAX_LLM_CONTEXT_ITEMS - len(relevant_items_for_llm),
                        category=user_asked_category_name
                    )
                    for key, details in seasonal_products:
                        if key not in added_product_keys:
                            relevant_items_for_llm.append(details)
                            added_product_keys.add(key)
                
                # 5. 添加热门产品
                if len(relevant_items_for_llm) < MAX_LLM_CONTEXT_ITEMS:
                    popular_products = self.product_manager.get_popular_products(
                        limit=MAX_LLM_CONTEXT_ITEMS - len(relevant_items_for_llm),
                        category=user_asked_category_name
                    )
                    for key, details in popular_products:
                        if key not in added_product_keys:
                            relevant_items_for_llm.append(details)
                            added_product_keys.add(key)
                
                # 6. 如果仍然不足，随机添加一些产品
                if len(relevant_items_for_llm) < MAX_LLM_CONTEXT_ITEMS:
                    all_keys = list(self.product_manager.product_catalog.keys())
                    random.shuffle(all_keys)
                    for key in all_keys:
                        if len(relevant_items_for_llm) >= MAX_LLM_CONTEXT_ITEMS: break
                        if key not in added_product_keys:
                            relevant_items_for_llm.append(self.product_manager.product_catalog[key])
                            added_product_keys.add(key)

                if relevant_items_for_llm:
                    context_for_llm += "\n\n作为参考，这是我们目前的部分相关产品列表和价格（价格单位以实际规格为准）：\n"
                    for i, details in enumerate(relevant_items_for_llm[:MAX_LLM_CONTEXT_ITEMS]):
                        context_for_llm += f"- {self.product_manager.format_product_display(details)}\n"
            
            # 将所有系统信息合并到一条 system prompt 中，以避免模型混淆
            final_system_prompt = messages[0]['content'] # 从已有的 messages 列表开始
            if context_for_llm.strip():
                final_system_prompt += "\n\n---\n\n以下是产品参考信息，请在回答时利用这些信息：\n" + context_for_llm
            
            # 构建最终的消息列表
            final_messages = [
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": user_input}
            ]
                
            chat_completion = config.llm_client.chat.completions.create(
                model=config.LLM_MODEL_NAME,
                messages=final_messages,
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=config.LLM_TEMPERATURE
            )
            if chat_completion.choices and chat_completion.choices[0].message and chat_completion.choices[0].message.content:
                final_response = chat_completion.choices[0].message.content.strip()
                # 缓存LLM响应
                self.cache_manager.cache_llm_response(user_input, final_response, context=session.get('last_product_key'))
            else:
                final_response = "抱歉，AI助手暂时无法给出回复，请稍后再试。"
        except Exception as e:
            logger.error(f"调用 LLM API 失败: {e}")
            final_response = "抱歉，AI助手暂时遇到问题，请稍后再试。"

        # 尝试从LLM的回复中提取产品信息
        if final_response and not any(err_msg in final_response for err_msg in ["抱歉", "无法"]):
            if self.product_manager.product_catalog:
                price_keywords_in_llm_response = ["价格", "价钱", "多少钱", "元", "$", "块", "售价是", "卖"]
                llm_response_lower = final_response.lower()
                
                best_match_product_key = None
                longest_match_len = 0

                for key, details in self.product_manager.product_catalog.items():
                    product_name_variants = []
                    if details.get('original_display_name'):
                        product_name_variants.append(details.get('original_display_name').lower())
                    if details.get('name'):
                         product_name_variants.append(details.get('name').lower())
                    
                    # Ensure product names are non-empty and have a minimum length (e.g., 2)
                    product_name_variants = list(set(name for name in product_name_variants if name and len(name) >= 2))

                    for name_variant in product_name_variants:
                        if name_variant in llm_response_lower:
                            # Check if the response also contains price-related keywords
                            contains_price_keyword_in_reply = any(pk_word in llm_response_lower for pk_word in price_keywords_in_llm_response)
                            if contains_price_keyword_in_reply:
                                if len(name_variant) > longest_match_len:
                                    longest_match_len = len(name_variant)
                                    best_match_product_key = key
                
                if best_match_product_key:
                    product_details_llm = self.product_manager.product_catalog.get(best_match_product_key)
                    if product_details_llm:
                        extracted_product_payload = {
                            'key': best_match_product_key,
                            'name': product_details_llm.get('original_display_name') or product_details_llm.get('name'),
                            'price': product_details_llm.get('price'),
                            'specification': product_details_llm.get('specification'),
                            'description': product_details_llm.get('description')
                        }
                        logger.info(f"LLM fallback response potentially mentioned product: {extracted_product_payload['name']}")
        
        return final_response, extracted_product_payload