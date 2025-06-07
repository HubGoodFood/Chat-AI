# 搜索算法优化实现方案

## 1. 混合搜索引擎

### 1.1 核心搜索引擎架构

```python
#!/usr/bin/env python3
"""
混合搜索引擎：结合多种搜索算法，提供最佳搜索体验
"""

import re
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import jieba  # 中文分词
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果数据类"""
    content: str
    score: float
    match_type: str  # exact, keyword, tfidf, semantic
    source: str
    metadata: Dict[str, Any] = None

class HybridSearchEngine:
    """
    混合搜索引擎
    
    搜索策略优先级：
    1. 精确匹配（最快，最准确）
    2. 关键词匹配（快速，较准确）
    3. TF-IDF语义搜索（中等速度，语义理解）
    4. 深度语义搜索（较慢，最佳语义理解）
    """
    
    def __init__(self, documents: List[str], document_metadata: List[Dict] = None):
        self.documents = documents
        self.document_metadata = document_metadata or [{}] * len(documents)
        
        # 搜索配置
        self.config = {
            'exact_match_threshold': 0.95,
            'keyword_match_threshold': 0.7,
            'tfidf_threshold': 0.3,
            'semantic_threshold': 0.5,
            'max_results_per_method': 5
        }
        
        # 初始化组件
        self._init_keyword_index()
        self._init_tfidf_vectorizer()
        self._init_chinese_processing()
        
        # 性能统计
        self.search_stats = defaultdict(int)
        
    def _init_keyword_index(self):
        """初始化关键词索引"""
        self.keyword_index = defaultdict(list)
        
        for idx, doc in enumerate(self.documents):
            # 提取关键词
            keywords = self._extract_keywords(doc)
            for keyword in keywords:
                self.keyword_index[keyword].append(idx)
        
        logger.info(f"关键词索引构建完成，共 {len(self.keyword_index)} 个关键词")
    
    def _init_tfidf_vectorizer(self):
        """初始化TF-IDF向量化器"""
        # 优化的TF-IDF配置
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 3),
            min_df=1,  # 最小文档频率
            max_df=0.8,  # 最大文档频率
            sublinear_tf=True,  # 使用对数TF
            analyzer='char',  # 字符级分析，适合中文
            token_pattern=r'[\u4e00-\u9fff]+',  # 中文字符模式
            stop_words=self._get_chinese_stop_words()
        )
        
        try:
            # 预处理文档
            processed_docs = [self._preprocess_text(doc) for doc in self.documents]
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(processed_docs)
            logger.info(f"TF-IDF矩阵构建完成，形状: {self.tfidf_matrix.shape}")
        except Exception as e:
            logger.error(f"TF-IDF初始化失败: {e}")
            self.tfidf_matrix = None
    
    def _init_chinese_processing(self):
        """初始化中文处理组件"""
        # 加载jieba词典（如果有自定义词典）
        try:
            # 添加领域特定词汇
            domain_words = [
                '配送时间', '付款方式', '取货地点', '质量保证',
                '群规', '退款政策', '运费标准', '起送金额',
                '农场直供', '时令水果', '新鲜蔬菜', '走地鸡'
            ]
            
            for word in domain_words:
                jieba.add_word(word)
                
            logger.info("中文处理组件初始化完成")
        except Exception as e:
            logger.warning(f"中文处理组件初始化警告: {e}")
    
    def search(self, query: str, top_k: int = 5, search_methods: List[str] = None) -> List[SearchResult]:
        """
        执行混合搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            search_methods: 指定搜索方法，None表示使用所有方法
        
        Returns:
            搜索结果列表
        """
        start_time = time.time()
        
        if not query.strip():
            return []
        
        # 预处理查询
        processed_query = self._preprocess_text(query)
        
        # 默认搜索方法
        if search_methods is None:
            search_methods = ['exact', 'keyword', 'tfidf', 'semantic']
        
        all_results = []
        
        # 1. 精确匹配
        if 'exact' in search_methods:
            exact_results = self._exact_match_search(processed_query, query)
            all_results.extend(exact_results)
            self.search_stats['exact_searches'] += 1
            
            # 如果精确匹配找到足够结果，直接返回
            if len(exact_results) >= top_k:
                return self._rank_and_deduplicate(exact_results, top_k)
        
        # 2. 关键词匹配
        if 'keyword' in search_methods and len(all_results) < top_k:
            keyword_results = self._keyword_search(processed_query, query)
            all_results.extend(keyword_results)
            self.search_stats['keyword_searches'] += 1
        
        # 3. TF-IDF搜索
        if 'tfidf' in search_methods and len(all_results) < top_k:
            tfidf_results = self._tfidf_search(processed_query, query)
            all_results.extend(tfidf_results)
            self.search_stats['tfidf_searches'] += 1
        
        # 4. 语义搜索（如果可用）
        if 'semantic' in search_methods and len(all_results) < top_k:
            semantic_results = self._semantic_search(processed_query, query)
            all_results.extend(semantic_results)
            self.search_stats['semantic_searches'] += 1
        
        # 排序和去重
        final_results = self._rank_and_deduplicate(all_results, top_k)
        
        # 记录性能
        search_time = time.time() - start_time
        self.search_stats['total_searches'] += 1
        self.search_stats['total_search_time'] += search_time
        
        logger.debug(f"搜索完成: '{query}' -> {len(final_results)} 结果, 耗时: {search_time:.3f}s")
        
        return final_results
    
    def _exact_match_search(self, processed_query: str, original_query: str) -> List[SearchResult]:
        """精确匹配搜索"""
        results = []
        
        for idx, doc in enumerate(self.documents):
            processed_doc = self._preprocess_text(doc)
            
            # 检查完全匹配
            if processed_query in processed_doc:
                score = 1.0
                if processed_query == processed_doc:
                    score = 1.0  # 完全匹配
                else:
                    # 计算匹配度
                    score = len(processed_query) / len(processed_doc)
                    score = min(score, 0.95)  # 最高0.95
                
                results.append(SearchResult(
                    content=doc,
                    score=score,
                    match_type='exact',
                    source=f'doc_{idx}',
                    metadata=self.document_metadata[idx]
                ))
        
        return sorted(results, key=lambda x: x.score, reverse=True)
    
    def _keyword_search(self, processed_query: str, original_query: str) -> List[SearchResult]:
        """关键词匹配搜索"""
        results = []
        
        # 提取查询关键词
        query_keywords = self._extract_keywords(processed_query)
        
        # 计算文档匹配分数
        doc_scores = defaultdict(float)
        
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for doc_idx in self.keyword_index[keyword]:
                    # 计算关键词权重
                    keyword_weight = len(keyword) / len(processed_query)
                    doc_scores[doc_idx] += keyword_weight
        
        # 转换为SearchResult
        for doc_idx, score in doc_scores.items():
            if score >= self.config['keyword_match_threshold']:
                results.append(SearchResult(
                    content=self.documents[doc_idx],
                    score=min(score, 0.9),  # 关键词匹配最高0.9
                    match_type='keyword',
                    source=f'doc_{doc_idx}',
                    metadata=self.document_metadata[doc_idx]
                ))
        
        return sorted(results, key=lambda x: x.score, reverse=True)
    
    def _tfidf_search(self, processed_query: str, original_query: str) -> List[SearchResult]:
        """TF-IDF语义搜索"""
        if self.tfidf_matrix is None:
            return []
        
        try:
            # 将查询转换为TF-IDF向量
            query_vector = self.tfidf_vectorizer.transform([processed_query])
            
            # 计算余弦相似度
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # 获取相似度超过阈值的文档
            results = []
            for idx, similarity in enumerate(similarities):
                if similarity >= self.config['tfidf_threshold']:
                    results.append(SearchResult(
                        content=self.documents[idx],
                        score=min(similarity * 0.8, 0.8),  # TF-IDF最高0.8
                        match_type='tfidf',
                        source=f'doc_{idx}',
                        metadata=self.document_metadata[idx]
                    ))
            
            return sorted(results, key=lambda x: x.score, reverse=True)
            
        except Exception as e:
            logger.error(f"TF-IDF搜索失败: {e}")
            return []
    
    def _semantic_search(self, processed_query: str, original_query: str) -> List[SearchResult]:
        """深度语义搜索（可选，需要sentence-transformers）"""
        try:
            # 这里可以集成sentence-transformers或其他语义搜索模型
            # 暂时返回空结果，避免依赖重型模型
            logger.debug("语义搜索暂未实现，跳过")
            return []
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    def _rank_and_deduplicate(self, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """排序和去重"""
        if not results:
            return []
        
        # 去重（基于内容）
        seen_content = set()
        unique_results = []
        
        for result in results:
            content_hash = hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        # 返回前top_k个结果
        return unique_results[:top_k]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 使用jieba分词
        words = jieba.lcut(text)
        
        # 过滤停用词和短词
        stop_words = self._get_chinese_stop_words()
        keywords = [
            word.lower() for word in words 
            if len(word) > 1 and word.lower() not in stop_words
        ]
        
        return keywords
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转小写
        text = text.lower()
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 移除特殊字符（保留中文、英文、数字）
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)
        
        return text
    
    def _get_chinese_stop_words(self) -> set:
        """获取中文停用词"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', 
            '不', '人', '都', '一', '一个', '上', '也', '很',
            '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这', '那', '里', '后', '前',
            '时', '分', '可', '能', '还', '多', '个', '中',
            '来', '为', '什么', '怎么', '哪里', '什么时候'
        }
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        total_searches = self.search_stats['total_searches']
        
        if total_searches == 0:
            return {'message': '暂无搜索统计数据'}
        
        avg_search_time = self.search_stats['total_search_time'] / total_searches
        
        return {
            'total_searches': total_searches,
            'average_search_time_ms': avg_search_time * 1000,
            'exact_searches': self.search_stats['exact_searches'],
            'keyword_searches': self.search_stats['keyword_searches'],
            'tfidf_searches': self.search_stats['tfidf_searches'],
            'semantic_searches': self.search_stats['semantic_searches'],
            'search_method_distribution': {
                'exact': self.search_stats['exact_searches'] / total_searches,
                'keyword': self.search_stats['keyword_searches'] / total_searches,
                'tfidf': self.search_stats['tfidf_searches'] / total_searches,
                'semantic': self.search_stats['semantic_searches'] / total_searches,
            }
        }
    
    def update_documents(self, new_documents: List[str], new_metadata: List[Dict] = None):
        """更新文档集合"""
        self.documents = new_documents
        self.document_metadata = new_metadata or [{}] * len(new_documents)
        
        # 重新初始化索引
        self._init_keyword_index()
        self._init_tfidf_vectorizer()
        
        logger.info(f"文档集合已更新，共 {len(new_documents)} 个文档")
```

