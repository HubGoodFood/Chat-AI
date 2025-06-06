import sys
import os
# Add the project root directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')) # Three levels up from src/app/products
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import re
import csv
import random
from typing import Dict, List, Tuple # 新增导入，用于类型提示
import logging
import os
from src.config import settings as config
from src.core.cache import CacheManager, cached
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
        # 移除路径修改逻辑，直接使用传入的 file_path，期望它是正确的路径
        # (例如，config.PRODUCT_DATA_FILE 应为 "data/products.csv")

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

    def get_all_product_names_and_keywords(self) -> List[str]:
        """获取所有产品名称和关键词的扁平列表。"""
        all_words = set()
        for key, details in self.product_catalog.items():
            # 添加产品名称（小写）
            all_words.add(details['name'].lower())
            # 添加原始显示名称（小写）
            if 'original_display_name' in details:
                all_words.add(details['original_display_name'].lower())
            # 添加关键词（已经是小写）
            for kw in details.get('keywords', []):
                all_words.add(kw)
        return list(all_words)

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
    
    # @cached(ttl_seconds=600) # 暂时注释掉缓存以进行调试
    def fuzzy_match_product(self, query_text: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """
        使用多种匹配算法进行模糊匹配，返回匹配度超过阈值的产品列表。
        
        Args:
            query_text: 用户查询文本
            threshold: 相似度阈值，低于此值的匹配将被过滤
            
        Returns:
            List[Tuple[str, float]]: 包含(product_key, similarity_score)的列表
        """
        if not query_text or not self.product_catalog:
            return []

        # --- 新增：常见问候语列表 ---
        COMMON_GREETINGS = {
            "你好", "您好", "hello", "hi", "你好呀", "你好吗", "在吗", "你好么",
            "早上好", "中午好", "下午好", "晚上好", "早安", "午安", "晚安"
        }
        # ---

        # --- 统一清理和规范化查询文本 ---
        # 移除标点符号，去除首尾空格，并转换为小写
        # 使用原始 query_text 进行日志记录，使用 normalized_query_text 进行匹配
        original_query_for_log = query_text
        normalized_query_text = re.sub(r'[^\w\s]', '', query_text).strip().lower()
        # ---

        if not normalized_query_text: # 如果清理后为空，也直接返回
            logger.debug(f"Query '{original_query_for_log}' normalized to empty string. Skipping product matching.")
            return []

        # --- 新增：检查是否为常见问候语 ---
        if normalized_query_text in COMMON_GREETINGS:
            logger.info(f"Query '{original_query_for_log}' (Normalized: '{normalized_query_text}') identified as a common greeting. Skipping product matching.")
            return []
        # ---
            
        # 权重配置，用于调整不同匹配算法的重要性
        weights = {
            'jaccard_name': 0.2,
            'jaccard_keywords': 0.1,
            'char_jaccard': 0.3,  # 增加字符匹配的权重
            'levenshtein': 0.3,   # 增加编辑距离的权重
            'pinyin': 0.1         # 降低拼音匹配的权重
        }
        
        # 特殊处理：如果查询是单个汉字，则优先考虑直接包含关系
        # 使用 normalized_query_text 的长度
        exact_match_bonus = 0.5 if len(normalized_query_text) == 1 else 0.3
        
        results = []
        # query_text_lower 现在是 normalized_query_text
        
        for product_key, product_details in self.product_catalog.items():
            product_name = product_details.get('name', '')
            product_original_name = product_details.get('original_display_name', product_name) # 用于日志
            product_name_lower = product_name.lower()
            
            # 计算各种相似度指标，使用 normalized_query_text 和 product_name_lower
            jaccard_name_score = self._jaccard_similarity(normalized_query_text, product_name_lower)
            
            # 关键词匹配
            product_keywords = product_details.get('keywords', [])
            # normalized_query_text.split() 可能需要进一步处理，例如过滤空字符串
            query_tokens = [token for token in normalized_query_text.split() if token]
            jaccard_kw_score = self._jaccard_similarity_lists(query_tokens, product_keywords)
            
            # 字符级别的Jaccard相似度
            char_jaccard_score = self._character_jaccard_similarity(normalized_query_text, product_name_lower)
            
            # Levenshtein编辑距离相似度
            levenshtein_score = self._levenshtein_similarity(normalized_query_text, product_name_lower)
            
            # 拼音相似度
            pinyin_score = self._pinyin_similarity(normalized_query_text, product_name_lower)
            
            # 调试输出
            # 使用 original_query_for_log 和 product_original_name 进行日志记录，以反映原始输入
            if "芭乐" in product_original_name and "芭乐" in original_query_for_log:
                logger.info(f"--- DETAILED DEBUG for '芭乐' MATCH ---")
                logger.info(f"  Query: '{original_query_for_log}' (Normalized: '{normalized_query_text}') vs Product: '{product_original_name}' (Key: '{product_key}')")
                logger.info(f"    Raw Jaccard Name: {jaccard_name_score:.4f}")
                logger.info(f"    Raw Jaccard KW: {jaccard_kw_score:.4f} (Keywords: {product_keywords})")
                logger.info(f"    Raw Char Jaccard: {char_jaccard_score:.4f}")
                logger.info(f"    Raw Levenshtein: {levenshtein_score:.4f}")
                logger.info(f"    Raw Pinyin: {pinyin_score:.4f}")
                logger.info(f"    Weighted Jaccard Name: {jaccard_name_score * weights['jaccard_name']:.4f}")
                logger.info(f"    Weighted Jaccard KW: {jaccard_kw_score * weights['jaccard_keywords']:.4f}")
                logger.info(f"    Weighted Char Jaccard: {char_jaccard_score * weights['char_jaccard']:.4f}")
                logger.info(f"    Weighted Levenshtein: {levenshtein_score * weights['levenshtein']:.4f}")
                logger.info(f"    Weighted Pinyin: {pinyin_score * weights['pinyin']:.4f}")
            else:
                logger.debug(f"--- Debug Scores for Product KEY: '{product_key}', NAME: '{product_original_name}' vs Query: '{original_query_for_log}' (Normalized: '{normalized_query_text}') ---")
                logger.debug(f"  Jaccard Name: {jaccard_name_score * weights['jaccard_name']:.4f} (Raw Score: {jaccard_name_score:.4f})")
                logger.debug(f"  Jaccard KW: {jaccard_kw_score * weights['jaccard_keywords']:.4f} (Raw Score: {jaccard_kw_score:.4f})")
                logger.debug(f"  Char Jaccard: {char_jaccard_score * weights['char_jaccard']:.4f} (Raw Score: {char_jaccard_score:.4f})")
                logger.debug(f"  Levenshtein: {levenshtein_score * weights['levenshtein']:.4f} (Raw Score: {levenshtein_score:.4f})")
                logger.debug(f"  Pinyin: {pinyin_score * weights['pinyin']:.4f} (Raw Score: {pinyin_score:.4f})")
            
            # 计算加权得分
            weighted_scores = [
                jaccard_name_score * weights['jaccard_name'],
                jaccard_kw_score * weights['jaccard_keywords'],
                char_jaccard_score * weights['char_jaccard'],
                levenshtein_score * weights['levenshtein'],
                pinyin_score * weights['pinyin']
            ]
            
            # 取最高分
            max_score = max(weighted_scores) if weighted_scores else 0.0 # Handle empty weighted_scores
            
            # 特殊处理：如果查询文本直接包含在产品名称中，给予额外加分
            exact_match_applied_log = ""
            if normalized_query_text and normalized_query_text in product_name_lower: # 使用 normalized_query_text
                max_score += exact_match_bonus
                max_score = min(max_score, 1.0)  # 确保分数不超过1
                exact_match_applied_log = f" (Exact match bonus {exact_match_bonus} applied, new score: {max_score:.4f})"
            
            if "芭乐" in product_original_name and "芭乐" in original_query_for_log:
                logger.info(f"    Max Score from components: {max_score:.4f}{exact_match_applied_log}")
                logger.info(f"    Final Overall Similarity for KEY: '{product_key}': {max_score:.4f} (Threshold: {threshold})")

            if max_score >= threshold:
                results.append((product_key, max_score))
            
            if not ("芭乐" in product_original_name and "芭乐" in original_query_for_log):
                logger.debug(f"  Max Score from components: {max_score:.4f}{exact_match_applied_log}")
                logger.debug(f"  Final Overall Similarity for KEY: '{product_key}': {max_score:.4f} (Threshold: {threshold})")
                
        # 按相似度降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 优先返回真正相关的产品（如查询"鸡"时返回含"鸡"的产品）
        if len(normalized_query_text) == 1: # 使用 normalized_query_text
            # 对于单字查询，将直接包含该字的产品排在前面
            # 确保比较时产品名称也是小写
            exact_matches = [(k, s) for k, s in results if normalized_query_text in self.product_catalog[k].get('name', '').lower()]
            other_matches = [(k, s) for k, s in results if normalized_query_text not in self.product_catalog[k].get('name', '').lower()]
            results = exact_matches + other_matches
        
        for key, score in results:
            logger.debug(f"找到匹配产品: {self.product_catalog[key].get('name', key)}, 得分: {score}")
            
        # 日志中使用原始查询文本
        logger.info(f"fuzzy_match_product: 为查询 '{original_query_for_log}' (Normalized: '{normalized_query_text}') 找到 {len(results)} 个相似产品")
        return results
    
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

    def find_similar_products(self, query_string: str, threshold: float = 0.3):
        """
        根据查询字符串查找相似的产品。
        利用 fuzzy_match_product 进行更稳健的匹配。

        Args:
            query_string (str): 用户的模糊查询字符串。
            threshold (float): 相似度阈值，默认降低到0.3以便捕获更多潜在匹配。

        Returns:
            list: 包含(product_key, product_details)元组的列表。
        """
        similar_products = []
        if not query_string or not self.product_catalog:
            logger.debug("find_similar_products: 空查询或空产品目录，返回空列表。")
            return similar_products

        logger.debug(f"find_similar_products: 查询='{query_string}', 阈值={threshold}")

        # 调用现有的更复杂的模糊匹配函数
        matched_products_with_scores = self.fuzzy_match_product(query_text=query_string, threshold=threshold)
        
        # 对匹配结果按相似度得分降序排序
        matched_products_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 转换为期望的返回格式
        for product_key, score in matched_products_with_scores:
            if product_key in self.product_catalog:
                similar_products.append((product_key, self.product_catalog[product_key]))
                logger.debug(f"找到匹配产品: {product_key}, 得分: {score}")

        logger.info(f"find_similar_products: 为查询 '{query_string}' 找到 {len(similar_products)} 个相似产品")
        return similar_products

    def get_product_categories(self):
        """
        获取所有产品分类。
        """
        return {
            "禽类": ["鸡", "鸭", "鹅", "鸽子", "母鸡", "公鸡", "童子鸡", "土鸡", "走地鸡", "松母鸡", "鸡肉", "鸭肉", "鹅肉"],
            "肉类": ["猪肉", "牛肉", "羊肉", "肉"],
            "海鲜": ["鱼", "虾", "蟹", "贝", "海鲜", "蝦餃"],
            "蔬菜": ["青菜", "西兰花", "菠菜", "茄子", "青江菜", "西兰花苔", "茭白", "嫩菠菜"],
            "水果": ["苹果", "香蕉", "橙子", "梨", "奇异果", "芭乐"],
            "点心": ["包子", "饺子", "馄饨", "笋饼", "糕点", "生煎包", "火燒", "水饺"],
            "其他": ["调味料", "饮品", "零食", "意大利面", "筋道", "泡椒", "姜"]
        }

    def categorize_product(self, product_name: str) -> str:
        """
        根据产品名称判断其所属分类。
        
        Args:
            product_name: 产品名称
            
        Returns:
            str: 产品分类名称
        """
        if not product_name:
            return "其他"
            
        categories = self.get_product_categories()
        product_name_lower = product_name.lower()
        
        # 特殊处理：如果产品名称是"鸡"，直接返回"禽类"
        if product_name == "鸡":
            logger.debug(f"产品 '{product_name}' 直接匹配到分类: 禽类")
            return "禽类"
        
        # 首先尝试精确匹配产品名称中的关键词
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in product_name_lower:
                    logger.debug(f"产品 '{product_name}' 通过关键词 '{keyword}' 匹配到分类: {category}")
                    return category
        
        # 如果是单字查询（如"鸡"），特殊处理
        if len(product_name) == 1:
            if product_name in "鸡鸭鹅":
                return "禽类"
            elif product_name in "猪牛羊肉":
                return "肉类"
            elif product_name in "鱼虾蟹":
                return "海鲜"
                    
        # 如果没有找到匹配的关键词，返回"其他"分类
        logger.debug(f"产品 '{product_name}' 未找到匹配分类，归入'其他'类别")
        return "其他"

    def _jaccard_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的Jaccard相似度"""
        set1 = set(str1)
        set2 = set(str2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    def _jaccard_similarity_lists(self, list1: List[str], list2: List[str]) -> float:
        """计算两个列表的Jaccard相似度"""
        set1 = set(list1)
        set2 = set(list2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    def _character_jaccard_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的字符级Jaccard相似度"""
        chars1 = set(str1)
        chars2 = set(str2)
        intersection = len(chars1.intersection(chars2))
        union = len(chars1.union(chars2))
        return intersection / union if union > 0 else 0

    def _levenshtein_similarity(self, str1: str, str2: str) -> float:
        """
        使用 Levenshtein 库计算两个字符串的相似度。
        返回一个 0 到 1 之间的浮点数，1 表示完全相同。
        """
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            # 如果其中一个为空，则相似度为0，除非另一个也为空（已处理）
            return 0.0
        return Levenshtein.ratio(str1, str2)

    def _pinyin_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的拼音相似度"""
        try:
            from pypinyin import lazy_pinyin
            # 转换为拼音
            pinyin1 = ' '.join(lazy_pinyin(str1))
            pinyin2 = ' '.join(lazy_pinyin(str2))
            
            # 计算拼音的Levenshtein相似度
            return self._levenshtein_similarity(pinyin1, pinyin2)
        except ImportError:
            logger.warning("pypinyin module not found, pinyin similarity calculation skipped")
            return 0.0