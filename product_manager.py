import re
import csv
import random
import logging
import os
import config
from cache_manager import CacheManager, cached

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
                       Description (optional), IsSeasonal (optional, true/false/1/0/yes/no).
        
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
        expected_headers = ['ProductName', 'Specification', 'Price', 'Unit', 'Category', 'Description', 'IsSeasonal', 'Keywords']
        
        try:
            with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile: 
                reader = csv.DictReader(csvfile)
                logger.debug(f"CSV Headers read by DictReader: {reader.fieldnames}")
                
                # 检查是否有必要的列
                has_description = 'Description' in (reader.fieldnames or [])
                has_seasonal = 'IsSeasonal' in (reader.fieldnames or [])
                has_keywords = 'Keywords' in (reader.fieldnames or [])
                
                if not reader.fieldnames or not all(col in reader.fieldnames for col in ['ProductName', 'Specification', 'Price', 'Unit', 'Category']):
                    logger.error(f"CSV文件 {file_path} 的基本列标题不正确。必须包含: ProductName, Specification, Price, Unit, Category")
                    return False
                
                for row_num, row in enumerate(reader, 1): 
                    try:
                        product_name = row['ProductName'].strip()
                        specification = row['Specification'].strip()
                        price_str = row['Price'].strip()
                        unit = row['Unit'].strip()
                        category = row['Category'].strip()
                        # 读取可选列
                        description = row.get('Description', '').strip() if has_description else ""
                        is_seasonal = row.get('IsSeasonal', '').strip().lower() in ['true', 'yes', '1', 'y'] if has_seasonal else False
                        if not is_seasonal:
                            cat_lower = category.lower()
                            if '时令' in cat_lower or '当季' in cat_lower or 'seasonal' in cat_lower:
                                is_seasonal = True
                        keywords_text = row.get('Keywords', '').strip() if has_keywords else ""
                        keywords = [k.lower() for k in re.split(r'[;,\s]+', keywords_text) if k.strip()]

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
                            'popularity': 0
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
        
        # 1. 尝试直接匹配产品名或catalog_key
        for key, details in self.product_catalog.items():
            if query_lower == key or query_lower == details['name'].lower() or \
               query_lower in key or query_lower in details['name'].lower() or \
               key in query_lower or details['name'].lower() in query_lower:
                direct_matches.append((key, 1.0))  # 完全或高度相关匹配，相似度为1

        if direct_matches:
            direct_matches.sort(key=lambda x: len(x[0]), reverse=True)
            return direct_matches

        # 2. 尝试关键词部分匹配 (Jaccard相似度)
        query_words = set(self._tokenize(query_lower))
        if not query_words:
            return []

        for key, details in self.product_catalog.items():
            product_name_words = set(self._tokenize(details['name'].lower()))
            product_key_words = set(self._tokenize(key))
            keywords_words = set()
            for kw in details.get('keywords', []):
                keywords_words.update(self._tokenize(kw))

            # 名称和key的Jaccard相似度
            intersection_name = query_words.intersection(product_name_words)
            union_name = query_words.union(product_name_words)
            similarity_name = len(intersection_name) / len(union_name) if union_name else 0

            intersection_key = query_words.intersection(product_key_words)
            union_key = query_words.union(product_key_words)
            similarity_key = len(intersection_key) / len(union_key) if union_key else 0

            # 关键词Jaccard相似度
            intersection_kw = query_words.intersection(keywords_words)
            union_kw = query_words.union(keywords_words)
            similarity_kw = len(intersection_kw) / len(union_kw) if union_kw else 0

            # 取较高的相似度
            similarity = max(similarity_name, similarity_key, similarity_kw)

            if similarity >= threshold:
                partial_matches.append((key, similarity))

        # 按相似度排序
        partial_matches.sort(key=lambda x: x[1], reverse=True)
        return partial_matches
    
    def find_related_category(self, query_text):
        """根据用户查询文本尝试推断相关的产品类别
        
        Args:
            query_text (str): 用户输入的查询文本
            
        Returns:
            str or None: 推断出的类别名称，如果无法确定则返回None
        """
        query_lower = query_text.lower()

        # 检查关键词是否在查询中
        for keyword in config.FRUIT_KEYWORDS:
            if keyword in query_lower:
                logger.debug(f"通过水果关键词识别到产品类别: 水果 (关键词: {keyword})")
                return "水果"

        for keyword in config.VEGETABLE_KEYWORDS:
            if keyword in query_lower:
                logger.debug(f"通过蔬菜关键词识别到产品类别: 蔬菜 (关键词: {keyword})")
                return "蔬菜"

        # 1. 直接在查询中查找类别名称
        for category_name in self.product_categories.keys():
            if category_name.lower() in query_lower:
                return category_name

        # 2. 检查类别关键词
        category_scores = {}
        for cat, keywords_list in config.CATEGORY_KEYWORD_MAP.items():
            score = 0
            for keyword in keywords_list:
                if keyword in query_lower:
                    score += 1
            if score > 0:
                category_scores[cat] = score

        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        # 3. 基于通用词汇进行猜测
        if any(word in query_lower for word in ["吃", "食", "鲜", "甜", "新鲜", "水果"]):
            return "水果"
        if any(word in query_lower for word in ["菜", "素", "绿色", "蔬菜"]):
            return "蔬菜"

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