## 2. 相关性评分系统

### 2.1 智能评分算法

```python
class RelevanceScorer:
    """
    相关性评分系统
    
    综合考虑多个因素：
    - 匹配类型权重
    - 查询长度因子
    - 文档热度
    - 时间衰减
    - 用户反馈
    """
    
    def __init__(self):
        self.weights = {
            'exact_match': 1.0,
            'keyword_match': 0.8,
            'tfidf_similarity': 0.6,
            'semantic_similarity': 0.7,
            'query_length_factor': 0.1,
            'document_popularity': 0.15,
            'time_decay': 0.05,
            'user_feedback': 0.2
        }
        
        # 文档统计
        self.document_stats = defaultdict(lambda: {
            'view_count': 0,
            'positive_feedback': 0,
            'negative_feedback': 0,
            'last_accessed': time.time()
        })
    
    def calculate_relevance_score(self, 
                                search_result: SearchResult, 
                                query: str, 
                                user_context: Dict = None) -> float:
        """计算综合相关性评分"""
        
        base_score = search_result.score
        match_type = search_result.match_type
        
        # 1. 匹配类型权重
        type_weight = self.weights.get(f"{match_type}_match", 0.5)
        weighted_score = base_score * type_weight
        
        # 2. 查询长度因子
        length_factor = self._calculate_length_factor(query)
        
        # 3. 文档热度因子
        popularity_factor = self._calculate_popularity_factor(search_result.source)
        
        # 4. 时间衰减因子
        time_factor = self._calculate_time_factor(search_result.source)
        
        # 5. 用户反馈因子
        feedback_factor = self._calculate_feedback_factor(search_result.source)
        
        # 综合评分
        final_score = (
            weighted_score +
            length_factor * self.weights['query_length_factor'] +
            popularity_factor * self.weights['document_popularity'] +
            time_factor * self.weights['time_decay'] +
            feedback_factor * self.weights['user_feedback']
        )
        
        return min(final_score, 1.0)
    
    def _calculate_length_factor(self, query: str) -> float:
        """计算查询长度因子"""
        # 较长的查询通常更具体，应该给予更高权重
        query_length = len(query.strip())
        
        if query_length <= 2:
            return 0.5  # 短查询
        elif query_length <= 10:
            return 0.8  # 中等查询
        else:
            return 1.0  # 长查询
    
    def _calculate_popularity_factor(self, document_id: str) -> float:
        """计算文档热度因子"""
        stats = self.document_stats[document_id]
        view_count = stats['view_count']
        
        # 使用对数缩放避免热门文档过度占优
        if view_count == 0:
            return 0.0
        
        popularity = min(np.log(view_count + 1) / 10, 1.0)
        return popularity
    
    def _calculate_time_factor(self, document_id: str) -> float:
        """计算时间衰减因子"""
        stats = self.document_stats[document_id]
        last_accessed = stats['last_accessed']
        
        # 最近访问的文档给予更高权重
        time_diff = time.time() - last_accessed
        days_diff = time_diff / (24 * 3600)
        
        # 7天内的文档保持高权重
        if days_diff <= 7:
            return 1.0
        elif days_diff <= 30:
            return 0.8
        else:
            return 0.5
    
    def _calculate_feedback_factor(self, document_id: str) -> float:
        """计算用户反馈因子"""
        stats = self.document_stats[document_id]
        positive = stats['positive_feedback']
        negative = stats['negative_feedback']
        
        total_feedback = positive + negative
        if total_feedback == 0:
            return 0.0
        
        # 计算正面反馈比例
        positive_ratio = positive / total_feedback
        return positive_ratio
    
    def record_document_access(self, document_id: str):
        """记录文档访问"""
        self.document_stats[document_id]['view_count'] += 1
        self.document_stats[document_id]['last_accessed'] = time.time()
    
    def record_user_feedback(self, document_id: str, is_positive: bool):
        """记录用户反馈"""
        if is_positive:
            self.document_stats[document_id]['positive_feedback'] += 1
        else:
            self.document_stats[document_id]['negative_feedback'] += 1
```

这个混合搜索引擎将显著提升Chat-AI的搜索准确性和响应速度，特别是在处理中文查询时。通过多层搜索策略和智能评分系统，可以为用户提供更相关和有用的搜索结果。
