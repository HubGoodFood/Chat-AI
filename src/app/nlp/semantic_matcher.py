"""
语义匹配器
提供增强的语义相似度计算和匹配功能
"""

import re
import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class SemanticMatcher:
    """语义匹配器"""
    
    def __init__(self, chinese_processor=None):
        """初始化语义匹配器"""
        self.chinese_processor = chinese_processor
        self.word_weights = self._init_word_weights()
        self.semantic_templates = self._init_semantic_templates()
        
    def _init_word_weights(self) -> Dict[str, float]:
        """初始化词汇权重"""
        return {
            # 高权重词汇（核心意图词）
            '推荐': 3.0, '介绍': 3.0, '建议': 3.0,
            '什么': 2.5, '哪个': 2.5, '哪些': 2.5, '哪种': 2.5,
            '最': 2.0, '比较': 2.0, '更': 2.0, '特别': 2.0,
            '好吃': 2.0, '好': 1.8, '棒': 1.8, '值得': 2.0,
            '新鲜': 2.0, '甜': 1.5, '香': 1.5, '脆': 1.5,
            
            # 中权重词汇（类别词）
            '水果': 1.5, '蔬菜': 1.5, '肉类': 1.5, '海鲜': 1.5,
            '时令': 1.3, '当季': 1.3, '有机': 1.3,
            
            # 低权重词汇（功能词）
            '有': 0.8, '卖': 0.8, '买': 0.8,
            '多少钱': 1.2, '价格': 1.2, '价钱': 1.2,
            
            # 极低权重词汇（停用词）
            '的': 0.1, '了': 0.1, '在': 0.1, '是': 0.1,
            '我': 0.2, '你': 0.2, '他': 0.2
        }
    
    def _init_semantic_templates(self) -> Dict[str, List[Dict]]:
        """初始化语义模板"""
        return {
            'recommendation': [
                {
                    'pattern': r'(?P<question>什么|哪个|哪些|哪种).*(?P<category>水果|蔬菜|肉类|海鲜).*(?P<quality>最|比较|更)?(?P<adjective>好吃|好|棒|值得|新鲜)',
                    'weight': 0.95,
                    'description': '疑问词+类别+修饰词+形容词'
                },
                {
                    'pattern': r'(?P<adjective>好吃|好|棒|值得|新鲜).*(?P<question>什么|哪个|哪些|哪种)',
                    'weight': 0.9,
                    'description': '形容词+疑问词'
                },
                {
                    'pattern': r'有.*(?P<quality>最|比较|更|特别|很|非常)?(?P<adjective>好吃|好|棒|值得|新鲜).*(?P<category>水果|蔬菜|肉类|海鲜)',
                    'weight': 0.85,
                    'description': '有+修饰词+形容词+类别'
                },
                {
                    'pattern': r'(?P<action>推荐|介绍|建议).*(?P<category>水果|蔬菜|肉类|海鲜|产品)',
                    'weight': 0.9,
                    'description': '推荐动词+类别'
                }
            ],
            
            'availability': [
                {
                    'pattern': r'(?P<negation>卖不卖|有没有|有吗|卖不|有不|没有)(?P<product>.*)',
                    'weight': 0.95,
                    'description': '否定疑问+产品'
                },
                {
                    'pattern': r'(?P<product>.*)(?P<negation>卖不卖|有没有|有吗|卖不|有不)',
                    'weight': 0.9,
                    'description': '产品+否定疑问'
                }
            ],
            
            'price': [
                {
                    'pattern': r'(?P<product>.*)(?P<price_word>多少钱|什么价格|价钱|怎么卖|费用)',
                    'weight': 0.95,
                    'description': '产品+价格词'
                },
                {
                    'pattern': r'(?P<price_word>多少钱|什么价格|价钱|怎么卖|费用)(?P<product>.*)',
                    'weight': 0.9,
                    'description': '价格词+产品'
                }
            ]
        }
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 1. 基于关键词的相似度
        keyword_sim = self._calculate_keyword_similarity(text1, text2)
        
        # 2. 基于语义模板的相似度
        template_sim = self._calculate_template_similarity(text1, text2)
        
        # 3. 基于字符级别的相似度
        char_sim = self._calculate_character_similarity(text1, text2)
        
        # 4. 基于词序的相似度
        order_sim = self._calculate_order_similarity(text1, text2)
        
        # 加权组合
        final_similarity = (
            keyword_sim * 0.4 +
            template_sim * 0.3 +
            char_sim * 0.2 +
            order_sim * 0.1
        )
        
        return min(final_similarity, 1.0)
    
    def match_intent_template(self, text: str) -> Dict[str, Any]:
        """匹配意图模板"""
        results = {}
        
        for intent, templates in self.semantic_templates.items():
            best_match = None
            best_score = 0.0
            
            for template in templates:
                pattern = re.compile(template['pattern'], re.IGNORECASE)
                match = pattern.search(text)
                
                if match:
                    score = template['weight']
                    # 根据匹配的完整性调整分数
                    matched_groups = len([g for g in match.groups() if g])
                    total_groups = len(pattern.groupindex)
                    completeness = matched_groups / max(total_groups, 1)
                    adjusted_score = score * (0.7 + 0.3 * completeness)
                    
                    if adjusted_score > best_score:
                        best_score = adjusted_score
                        best_match = {
                            'template': template,
                            'match': match,
                            'groups': match.groupdict(),
                            'score': adjusted_score
                        }
            
            if best_match:
                results[intent] = best_match
        
        return results
    
    def extract_semantic_features(self, text: str) -> Dict[str, Any]:
        """提取语义特征"""
        features = {}
        
        # 1. 关键词特征
        if self.chinese_processor:
            keywords = self.chinese_processor.extract_keywords(text)
            features['keywords'] = keywords
            features['keyword_weights'] = [self.word_weights.get(kw, 1.0) for kw in keywords]
        
        # 2. 语义模板匹配
        template_matches = self.match_intent_template(text)
        features['template_matches'] = template_matches
        
        # 3. 语言特征
        features['question_words'] = self._extract_question_indicators(text)
        features['negation_words'] = self._extract_negation_indicators(text)
        features['quality_words'] = self._extract_quality_indicators(text)
        features['category_words'] = self._extract_category_indicators(text)
        
        # 4. 结构特征
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['has_question_mark'] = '？' in text or '?' in text
        
        return features
    
    def _calculate_keyword_similarity(self, text1: str, text2: str) -> float:
        """计算关键词相似度"""
        if not self.chinese_processor:
            return 0.0
        
        keywords1 = set(self.chinese_processor.extract_keywords(text1))
        keywords2 = set(self.chinese_processor.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # 计算加权Jaccard相似度
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        if not union:
            return 0.0
        
        # 计算权重
        intersection_weight = sum(self.word_weights.get(word, 1.0) for word in intersection)
        union_weight = sum(self.word_weights.get(word, 1.0) for word in union)
        
        return intersection_weight / union_weight if union_weight > 0 else 0.0
    
    def _calculate_template_similarity(self, text1: str, text2: str) -> float:
        """计算模板相似度"""
        matches1 = self.match_intent_template(text1)
        matches2 = self.match_intent_template(text2)
        
        if not matches1 or not matches2:
            return 0.0
        
        # 检查是否匹配相同的意图模板
        common_intents = set(matches1.keys()).intersection(set(matches2.keys()))
        
        if not common_intents:
            return 0.0
        
        # 计算最高的模板匹配分数
        max_similarity = 0.0
        for intent in common_intents:
            score1 = matches1[intent]['score']
            score2 = matches2[intent]['score']
            similarity = min(score1, score2)  # 取较低的分数
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_character_similarity(self, text1: str, text2: str) -> float:
        """计算字符级相似度"""
        chars1 = set(text1)
        chars2 = set(text2)
        
        if not chars1 or not chars2:
            return 0.0
        
        intersection = len(chars1.intersection(chars2))
        union = len(chars1.union(chars2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_order_similarity(self, text1: str, text2: str) -> float:
        """计算词序相似度"""
        if not self.chinese_processor:
            return 0.0
        
        words1 = self.chinese_processor.extract_keywords(text1)
        words2 = self.chinese_processor.extract_keywords(text2)
        
        if not words1 or not words2:
            return 0.0
        
        # 计算最长公共子序列
        lcs_length = self._longest_common_subsequence(words1, words2)
        max_length = max(len(words1), len(words2))
        
        return lcs_length / max_length if max_length > 0 else 0.0
    
    def _longest_common_subsequence(self, seq1: List[str], seq2: List[str]) -> int:
        """计算最长公共子序列长度"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _extract_question_indicators(self, text: str) -> List[str]:
        """提取疑问指示词"""
        indicators = ['什么', '哪个', '哪些', '哪种', '怎么', '为什么', '多少', '几', '如何']
        return [word for word in indicators if word in text]
    
    def _extract_negation_indicators(self, text: str) -> List[str]:
        """提取否定指示词"""
        indicators = ['不', '没', '无', '非', '卖不卖', '有没有', '有吗', '卖不', '有不']
        return [word for word in indicators if word in text]
    
    def _extract_quality_indicators(self, text: str) -> List[str]:
        """提取品质指示词"""
        indicators = ['好吃', '好', '棒', '值得', '新鲜', '甜', '香', '脆', '嫩', '最', '比较', '更', '特别']
        return [word for word in indicators if word in text]
    
    def _extract_category_indicators(self, text: str) -> List[str]:
        """提取类别指示词"""
        indicators = ['水果', '蔬菜', '肉类', '海鲜', '禽类', '蛋类', '干货', '调料', '时令', '当季', '有机']
        return [word for word in indicators if word in text]
