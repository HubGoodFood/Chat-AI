"""
中文语言处理器
提供增强的中文分词、语义分析和语序处理功能
"""

import re
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ChineseProcessor:
    """中文语言处理器"""
    
    def __init__(self):
        """初始化中文处理器"""
        self.initialized = False
        self._init_jieba()
        self._load_domain_words()
        self._init_semantic_patterns()
        self._init_synonyms()
        
    def _init_jieba(self):
        """初始化jieba分词器"""
        try:
            # 设置jieba为精确模式
            jieba.setLogLevel(logging.WARNING)
            logger.info("jieba分词器初始化完成")
        except Exception as e:
            logger.error(f"jieba初始化失败: {e}")
    
    def _load_domain_words(self):
        """加载领域特定词汇"""
        domain_words = [
            # 产品相关
            '时令水果', '新鲜蔬菜', '走地鸡', '农场直供', '有机蔬菜',
            '当季水果', '绿色蔬菜', '土鸡蛋', '新鲜水果', '优质蔬菜',
            
            # 政策相关
            '配送时间', '付款方式', '取货地点', '质量保证', '群规',
            '退款政策', '运费标准', '起送金额', '配送范围', '免费配送',
            
            # 查询相关
            '多少钱', '什么价格', '怎么卖', '价钱', '费用',
            '好不好', '新鲜吗', '质量', '口感', '味道'
        ]
        
        for word in domain_words:
            jieba.add_word(word, freq=1000)
            
        logger.info(f"加载了{len(domain_words)}个领域词汇")
    
    def _init_semantic_patterns(self):
        """初始化语义模式"""
        self.semantic_patterns = {
            'recommendation': [
                # 推荐意图的语义模式
                r'(?P<question>什么|哪个|哪些|哪种).*(?P<modifier>最|比较|更|特别|很|非常)?(?P<quality>好吃|好|棒|值得|新鲜|甜|香|脆|嫩)',
                r'(?P<quality>好吃|好|棒|值得|新鲜|甜|香|脆|嫩).*(?P<question>什么|哪个|哪些|哪种)',
                r'(?P<question>什么|哪个|哪些|哪种).*(?P<category>水果|蔬菜|肉类|海鲜).*(?P<modifier>最|比较|更)?(?P<quality>好|棒|值得|新鲜)',
                r'有.*(?P<modifier>最|比较|更|特别|很|非常)?(?P<quality>好吃|好|棒|值得|新鲜|甜|香|脆|嫩).*(?P<category>水果|蔬菜|肉类|海鲜)',
                r'推荐.*(?P<category>水果|蔬菜|肉类|海鲜|产品)',
                r'介绍.*(?P<quality>好|棒|值得|新鲜).*(?P<category>水果|蔬菜|肉类|海鲜)',
            ],
            
            'availability': [
                # 可用性查询的语义模式
                r'(?P<negation>卖不卖|有没有|有吗|卖不|有不|没有)(?P<product>.*)',
                r'(?P<product>.*)(?P<negation>卖不卖|有没有|有吗|卖不|有不)',
                r'(?P<question>你们|这里|店里)(?P<action>有|卖)(?P<product>.*)',
            ],
            
            'price': [
                # 价格查询的语义模式
                r'(?P<product>.*)(?P<price_word>多少钱|什么价格|价钱|怎么卖|费用)',
                r'(?P<price_word>多少钱|什么价格|价钱|怎么卖|费用)(?P<product>.*)',
                r'(?P<product>.*)(?P<price_word>贵不贵|便宜|实惠)',
            ]
        }
        
        # 编译正则表达式
        self.compiled_patterns = {}
        for intent, patterns in self.semantic_patterns.items():
            self.compiled_patterns[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _init_synonyms(self):
        """初始化同义词词典"""
        self.synonyms = {
            '好吃': ['美味', '好味', '香甜', '可口', '鲜美', '棒', '赞', '不错'],
            '新鲜': ['鲜', '新', '嫩', '脆', '水灵'],
            '推荐': ['介绍', '建议', '推荐一下', '说说', '讲讲'],
            '什么': ['哪个', '哪些', '哪种', '什么样的'],
            '水果': ['果子', '鲜果', '时令水果', '当季水果'],
            '蔬菜': ['青菜', '菜', '蔬', '绿色蔬菜', '新鲜蔬菜'],
            '多少钱': ['什么价格', '价钱', '怎么卖', '费用', '价位'],
            '有没有': ['卖不卖', '有吗', '卖不', '有不'],
        }
    
    def extract_keywords(self, text: str, with_pos: bool = False) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        # 预处理文本
        text = self._preprocess_text(text)
        
        if with_pos:
            # 带词性标注的分词
            words = pseg.cut(text)
            keywords = []
            for word, pos in words:
                if len(word) > 1 and pos in ['n', 'v', 'a', 'nr', 'ns', 'nt', 'nz']:
                    keywords.append(word)
            return keywords
        else:
            # 普通分词
            words = jieba.lcut(text)
            # 过滤停用词和短词
            stop_words = self._get_stop_words()
            keywords = [word for word in words if len(word) > 1 and word not in stop_words]
            return keywords
    
    def analyze_semantic_pattern(self, text: str) -> Dict[str, any]:
        """分析语义模式"""
        text = self._preprocess_text(text)
        results = {}
        
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    results[intent] = {
                        'matched': True,
                        'groups': match.groupdict(),
                        'confidence': 0.9  # 规则匹配的高置信度
                    }
                    break
        
        return results
    
    def expand_synonyms(self, text: str) -> List[str]:
        """扩展同义词"""
        expanded_texts = [text]
        
        for key, synonyms in self.synonyms.items():
            if key in text:
                for synonym in synonyms:
                    expanded_texts.append(text.replace(key, synonym))
        
        return list(set(expanded_texts))  # 去重
    
    def extract_intent_features(self, text: str) -> Dict[str, any]:
        """提取意图特征"""
        features = {
            'keywords': self.extract_keywords(text),
            'pos_keywords': self.extract_keywords(text, with_pos=True),
            'semantic_patterns': self.analyze_semantic_pattern(text),
            'question_words': self._extract_question_words(text),
            'modifiers': self._extract_modifiers(text),
            'categories': self._extract_categories(text),
            'sentiment': self._analyze_sentiment(text)
        }
        
        return features
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转小写
        text = text.lower()
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        # 标准化标点符号
        text = re.sub(r'[？?]', '？', text)
        text = re.sub(r'[！!]', '！', text)
        text = re.sub(r'[。.]', '。', text)
        
        return text
    
    def _get_stop_words(self) -> Set[str]:
        """获取停用词列表"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '就是', '还', '把', '比', '或者', '等', '可以', '这个'
        }
    
    def _extract_question_words(self, text: str) -> List[str]:
        """提取疑问词"""
        question_words = ['什么', '哪个', '哪些', '哪种', '怎么', '为什么', '多少', '几']
        return [word for word in question_words if word in text]
    
    def _extract_modifiers(self, text: str) -> List[str]:
        """提取修饰词"""
        modifiers = ['最', '比较', '更', '特别', '很', '非常', '超级', '极其', '相当']
        return [word for word in modifiers if word in text]
    
    def _extract_categories(self, text: str) -> List[str]:
        """提取类别词"""
        categories = ['水果', '蔬菜', '肉类', '海鲜', '禽类', '蛋类', '干货', '调料']
        return [word for word in categories if word in text]
    
    def _analyze_sentiment(self, text: str) -> str:
        """简单的情感分析"""
        positive_words = ['好', '棒', '赞', '不错', '喜欢', '满意', '新鲜', '甜', '香']
        negative_words = ['不好', '差', '坏', '烂', '不新鲜', '贵', '不满意']
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
