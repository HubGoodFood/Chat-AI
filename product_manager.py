import re
import csv
import random
import logging
import os
import config
from cache_manager import CacheManager, cached
from pypinyin import pinyin, Style
import Levenshtein # 新增导入

# 配置日志
logger = logging.getLogger(__name__)

class ProductManager:
    """产品管理类，处理产品数据加载、搜索、推荐等功能"""
    
    def __init__(self, cache_manager=None):
        """初始化产品管理器
        
        Args:
            cache_manager (CacheManager, optional): 缓存管理器实例
        """
        # 产品数据存储
        self.product_catalog = {}
        self.product_categories = {} 
        self.all_product_keywords = []
        self.seasonal_products = []
        self.popular_products = {}
        
        # 缓存管理器
        self.cache_manager = cache_manager or CacheManager()
    
    def load_product_data(self, file_path=config.PRODUCT_DATA_FILE):
        """从CSV文件加载产品数据
        
        CSV文件应包含列: ProductName, Specification, Price, Unit, Category,
                       Description (optional), IsSeasonal (optional, true/false/1/0/yes/no),
                       Keywords (optional), Taste (optional), Origin (optional),
                       Benefits (optional), SuitableFor (optional).
        
        Args:
            file_path (str, optional): 产品数据CSV文件的路径
            
        Returns:
            bool: 加载是否成功
        """
        # 如果提供相对路径，解析为相对于当前文件的路径
        if not os.path.isabs(file_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, file_path)
        # 尝试从缓存加载
        cached_data = self.cache_manager.get_cached_product_data()
        if cached_data:
            self.product_catalog, self.product_categories, self.seasonal_products = cached_data
            self.all_product_keywords = self._extract_all_keywords()
            logger.info(f"从缓存加载产品数据完成，共 {len(self.product_catalog)} 条产品规格")
            return True
            
        # 缓存未命中，从文件加载
        logger.info(f"尝试从文件加载产品数据: {file_path}")
        
        self.product_catalog = {} 
        self.product_categories = {} 
        self.all_product_keywords = []
        self.seasonal_products = []
        expected_headers = ['ProductName', 'Specification', 'Price', 'Unit', 'Category', 'Description', 'IsSeasonal', 'Keywords', 'Taste', 'Origin', 'Benefits', 'SuitableFor'] # 保持与文档一致
        
        try:
            with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                logger.debug(f"CSV Headers read by DictReader: {reader.fieldnames}")
                
                # 检查是否有必要的列
                fieldnames_lower = [fn.lower() for fn in (reader.fieldnames or [])]
                has_description = 'description' in fieldnames_lower
                has_seasonal = 'isseasonal' in fieldnames_lower
                has_keywords = 'keywords' in fieldnames_lower
                has_taste = 'taste' in fieldnames_lower
                has_origin = 'origin' in fieldnames_lower
                has_benefits = 'benefits' in fieldnames_lower
                has_suitablefor = 'suitablefor' in fieldnames_lower
                
                # Ensure basic columns are present, checking against lowercased fieldnames for robustness
                required_cols_lower = ['productname', 'specification', 'price', 'unit', 'category']
                if not reader.fieldnames or not all(col_req.lower() in fieldnames_lower for col_req in required_cols_lower):
                    logger.error(f"CSV文件 {file_path} 的基本列标题不正确。必须包含: ProductName, Specification, Price, Unit, Category (大小写不敏感)")
                    return False
                
                for row_num, row in enumerate(reader, 1): 
                    try:
                        product_name = row['ProductName'].strip()
                        specification = row['Specification'].strip()
                        price_str = row['Price'].strip()
                        unit = row['Unit'].strip()
                        category = row['Category'].strip()
                        # 读取可选列
                        description = row.get('Description', row.get('description', '')).strip() if has_description else ""
                        is_seasonal_str = row.get('IsSeasonal', row.get('isseasonal', '')).strip().lower()
                        is_seasonal = is_seasonal_str in ['true', 'yes', '1', 'y'] if has_seasonal else False
                        keywords_text = row.get('Keywords', row.get('keywords', '')).strip() if has_keywords else ""
                        keywords = [k.lower() for k in re.split(r'[;,\s]+', keywords_text) if k.strip()]
                        
                        # 新增: 读取多维度标签
                        taste = row.get('Taste', row.get('taste', '')).strip() if has_taste else ""
                        origin = row.get('Origin', row.get('origin', '')).strip() if has_origin else ""
                        benefits = row.get('Benefits', row.get('benefits', '')).strip() if has_benefits else ""
                        suitablefor = row.get('SuitableFor', row.get('suitablefor', '')).strip() if has_suitablefor else ""

                        if not product_name or not price_str or not specification or not unit or not category:
                            logger.warning(f"CSV文件第 {row_num+1} 行数据不完整，已跳过: {row}")
                            continue
                        
                        price = float(price_str)
                        unique_product_key = product_name
                        if specification and specification.lower() != unit.lower() and specification not in product_name:
                            unique_product_key = f"{product_name} ({specification})"
                        
                        self.product_catalog[unique_product_key.lower()] = {
                            'name': product_name,
                            'specification': specification,
                            'price': price,
                            'unit': unit,
                            'category': category,
                            'original_display_name': unique_product_key,
                            'description': description,
                            'is_seasonal': is_seasonal,
                            'keywords': keywords,
                            'popularity': 0,
                            # 新增: 存储多维度标签
                            'taste': taste,
                            'origin': origin,
                            'benefits': benefits,
                            'suitablefor': suitablefor
                        }
                        
                        # 记录季节性产品
                        if is_seasonal:
                            self.seasonal_products.append(unique_product_key.lower())
                            
                        # 构建类别索引
                        if category not in self.product_categories:
                            self.product_categories[category] = []
                        self.product_categories[category].append(unique_product_key.lower())
                        
                    except ValueError as ve:
                        logger.warning(f"CSV文件第 {row_num+1} 行价格格式错误，已跳过: {row} - {ve}")
                    except KeyError as ke:
                        logger.warning(f"CSV文件第 {row_num+1} 行缺少必要的列，已跳过: {row} - {ke}")
                    except Exception as e:
                        logger.warning(f"处理CSV文件第 {row_num+1} 行时发生未知错误，已跳过: {row} - {e}")
        except FileNotFoundError:
            logger.error(f"产品文件 {file_path} 未找到。请确保它在应用根目录。")
            return False
        except Exception as e:
            logger.error(f"加载产品数据时发生严重错误: {e}")
            return False
        
        # 提取所有关键词
        self.all_product_keywords = self._extract_all_keywords()
        
        # 缓存产品数据
        self.cache_manager.cache_product_data(
            self.product_catalog,
            self.product_categories,
            self.seasonal_products
        )
        
        if not self.product_catalog:
            logger.warning("产品目录为空。请检查 products.csv 文件是否存在且包含有效数据和正确的列标题。")
            return False
        else:
            logger.info(f"产品目录加载完成，共 {len(self.product_catalog)} 条产品规格。")
            if self.seasonal_products:
                logger.info(f"当季推荐产品: {len(self.seasonal_products)} 条")
            return True

    def _tokenize(self, text):
        """Tokenize text into alphanumeric words and Chinese characters/bigrams"""
        text = text.lower()
        tokens = re.findall(r'[A-Za-z0-9]+', text)
        for seq in re.findall(r'[\u4e00-\u9fff]+', text):
            tokens.extend(list(seq))
            tokens.extend([seq[i:i+2] for i in range(len(seq)-1)])
        return tokens

    def _extract_all_keywords(self):
        """从产品目录中提取所有关键词
        
        Returns:
            list: 关键词列表
        """
        keywords = []
        for key, details in self.product_catalog.items():
            product_name = details['name'].lower()
            
            # 添加完整产品名
            if product_name not in keywords:
                keywords.append(product_name)
                
            # 添加单个词作为关键词
            for word in self._tokenize(product_name):
                if len(word) > 1 and word not in keywords:
                    keywords.append(word)

            # 添加自定义关键词
            for kw in details.get('keywords', []):
                for tok in self._tokenize(kw):
                    if tok and tok not in keywords:
                        keywords.append(tok)
                    
        return keywords

    def _get_pinyin_forms(self, text: str) -> Dict[str, str]:
        """为给定文本生成多种形式的拼音"""
        if not text:
            return {
                'full_tone': '',
                'full_flat': '',
                'initials': '',
                'full_flat_joined': ''
            }
        # 完整拼音，带声调，例如：[['nǐ'], ['hǎo']]
        pinyin_list_tone = pinyin(text, style=Style.TONE3, heteronym=False, errors='ignore')
        # 完整拼音，不带声调，例如：[['ni'], ['hao']]
        pinyin_list_flat = pinyin(text, style=Style.NORMAL, heteronym=False, errors='ignore')
        # 首字母，例如：[['n'], ['h']]
        pinyin_list_initials = pinyin(text, style=Style.INITIALS, strict=False, heteronym=False, errors='ignore')

        # 将拼音列表连接成字符串
        # full_tone: 'nǐhǎo' (实际pypinyin输出可能是 'ni3hao3' 或类似，取决于TONE3风格)
        # TONE3 对于 '你好' 输出是 'ni3 hao3' (带空格)，需要处理
        full_tone_str = "".join(["".join(p) for p in pinyin_list_tone if p])
        # full_flat: 'nihao'
        full_flat_str = "".join(["".join(p) for p in pinyin_list_flat if p])
        # initials: 'nh'
        initials_str = "".join(["".join(p) for p in pinyin_list_initials if p])
        
        return {
            'full_tone': full_tone_str.replace(" ", ""), # 移除潜在的空格
            'full_flat': full_flat_str.replace(" ", ""), # 移除潜在的空格
            'initials': initials_str.replace(" ", ""),   # 移除潜在的空格
            'full_flat_joined': full_flat_str.replace(" ", "") # 与 full_flat 相同，确保无空格
        }
    
    def update_product_popularity(self, product_key, increment=1):
        """更新商品热度
        
        Args:
            product_key (str): 产品键
            increment (int): 增加的热度值
        """
        if product_key and product_key in self.product_catalog:
            self.product_catalog[product_key]['popularity'] = self.product_catalog[product_key].get('popularity', 0) + increment
            self.popular_products[product_key] = self.popular_products.get(product_key, 0) + increment
    
    def get_products_by_category(self, category, limit=5):
        """获取特定类别的产品
        
        Args:
            category (str): 类别名称
            limit (int): 最大返回数量
            
        Returns:
            list: 元组 (product_key, product_details) 的列表
        """
        if not category:
            return []
        
        matching_products = []
        for key, details in self.product_catalog.items():
            if details['category'].lower() == category.lower():
                matching_products.append((key, details))
                
        # 按热度排序
        matching_products.sort(key=lambda x: x[1].get('popularity', 0), reverse=True)
        return matching_products[:limit]
    
    def get_popular_products(self, limit=3, category=None):
        """获取热门产品
        
        Args:
            limit (int): 最大返回数量
            category (str, optional): 如果指定，只返回该类别的产品
            
        Returns:
            list: 元组 (product_key, product_details) 的列表
        """
        products = []
        for key, details in self.product_catalog.items():
            # 如果指定了类别，只选择该类别
            if category and details['category'].lower() != category.lower():
                continue
            products.append((key, details))
            
        # 按热度排序
        products.sort(key=lambda x: x[1].get('popularity', 0), reverse=True)
        return products[:limit]
    
    def get_seasonal_products(self, limit=3, category=None):
        """获取季节性产品
        
        Args:
            limit (int): 最大返回数量
            category (str, optional): 如果指定，只返回该类别的产品
            
        Returns:
            list: 元组 (product_key, product_details) 的列表
        """
        # 如果用户指定了"时令水果"类别，返回该类别下所有产品
        if category and category == "时令水果":
            products = []
            for key in self.product_categories.get(category, []):
                if key in self.product_catalog:
                    products.append((key, self.product_catalog[key]))
            return products[:limit]

        products = []
        for key in self.seasonal_products:
            if key in self.product_catalog:
                details = self.product_catalog[key]
                # 如果指定了类别，只选择该类别
                if category and details['category'].lower() != category.lower():
                    continue
                products.append((key, details))
                
        # 如果季节性产品不足，补充热门产品
        if len(products) < limit:
            popular = self.get_popular_products(limit - len(products), category)
            # 确保不重复
            for key, details in popular:
                if key not in [p[0] for p in products]:
                    products.append((key, details))
                    
        return products[:limit]
    
    @cached(ttl_seconds=600)
    def fuzzy_match_product(self, query_text, threshold=config.FUZZY_MATCH_THRESHOLD):
        """使用直接匹配和Jaccard相似度进行产品名称的模糊匹配
        
        Args:
            query_text (str): 用户输入的查询文本
            threshold (float): Jaccard相似度的阈值
            
        Returns:
            list: 包含元组 (product_key, similarity_score) 的列表，按相似度降序排列
        """
        query_lower = query_text.lower()
        direct_matches = []
        partial_matches = []

        # 获取查询文本的拼音形式
        query_pinyin_forms = self._get_pinyin_forms(query_lower)
        query_pinyin_flat = query_pinyin_forms['full_flat']
        query_pinyin_initials = query_pinyin_forms['initials']

        # 0. 检查是否有完全匹配的产品名称
        for key, details in self.product_catalog.items():
            product_name_lower = details['name'].lower()
            if query_lower == product_name_lower or query_lower == key:
                return [(key, 1.0)]

        # 1. 尝试直接包含匹配 (产品名、关键词)
        for key, details in self.product_catalog.items():
            product_name_lower = details['name'].lower()
            # 查询是产品名的一部分，或产品名是查询的一部分
            if query_lower in product_name_lower or product_name_lower in query_lower:
                match_ratio = len(query_lower) / len(product_name_lower) if len(product_name_lower) > 0 else 0
                # 使用max(0.8, match_ratio)可能过高，调整为更依赖实际重叠比例，但给予一个基础分
                direct_matches.append((key, 0.7 + 0.2 * match_ratio)) # 基础0.7，根据重叠比例增加
            
            for keyword in details.get('keywords', []):
                if keyword.lower() in query_lower or query_lower in keyword.lower():
                    direct_matches.append((key, 0.72)) # 关键词直接包含匹配，给一个稍高的固定分
                    break
        
        # 如果有直接匹配结果，优先返回得分较高的
        if direct_matches:
            direct_matches.sort(key=lambda x: x[1], reverse=True)
            # 如果最高分已经很高（例如 > 0.85），可以考虑直接返回，减少后续计算
            if direct_matches[0][1] > 0.85:
                 return direct_matches[:3] # 返回前几个高分匹配

        # 2. 综合多种模糊匹配策略
        query_words = set(self._tokenize(query_lower))
        
        for key, details in self.product_catalog.items():
            # 避免重复计算已在direct_matches中的高分项
            if any(key == dm_key for dm_key, dm_score in direct_matches if dm_score > 0.8):
                continue

            product_name_lower = details['name'].lower()
            product_pinyin_forms = details.get('pinyin_forms', self._get_pinyin_forms(product_name_lower)) # 兼容旧缓存
            
            # a. Jaccard 相似度 (名称和关键词)
            product_name_words = set(self._tokenize(product_name_lower))
            intersection_name = query_words.intersection(product_name_words)
            union_name = query_words.union(product_name_words)
            similarity_jaccard_name = len(intersection_name) / len(union_name) if union_name else 0
            
            similarity_jaccard_kw = 0
            keywords_words = set()
            for kw in details.get('keywords', []): keywords_words.update(self._tokenize(kw.lower()))
            if keywords_words:
                intersection_kw = query_words.intersection(keywords_words)
                union_kw = query_words.union(keywords_words)
                similarity_jaccard_kw = len(intersection_kw) / len(union_kw) if union_kw else 0

            # b. 字符级别 Jaccard 相似度
            chars_query = set(query_lower)
            chars_product = set(product_name_lower)
            intersection_chars = chars_query.intersection(chars_product)
            similarity_char_jaccard = len(intersection_chars) / max(1, len(chars_query.union(chars_product)))


            # c. Levenshtein 编辑距离相似度
            max_len = max(len(query_lower), len(product_name_lower))
            similarity_levenshtein = 0
            if max_len > 0:
                distance = Levenshtein.distance(query_lower, product_name_lower)
                similarity_levenshtein = 1 - (distance / max_len)
            
            # d. 拼音相似度
            similarity_pinyin = 0
            product_py_flat = product_pinyin_forms.get('full_flat', '')
            product_py_initials = product_pinyin_forms.get('initials', '')

            if query_pinyin_flat and product_py_flat:
                if query_pinyin_flat == product_py_flat:
                    similarity_pinyin = max(similarity_pinyin, 0.85) # 完全匹配全拼
                elif query_pinyin_flat in product_py_flat:
                    similarity_pinyin = max(similarity_pinyin, 0.65 + 0.1 * (len(query_pinyin_flat) / len(product_py_flat)))
                elif product_py_flat in query_pinyin_flat: # 查询拼音更长
                     similarity_pinyin = max(similarity_pinyin, 0.6 + 0.1 * (len(product_py_flat) / len(query_pinyin_flat)))


            if query_pinyin_initials and product_py_initials:
                if query_pinyin_initials == product_py_initials:
                    similarity_pinyin = max(similarity_pinyin, 0.7) # 完全匹配首字母
                elif query_pinyin_initials in product_py_initials and len(query_pinyin_initials) > 1 : # 避免单个字母匹配
                     similarity_pinyin = max(similarity_pinyin, 0.55 + 0.1 * (len(query_pinyin_initials) / len(product_py_initials)))


            # 综合得分策略 (示例：取最大值，可调整权重)
            # 字符Jaccard和Levenshtein对于中文错别字和顺序差异更敏感
            # Jaccard词级别对于语序不敏感的关键词匹配有优势
            # 拼音处理拼音输入
            current_max_similarity = 0
            scores = {
                "jaccard_name": similarity_jaccard_name * 0.9, # 基础分
                "jaccard_kw": similarity_jaccard_kw * 0.8,   # 关键词权重稍低
                "char_jaccard": similarity_char_jaccard * 1.1, # 字符匹配权重稍高
                "levenshtein": similarity_levenshtein * 1.2, # 编辑距离权重更高
                "pinyin": similarity_pinyin * 1.0
            }
            
            # 如果查询本身就是纯拼音（无汉字），提高拼音匹配的权重
            if query_lower == query_pinyin_flat or query_lower == query_pinyin_initials:
                scores["pinyin"] *= 1.3
            
            overall_similarity = max(scores.values())

            # 之前直接包含匹配的得分也加入比较
            for dm_key, dm_score in direct_matches:
                if dm_key == key:
                    overall_similarity = max(overall_similarity, dm_score)
                    break

            if overall_similarity >= threshold:
                # 避免重复添加，如果已在direct_matches中，则更新分数（如果更高）
                existing_match_index = -1
                for i, (dm_k, _) in enumerate(direct_matches):
                    if dm_k == key:
                        existing_match_index = i
                        break
                if existing_match_index != -1:
                    if overall_similarity > direct_matches[existing_match_index][1]:
                        direct_matches[existing_match_index] = (key, overall_similarity)
                else: # 否则作为新匹配添加
                     partial_matches.append((key, overall_similarity))

        # 合并 direct_matches 和 partial_matches，去重并排序
        final_matches_dict = {key: score for key, score in direct_matches}
        for key, score in partial_matches:
            if key not in final_matches_dict or score > final_matches_dict[key]:
                final_matches_dict[key] = score
        
        sorted_matches = sorted(final_matches_dict.items(), key=lambda item: item[1], reverse=True)
        return partial_matches
    
    def find_related_category(self, query_text):
        """根据用户查询文本尝试推断相关的产品类别
        
        Args:
            query_text (str): 用户输入的查询文本
            
        Returns:
            str or None: 推断出的类别名称，如果无法确定则返回None
        """
        if not query_text:
            return None
            
        query_lower = query_text.lower()
        
        # 0. 首先尝试直接匹配产品名，如果找到产品，直接返回其类别
        for key, details in self.product_catalog.items():
            product_name = details['name'].lower()
            if product_name in query_lower or query_lower in product_name:
                logger.debug(f"通过产品名匹配识别到类别: {details['category']} (产品: {product_name})")
                return details['category']

        # 1. 检查水果和蔬菜特定关键词
        for keyword in config.FRUIT_KEYWORDS:
            if keyword in query_lower:
                logger.debug(f"通过水果关键词识别到产品类别: 水果 (关键词: {keyword})")
                return "水果"

        for keyword in config.VEGETABLE_KEYWORDS:
            if keyword in query_lower:
                logger.debug(f"通过蔬菜关键词识别到产品类别: 蔬菜 (关键词: {keyword})")
                return "蔬菜"

        # 2. 直接在查询中查找类别名称
        for category_name in self.product_categories.keys():
            if category_name.lower() in query_lower:
                logger.debug(f"通过类别名直接匹配: {category_name}")
                return category_name

        # 3. 检查类别关键词映射
        category_scores = {}
        for cat, keywords_list in config.CATEGORY_KEYWORD_MAP.items():
            score = 0
            matched_keywords = []
            for keyword in keywords_list:
                if keyword in query_lower:
                    score += 1
                    matched_keywords.append(keyword)
            if score > 0:
                category_scores[cat] = {
                    'score': score,
                    'keywords': matched_keywords
                }

        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1]['score'])
            logger.debug(f"通过关键词映射识别类别: {best_category[0]} (匹配关键词: {', '.join(best_category[1]['keywords'])})")
            return best_category[0]

        # 4. 使用模糊匹配查找产品，然后返回其类别
        fuzzy_matches = self.fuzzy_match_product(query_lower, threshold=0.5)
        if fuzzy_matches:
            top_match_key = fuzzy_matches[0][0]
            category = self.product_catalog[top_match_key]['category']
            logger.debug(f"通过产品模糊匹配识别类别: {category} (匹配产品: {self.product_catalog[top_match_key]['name']})")
            return category

        # 5. 基于通用词汇进行猜测
        if any(word in query_lower for word in ["吃", "食", "鲜", "甜", "新鲜", "水果", "果"]):
            logger.debug(f"通过通用词汇猜测类别: 水果")
            return "水果"
        if any(word in query_lower for word in ["菜", "素", "绿色", "蔬菜", "青菜"]):
            logger.debug(f"通过通用词汇猜测类别: 蔬菜")
            return "蔬菜"

        # 6. 分析查询中的字符，检查与类别名称的重叠
        query_chars = set(query_lower)
        category_char_scores = {}
        for category_name in self.product_categories.keys():
            category_chars = set(category_name.lower())
            overlap = len(query_chars.intersection(category_chars))
            if overlap > 0:
                category_char_scores[category_name] = overlap
        
        if category_char_scores:
            best_category = max(category_char_scores.items(), key=lambda x: x[1])
            logger.debug(f"通过字符重叠分析识别类别: {best_category[0]} (重叠字符数: {best_category[1]})")
            return best_category[0]

        return None

    def format_product_display(self, product_details, tag=""):
        """格式化产品信息以便在聊天中友好显示
        
        Args:
            product_details (dict): 包含产品信息的字典
            tag (str, optional): 显示标签，如 "当季新鲜"、"热门推荐" 等
            
        Returns:
            str: 格式化后的产品信息字符串
        """
        if not product_details:
            return ""

        name = product_details.get('original_display_name', product_details.get('name', '未知产品'))
        price = product_details.get('price', 0)
        specification = product_details.get('specification', 'N/A')
        description = product_details.get('description', '')
        is_seasonal = product_details.get('is_seasonal', False)

        display_tag = f"【{tag}】" if tag else ""
        seasonal_marker = "【当季新鲜】" if is_seasonal and not tag else ""
        desc_text = f" - {description}" if description else ""

        return f"{display_tag}{seasonal_marker}{name}: ${price:.2f}/{specification}{desc_text}"

    def convert_chinese_number_to_int(self, text):
        """将常用中文数字转换为整数
        
        Args:
            text (str): 包含中文数字的文本
            
        Returns:
            int: 转换后的整数，如未找到匹配则默认为1
        """
        num_map = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
                  '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
        text = text.strip()

        # 直接匹配单个数字
        if text in num_map:
            return num_map[text]

        # 处理十到九十九
        match = re.fullmatch(r'([一二两三四五六七八九])?十([一二三四五六七八九])?', text)
        if match:
            tens_char, ones_char = match.groups()
            tens = num_map.get(tens_char, 1)
            ones = num_map.get(ones_char, 0)
            return tens * 10 + ones

        return 1
