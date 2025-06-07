"""
高级中文NLP引擎
集成预训练模型，提供深度语义理解能力
"""

import os
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Any
from functools import lru_cache
import threading
import time

logger = logging.getLogger(__name__)

class AdvancedNLPEngine:
    """高级NLP引擎，集成多种预训练模型"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", 
                 cache_size: int = 1000, lazy_load: bool = True):
        """初始化高级NLP引擎
        
        Args:
            model_name: 预训练模型名称
            cache_size: 向量缓存大小
            lazy_load: 是否懒加载模型
        """
        self.model_name = model_name
        self.cache_size = cache_size
        self.lazy_load = lazy_load
        
        # 模型组件
        self.sentence_model = None
        self.tokenizer = None
        self.model_loaded = False
        self.loading_lock = threading.Lock()
        
        # 缓存机制
        self.vector_cache = {}
        self.similarity_cache = {}
        
        # 性能统计
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'inference_count': 0,
            'total_inference_time': 0.0
        }
        
        if not lazy_load:
            self._load_models()
    
    def _load_models(self):
        """加载预训练模型"""
        if self.model_loaded:
            return
        
        with self.loading_lock:
            if self.model_loaded:  # 双重检查
                return
            
            try:
                logger.info(f"开始加载NLP模型: {self.model_name}")
                start_time = time.time()
                
                # 懒加载sentence-transformers
                from sentence_transformers import SentenceTransformer
                
                # 加载sentence transformer模型
                self.sentence_model = SentenceTransformer(self.model_name)
                
                # 可选：加载其他模型组件
                self._load_additional_models()
                
                load_time = time.time() - start_time
                logger.info(f"NLP模型加载完成，耗时: {load_time:.2f}秒")
                self.model_loaded = True
                
            except Exception as e:
                logger.error(f"加载NLP模型失败: {e}")
                # 回退到基础模型
                self._load_fallback_models()
    
    def _load_additional_models(self):
        """加载额外的模型组件"""
        try:
            # 可以在这里加载其他模型，如：
            # - 命名实体识别模型
            # - 情感分析模型
            # - 关键词提取模型
            pass
        except Exception as e:
            logger.warning(f"加载额外模型失败: {e}")
    
    def _load_fallback_models(self):
        """加载回退模型"""
        try:
            logger.info("尝试加载回退模型")
            # 使用更轻量级的模型作为回退
            from sentence_transformers import SentenceTransformer
            self.sentence_model = SentenceTransformer('distiluse-base-multilingual-cased')
            self.model_loaded = True
            logger.info("回退模型加载成功")
        except Exception as e:
            logger.error(f"回退模型加载也失败: {e}")
            self.model_loaded = False
    
    def _ensure_model_loaded(self):
        """确保模型已加载"""
        if not self.model_loaded:
            self._load_models()
    
    @lru_cache(maxsize=1000)
    def encode_text(self, text: str) -> np.ndarray:
        """将文本编码为向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本的向量表示
        """
        self._ensure_model_loaded()
        
        if not self.model_loaded:
            logger.warning("模型未加载，返回零向量")
            return np.zeros(384)  # 默认维度
        
        # 检查缓存
        cache_key = f"encode_{hash(text)}"
        if cache_key in self.vector_cache:
            self.stats['cache_hits'] += 1
            return self.vector_cache[cache_key]
        
        try:
            start_time = time.time()
            
            # 使用sentence transformer编码
            vector = self.sentence_model.encode(text, convert_to_tensor=False)
            
            # 更新统计
            self.stats['cache_misses'] += 1
            self.stats['inference_count'] += 1
            self.stats['total_inference_time'] += time.time() - start_time
            
            # 缓存结果
            if len(self.vector_cache) < self.cache_size:
                self.vector_cache[cache_key] = vector
            
            return vector
            
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            return np.zeros(384)
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的语义相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度分数 (0-1)
        """
        # 检查缓存
        cache_key = f"sim_{hash(text1)}_{hash(text2)}"
        if cache_key in self.similarity_cache:
            self.stats['cache_hits'] += 1
            return self.similarity_cache[cache_key]
        
        # 计算向量
        vec1 = self.encode_text(text1)
        vec2 = self.encode_text(text2)
        
        # 计算余弦相似度
        similarity = self._cosine_similarity(vec1, vec2)
        
        # 缓存结果
        if len(self.similarity_cache) < self.cache_size:
            self.similarity_cache[cache_key] = similarity
        
        return similarity
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, similarity))  # 确保在[0,1]范围内
            
        except Exception as e:
            logger.error(f"余弦相似度计算失败: {e}")
            return 0.0
    
    def find_most_similar(self, query: str, candidates: List[str], 
                         top_k: int = 5) -> List[Tuple[str, float]]:
        """找到最相似的候选文本
        
        Args:
            query: 查询文本
            candidates: 候选文本列表
            top_k: 返回前k个结果
            
        Returns:
            (文本, 相似度)的列表，按相似度降序排列
        """
        if not candidates:
            return []
        
        query_vector = self.encode_text(query)
        similarities = []
        
        for candidate in candidates:
            candidate_vector = self.encode_text(candidate)
            similarity = self._cosine_similarity(query_vector, candidate_vector)
            similarities.append((candidate, similarity))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词（基础实现）
        
        Args:
            text: 输入文本
            top_k: 返回前k个关键词
            
        Returns:
            关键词列表
        """
        # 这里可以集成更高级的关键词提取算法
        # 如TF-IDF、TextRank、YAKE等
        
        # 简单实现：基于词频
        import jieba
        words = jieba.lcut(text)
        
        # 过滤停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个'}
        words = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 统计词频
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:top_k]]
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """情感分析（基础实现）
        
        Args:
            text: 输入文本
            
        Returns:
            情感分析结果 {'positive': 0.x, 'negative': 0.x, 'neutral': 0.x}
        """
        # 简单的基于词典的情感分析
        positive_words = {'好', '棒', '赞', '不错', '喜欢', '满意', '新鲜', '甜', '香', '优质'}
        negative_words = {'不好', '差', '坏', '烂', '不新鲜', '贵', '不满意', '难吃', '苦', '酸'}
        
        words = set(text.lower())
        
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))
        total = pos_count + neg_count
        
        if total == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        pos_score = pos_count / total
        neg_score = neg_count / total
        neutral_score = max(0.0, 1.0 - pos_score - neg_score)
        
        return {
            'positive': pos_score,
            'negative': neg_score,
            'neutral': neutral_score
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = self.stats['cache_hits'] / total_requests if total_requests > 0 else 0
        avg_inference_time = (self.stats['total_inference_time'] / 
                            self.stats['inference_count'] if self.stats['inference_count'] > 0 else 0)
        
        return {
            'model_loaded': self.model_loaded,
            'model_name': self.model_name,
            'cache_hit_rate': cache_hit_rate,
            'total_requests': total_requests,
            'avg_inference_time_ms': avg_inference_time * 1000,
            'vector_cache_size': len(self.vector_cache),
            'similarity_cache_size': len(self.similarity_cache)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.vector_cache.clear()
        self.similarity_cache.clear()
        logger.info("NLP引擎缓存已清空")
    
    def __del__(self):
        """析构函数"""
        try:
            self.clear_cache()
        except:
            pass
