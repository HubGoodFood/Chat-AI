import re
import logging
import config
from typing import Tuple, Optional, Dict, Any, Union
from cache_manager import CacheManager
from product_manager import ProductManager
from policy_manager import PolicyManager
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
        
    def detect_intent(self, user_input_processed: str) -> str:
        """检测用户意图
        
        Args:
            user_input_processed (str): 处理后的用户输入
            
        Returns:
            str: 意图类型 ('quantity_follow_up', 'what_do_you_sell',
                         'recommendation', 'price_or_buy', 'policy_question', 'identity_query', 'unknown')
        """
        # 检查是否是追问推荐的意图（如"其他"、"还有"）
        if any(k in user_input_processed for k in ["其他", "还有"]):
            return 'recommendation_follow_up'
        # 检查是否是纯数量追问
        quantity_pattern = r'^\s*([\d一二三四五六七八九十百千万俩两]+)\s*(?:份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*(?:呢|呀|啊|吧|多少钱|总共)?\s*$'
        if re.match(quantity_pattern, user_input_processed):
            return 'quantity_follow_up'
            
        # 检查是否询问"卖什么"
        if any(keyword in user_input_processed
               for keyword in config.WHAT_DO_YOU_SELL_KEYWORDS):
            return 'what_do_you_sell'
            
        # 检查是否是推荐请求
        if any(keyword in user_input_processed
               for keyword in config.RECOMMEND_KEYWORDS):
            return 'recommendation'
            
        # 检查是否是政策相关问题
        for keywords in config.POLICY_KEYWORD_MAP.values():
            if any(k in user_input_processed for k in keywords):
                return 'policy_question'

        # 检查机器人身份查询
        identity_keywords = ["你是谁", "你叫什么", "你是什么", "什么模型", "你的名字", "who are you", "what are you"]
        if any(keyword in user_input_processed for keyword in identity_keywords):
            return 'identity_query'

        # 检查是否是价格查询或购买意图
        if (any(keyword in user_input_processed for keyword in config.PRICE_QUERY_KEYWORDS) or
            any(keyword in user_input_processed for keyword in config.BUY_INTENT_KEYWORDS)):
            return 'price_or_buy'
        
        # 如果输入中直接包含可匹配的产品名称或关键词，也视为价格查询
        try:
            fuzzy = self.product_manager.fuzzy_match_product(user_input_processed)
            if fuzzy:
                return 'price_or_buy'
        except Exception:
            pass
        
        return 'unknown'
        
    def handle_quantity_follow_up(self, user_input_processed: str, user_id: str) -> Tuple[Optional[str], Optional[str], Optional[Dict], Optional[Dict]]:
        """处理用户在提及一个产品后，仅用数量进行追问的场景。
        
        Args:
            user_input_processed (str): 处理过的用户输入（小写）。
            user_id (str): 用户ID。

        Returns:
            Tuple: (response_str, new_general_context_key, new_general_context_details, new_bot_mention_payload)
        """
        session = self.get_user_session(user_id)
        last_product_key = session.get('last_product_key')
        
        response_str: Optional[str] = None
        new_general_context_key: Optional[str] = last_product_key # Default to existing
        new_general_context_details: Optional[Dict] = session.get('last_product_details')
        new_bot_mention_payload: Optional[Dict] = None

        quantity_follow_up_match = re.fullmatch(
            r'\s*([\d一二三四五六七八九十百千万俩两]+)\s*(份|个|条|块|包|袋|盒|瓶|箱|打|磅|斤|公斤|kg|g|只|听|罐|组|件|本|支|枚|棵|株|朵|头|尾|条|片|串|扎|束|打|筒|碗|碟|盘|杯|壶|锅|桶|篮|筐|篓|扇|面|匹|卷|轴|封|枚|锭|丸|粒|钱|两|克|斗|石|顷|亩|分|厘|毫)?\s*(?:呢|呀|啊|吧|多少钱|总共)?\s*',
            user_input_processed
        )
        
        if quantity_follow_up_match and last_product_key:
            logger.info(f"Detected quantity follow-up for product: {last_product_key}")
            try:
                quantity_str = quantity_follow_up_match.group(1)
                try:
                    quantity = int(quantity_str)
                except ValueError:
                    quantity = self.product_manager.convert_chinese_number_to_int(quantity_str)
                
                product_details = self.product_manager.product_catalog.get(last_product_key)
                if product_details:
                    item_price = product_details['price']
                    original_display_name = product_details['original_display_name']
                    original_unit_desc = product_details['specification']
                    item_total = quantity * item_price
                    
                    response_str = f"好的，{quantity} ({original_unit_desc}) 的 {original_display_name} 总共是 ${item_total:.2f}。"
                    new_general_context_key = last_product_key
                    new_general_context_details = product_details
                    # Bot is confirming/mentioning this product
                    new_bot_mention_payload = {
                        'key': last_product_key,
                        'name': product_details.get('original_display_name') or product_details.get('name'),
                        'price': product_details.get('price'),
                        'specification': product_details.get('specification'),
                        'description': product_details.get('description')
                    }
                    self.product_manager.update_product_popularity(last_product_key)
                else:
                    logger.error(f"last_identified_product_key '{last_product_key}' not found in PRODUCT_CATALOG.")
            except Exception as e:
                logger.error(f"处理数量追问时出错: {e}")
        
        return response_str, new_general_context_key, new_general_context_details, new_bot_mention_payload

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

    def handle_recommendation(self, user_input_processed: str, user_id: str, direct_category: Optional[str] = None) -> Tuple[str, Optional[Dict]]:
        """处理用户的产品推荐请求。
        Args:
            user_input_processed (str): 处理过的用户输入（小写）。
            user_id (str): 用户ID。
            direct_category (Optional[str], optional): 直接指定的目标类别. Defaults to None.

        Returns:
            Tuple[str, Optional[Dict]]: (回复字符串, new_bot_mention_payload)
        """
        response_str: str
        new_bot_mention_payload: Optional[Dict] = None

        if not self.product_manager.product_catalog:
            response_str = "我们的产品正在准备中，暂时无法为您推荐，非常抱歉！"
            return response_str, new_bot_mention_payload

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
            final_recommendations = recommended_products[:3]
            for i, (key, details, tag) in enumerate(final_recommendations):
                base_display_info = f"{details.get('original_display_name', details.get('name', '未知产品'))}: ${details.get('price', 0):.2f}/{details.get('specification', 'N/A')}"
                description = details.get('description', '')
                if description: base_display_info += f" - {description}"
                explanation = ""
                if tag == "当季新鲜": explanation = " (这款是当季的，保证新鲜！😋)"
                elif tag == "热门好评": explanation = " (这款特别受欢迎，很多朋友都推荐！👍)"
                elif tag == "精选": explanation = " (这是我们为您精心挑选的优质品！✨)"
                elif tag in ["为您优选", "当季推荐", "热门单品"] and tag: explanation = f" ({tag}！)"
                response_parts.append(f"- {base_display_info}{explanation if explanation else ''}")
                self.product_manager.update_product_popularity(key)

                # Set the first recommended product as the bot-mentioned product for context
                if i == 0: # Take the first one as the primary mention
                    new_bot_mention_payload = {
                        'key': key,
                        'name': details.get('original_display_name') or details.get('name'),
                        'price': details.get('price'),
                        'specification': details.get('specification'),
                        'description': details.get('description')
                    }
            response_parts.append("\n您对哪个感兴趣，想了解更多，还是需要其他推荐？")
        else:
            response_parts.append("我们的产品正在精心准备中，暂时无法为您提供具体推荐，非常抱歉！")
        
        response_str = "\n".join(response_parts)
        
        # context_updates for last_recommendation_category is handled by handle_chat_message if needed
        # This function now primarily returns the response and any bot mention.
        return response_str, new_bot_mention_payload

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
                    # 如果关键词搜索也失败，返回None让LLM处理
                    return None

        except Exception as e:
            logger.error(f"Error handling policy question with semantic search: {e}")
            # 如果发生异常，返回None让LLM处理
            return None

    def _handle_price_or_buy_fallback_recommendation(self, user_input_original: str, user_input_processed: str, identified_query_product_name: Optional[str]) -> Optional[str]:
        """辅助函数：当handle_price_or_buy未找到精确产品时，生成相关的产品推荐。

        Args:
            user_input_original (str): 原始用户输入。
            user_input_processed (str): 处理过的用户输入（小写）。
            identified_query_product_name (str or None): 从用户输入中初步识别出的产品名关键词。

        Returns:
            str or None: 如果能生成推荐，则返回推荐字符串，否则返回None。
        """
        recommendation_items = []
        related_category = self.product_manager.find_related_category(user_input_original) 
        logger.info(f"Fallback Recommendation: Related category: {related_category}, Query product keyword: {identified_query_product_name}")

        # 1. 如果有识别出的产品词或类别，优先推荐相关
        if identified_query_product_name or related_category:
            temp_recs = []
            # 基于产品名关键词推荐
            if identified_query_product_name:
                for key, details in self.product_manager.product_catalog.items():
                    if identified_query_product_name.lower() in details['name'].lower() or identified_query_product_name.lower() in key.lower():
                        if len(temp_recs) < 2: # 最多2个直接相关
                            temp_recs.append((key, details, f"与'{identified_query_product_name}'相关"))
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
            query_desc = f"'{identified_query_product_name if identified_query_product_name else user_input_original}'" \
                         if (identified_query_product_name or user_input_original) else "您查询的产品"
            
            recommendations_text_list = []
            for key, details, tag in recommendation_items[:MAX_RECOMMENDATIONS]: # 确保不超过最大推荐数
                recommendations_text_list.append(f"- {self.product_manager.format_product_display(details, tag=tag)}")
            recommendations_list_str = "\n".join(recommendations_text_list)

            response_str = (
                f"您好！您提到的'{query_desc}'我们暂时没有完全一样的呢。不过，这里有几款相似或店里很受欢迎的产品，"
                f"您可以看看喜不喜欢：\n\n{recommendations_list_str}\n\n"
                f"这些里面有您中意的吗？或者，如果您能告诉我您更偏好哪种口味、品类或者有什么特定需求，"
                f"我非常乐意再帮您精心挑选一下！"
            )
            return response_str
        else:
            # 如果没有任何推荐，返回引导性提示
            # 动态获取一些品类作为示例
            category_examples = []
            if self.product_manager and self.product_manager.product_categories:
                all_categories = list(self.product_manager.product_categories.keys())
                if len(all_categories) > 0:
                    random.shuffle(all_categories) # 随机打乱
                    # 取前3个或所有（如果不足3个）
                    example_count = min(3, len(all_categories))
                    category_examples = [f"【{cat}】" for cat in all_categories[:example_count]]
            
            if category_examples:
                examples_str = "、".join(category_examples)
                return (
                    f"哎呀，真不好意思，您提到的'{user_input_original}'我们店里暂时还没有呢。要不您看看我们其他的分类？"
                    f"比如我们有新鲜的{examples_str}都很受欢迎。"
                    f"您对哪个品类感兴趣，或者想找点什么特定口味的吗？告诉我您的想法，我来帮您参谋参谋！"
                )
            else: # 如果连品类都没有，给出更通用的提示
                return (
                    f"哎呀，真不好意思，您提到的'{user_input_original}'我们店里暂时还没有呢。"
                    f"您可以告诉我您想找的是哪一类产品吗？比如是水果、蔬菜，还是其他特定的东西？"
                    f"或者您对产品的口味、产地有什么偏好吗？这样我也许能帮您找到合适的替代品。"
                )

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

            possible_matches = self.product_manager.fuzzy_match_product(user_input_processed)
            acceptable_matches = [(key, score) for key, score in possible_matches if score >= config.MIN_ACCEPTABLE_MATCH_SCORE]

            if not acceptable_matches:
                query_product_name_keyword = None
                user_words = set(re.findall(r'[\w\u4e00-\u9fff]+', user_input_original.lower()))
                best_match_len = 0
                for word in user_words:
                    if len(word) < config.MIN_SUBSTRING_MATCH_LENGTH: continue
                    for key, details in self.product_manager.product_catalog.items():
                        if word in details['name'].lower() and len(word) > best_match_len:
                            query_product_name_keyword = details['name']
                            best_match_len = len(word)
                final_response = self._handle_price_or_buy_fallback_recommendation(user_input_original, user_input_processed, query_product_name_keyword)
                new_general_context_key = None # Fallback recommendation clears general product context
                new_bot_mention_payload_for_next_turn = None # Fallback rec usually doesn't set a single product context
                intent_handled = True
            else:
                acceptable_matches.sort(key=lambda x: x[1], reverse=True)
                top_match_key, top_score = acceptable_matches[0]
                
                clarification_candidates = []
                added_candidate_names = set()
                for key, score in acceptable_matches:
                    if len(clarification_candidates) >= config.MAX_CLARIFICATION_OPTIONS: break
                    if score >= config.PRICE_OR_BUY_CLARIFICATION_CANDIDATE_THRESHOLD:
                        product_details_cand = self.product_manager.product_catalog.get(key)
                        if product_details_cand:
                            product_name_for_clar = product_details_cand['name']
                            if product_name_for_clar not in added_candidate_names:
                                clarification_candidates.append((key, product_details_cand, score))
                                added_candidate_names.add(product_name_for_clar)
                
                needs_clarification = False
                if len(clarification_candidates) > 1:
                    if top_score < config.DOMINANT_MATCH_THRESHOLD:
                        if len(clarification_candidates) > 1 and (top_score - clarification_candidates[1][2]) < config.SIGNIFICANT_SCORE_DIFFERENCE:
                            needs_clarification = True
                    if len(set(c[1]['name'] for c in clarification_candidates)) > 1:
                         needs_clarification = True
                if len(clarification_candidates) <= 1 or top_score >= config.DOMINANT_MATCH_THRESHOLD:
                    needs_clarification = False
                if len(clarification_candidates) > 1 and clarification_candidates[0][1]['name'] == clarification_candidates[1][1]['name']:
                    needs_clarification = False

                if needs_clarification:
                    clarification_options_list = [{"display_text": dtls['original_display_name'], "payload": k} for k, dtls, _ in clarification_candidates]
                    final_response = {"message": "请问您指的是以下哪种产品？", "clarification_options": clarification_options_list}
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

                        if weight_only_query:
                            response_parts = [f"{self.product_manager.format_product_display(product_details)} 的规格重量如您所见。"]
                            response_parts.append(f"单价是 ${product_details['price']:.2f}/{product_details['specification']}。")
                            final_response = "\n".join(response_parts)
                        elif price_only_query or (is_price_action and not is_buy_action):
                            base_info = self.product_manager.format_product_display(product_details)
                            final_response = f"{base_info.split(':')[0]} 的价格是 ${product_details['price']:.2f}/{product_details['specification']}。"
                            if product_details.get('description'):
                                final_response += f"\n\n{product_details['description']}"
                        elif is_buy_action:
                            response_parts = ["好的，这是您的订单详情："]
                            formatted_name_price_spec = self.product_manager.format_product_display(product_details).split(' - ')[0]
                            response_parts.append(f"- {formatted_name_price_spec} x {quantity} = ${item_total:.2f}")
                            response_parts.append(f"\n总计：${item_total:.2f}")
                            final_response = "\n".join(response_parts)
                        else: # Default: fuzzy query a product name, give price
                             base_info = self.product_manager.format_product_display(product_details)
                             final_response = f"{base_info.split(':')[0]} 的价格是 ${product_details['price']:.2f}/{product_details['specification']}。"
                             if product_details.get('description'):
                                 final_response += f"\n\n{product_details['description']}"
                        
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
                "11. (新增) 如果顾客的问题不是很明确（例如只说‘随便看看’或者‘有什么好的’），请主动提问来澄清他们的需求，比如询问他们偏好的品类（水果、蔬菜等）、口味（甜的、酸的）、或者用途（自己吃、送礼等）。"
                "12. (新增) 当顾客遇到问题或者对某些信息不满意时，请表现出同理心，并积极尝试帮助他们解决问题或找到替代方案。在对话中，可以适当运用一些亲和的语气词，但避免过度使用表情符号。"
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
            
            messages.append({"role": "system", "content": "产品参考信息：" + context_for_llm})
            messages.append({"role": "user", "content": user_input})
                
            chat_completion = config.llm_client.chat.completions.create(
                model=config.LLM_MODEL_NAME,
                messages=messages,
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

    def handle_chat_message(self, user_input: str, user_id: str) -> Union[str, Dict]:
        """处理用户发送的聊天消息。
        主要流程:
        1. 预处理用户输入 (处理上下文追问)。
        2. 检测意图。
        3. 根据意图调用相应的处理函数。
        4. 如果规则处理器都未处理，则调用 LLM 回退。
        5. 更新用户会话和全局上下文。
        6. 返回响应。
        """
        logger.info(f"--- Chat message received from user {user_id} --- Input: {user_input}")
        session = self.get_user_session(user_id)
        
        # Store bot mention from the *previous* turn. This will be used by handlers.
        bot_mention_from_last_turn = session.get('last_bot_mentioned_product_payload')

        user_input_processed, user_input_original = self.preprocess_user_input(user_input, user_id)
        # Initial session update for the query itself, without affecting bot_mentioned_product_payload yet
        # We will do a consolidated update at the end.
        # For now, just log query to history if needed by preprocess or other early logic.
        # session['last_query'] = user_input_original (will be part of final update)
        # session['history'].append(user_input_original) (will be part of final update)

        intent = self.detect_intent(user_input_processed)
        logger.info(f"Detected intent: {intent} for processed input: {user_input_processed}")
        
        final_response_obj: Optional[Union[str, Dict]] = None
        intent_handled = False
        # Initialize context keys with current session values; handlers will update them.
        new_general_context_key: Optional[str] = session.get('last_product_key')
        new_general_context_details: Optional[Dict] = session.get('last_product_details')
        new_bot_mention_for_next_turn: Optional[Dict] = None # This turn's bot action might set this
        context_updates_for_session: Dict = {}


        if intent == 'quantity_follow_up':
            response_str, gen_ctx_key, gen_ctx_details, bot_mention_payload = self.handle_quantity_follow_up(user_input_processed, user_id)
            if response_str:
                final_response_obj = response_str
                intent_handled = True
                new_general_context_key = gen_ctx_key
                new_general_context_details = gen_ctx_details
                new_bot_mention_for_next_turn = bot_mention_payload

        elif intent == 'what_do_you_sell':
            final_response_obj = self.handle_what_do_you_sell()
            intent_handled = True
            new_general_context_key = None
            new_general_context_details = None
            new_bot_mention_for_next_turn = None

        elif intent == 'recommendation':
            response_str, bot_mention_payload = self.handle_recommendation(user_input_processed, user_id)
            final_response_obj = response_str
            intent_handled = True
            new_general_context_key = None
            new_general_context_details = None
            new_bot_mention_for_next_turn = bot_mention_payload
            # Preserve last_recommendation_category if a category was targeted
            # This logic was previously in handle_recommendation's update_user_session call
            target_category_for_rec_context = None
            # Re-evaluate target_category as handle_recommendation doesn't expose it directly now
            # For simplicity, if bot_mention_payload exists and has a category, use it.
            # Or, parse from user_input_processed again if needed for context.
            # For now, let's assume recommendation context is mainly driven by the bot_mention.
            if new_bot_mention_for_next_turn and new_bot_mention_for_next_turn.get('key'):
                # Attempt to get category from the mentioned product's details
                mentioned_product_details_for_cat = self.product_manager.product_catalog.get(new_bot_mention_for_next_turn['key'])
                if mentioned_product_details_for_cat:
                     target_category_for_rec_context = mentioned_product_details_for_cat.get('category')
            if not target_category_for_rec_context: # Fallback to parsing from input if first item has no category
                 target_category_for_rec_context = self.product_manager.find_related_category(user_input_processed)

            if target_category_for_rec_context:
                 context_updates_for_session['last_recommendation_category'] = target_category_for_rec_context


        elif intent == 'policy_question':
            final_response_obj = self.handle_policy_question(user_input_processed)
            if final_response_obj:
                intent_handled = True
            new_general_context_key = None
            new_general_context_details = None
            new_bot_mention_for_next_turn = None

        elif intent == 'price_or_buy':
            # Pass the bot_mention_from_last_turn
            response_obj, handled, gen_ctx_key, bot_mention_payload = self.handle_price_or_buy(
                user_input_processed, user_input_original, user_id, bot_mention_from_last_turn
            )
            if handled:
                final_response_obj = response_obj
                intent_handled = True
                new_general_context_key = gen_ctx_key
                new_general_context_details = self.product_manager.product_catalog.get(gen_ctx_key) if gen_ctx_key else None
                new_bot_mention_for_next_turn = bot_mention_payload
        
        elif intent == 'identity_query':
            final_response_obj = "我是您的智能果蔬客服，很高兴为您服务！"
            intent_handled = True
            new_general_context_key = None
            new_general_context_details = None
            new_bot_mention_for_next_turn = None

        elif intent == 'recommendation_follow_up':
            last_rec_category = session.get('context', {}).get('last_recommendation_category')
            if last_rec_category:
                logger.info(f"Handling recommendation_follow_up for category: {last_rec_category}")
                response_str, bot_mention_payload = self.handle_recommendation(user_input_processed, user_id, direct_category=last_rec_category)
                final_response_obj = response_str
                new_bot_mention_for_next_turn = bot_mention_payload
                # Update last_recommendation_category in context if recommendation was successful for this category
                if bot_mention_payload: # Check if any product was actually recommended
                     context_updates_for_session['last_recommendation_category'] = last_rec_category

            else:
                logger.info("recommendation_follow_up, but no last_recommendation_category in session context.")
                final_response_obj = "您希望我继续推荐哪一类的产品呢？比如水果、蔬菜或者其他。"
            intent_handled = True
            new_general_context_key = None
            new_general_context_details = None
            # new_bot_mention_for_next_turn is set above if recommendation happened

        if not intent_handled:
            non_product_keywords = getattr(config, 'FUZZY_SEARCH_EXCLUSION_KEYWORDS', ["你好", "您好", "嗨", "hello", "在吗", "谢谢", "再见", "你是谁", "卖什么", "推荐点", "有什么推荐", "查订单", "退货"])
            min_fuzzy_length = getattr(config, 'MIN_FUZZY_SEARCH_LENGTH', 2)
            is_explicit_non_product_command = any(keyword in user_input_original.lower() for keyword in non_product_keywords)
            should_try_fuzzy_search = intent in ['unknown', 'price_or_buy']

            if should_try_fuzzy_search and not is_explicit_non_product_command and len(user_input_original) > min_fuzzy_length:
                logger.info(f"Attempting fuzzy product search for: '{user_input_original}' as intent was '{intent}' and not handled by specific rules.")
                similar_products = self.product_manager.find_similar_products(user_input_original)
                if similar_products:
                    log_similar_products = [(p[0], p[1].get('original_display_name')) if isinstance(p, tuple) and len(p) > 1 and isinstance(p[1], dict) else str(p) for p in similar_products]
                    logger.info(f"Found similar products via find_similar_products: {log_similar_products}")
                    product_suggestions = []
                    for product_entry in similar_products:
                        if isinstance(product_entry, tuple) and len(product_entry) == 2:
                            product_key_sugg, product_details_sugg = product_entry
                            if isinstance(product_details_sugg, dict):
                                product_suggestions.append({"display_text": product_details_sugg.get('original_display_name', product_key_sugg), "payload": product_key_sugg})
                            else: logger.warning(f"Skipping similar product '{product_key_sugg}' due to unexpected details format: {type(product_details_sugg)}")
                        else: logger.warning(f"Skipping similar product entry due to unexpected format: {type(product_entry)}")
                    if product_suggestions:
                        final_response_obj = {"message": "我没有完全找到您说的产品，不过找到了这些相似的，您看看是哪个？", "product_suggestions": product_suggestions}
                        intent_handled = True
                        new_general_context_key = None
                        new_general_context_details = None
                        new_bot_mention_for_next_turn = None
            
            if not intent_handled:
                logger.info("No specific intent handled by rules or fuzzy search, falling back to LLM.")
                llm_response_text, llm_mentioned_product = self.handle_llm_fallback(user_input_original, user_input_processed, user_id)
                final_response_obj = llm_response_text
                
                new_general_context_key = None # LLM fallback usually clears general product context
                new_general_context_details = None
                # 如果LLM提及了产品，则将其设置为下一轮的机器人提及产品
                new_bot_mention_for_next_turn = llm_mentioned_product
                intent_handled = True

        # Consolidated session update
        if new_general_context_key and not new_general_context_details: # Ensure details are fetched if only key is new
            new_general_context_details = self.product_manager.product_catalog.get(new_general_context_key)

        self.update_user_session(user_id,
                                 query=user_input_original, # Update query for this turn
                                 product_key=new_general_context_key,
                                 product_details=new_general_context_details,
                                 context_updates=context_updates_for_session if context_updates_for_session else None,
                                 bot_mentioned_product_payload_update=new_bot_mention_for_next_turn)
        
        self.last_identified_product_key = new_general_context_key # For app.py global fallback

        logger.info(f"Final response object for user {user_id}: {final_response_obj}")
        
        if final_response_obj is None:
            return "抱歉，我暂时无法理解您的意思，请换个说法试试？"
        return final_response_obj