"""
个性化学习引擎
实现用户行为分析、偏好学习和自适应对话策略
"""

import time
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    preferences: Dict[str, float]  # 偏好权重
    behavior_patterns: Dict[str, Any]  # 行为模式
    interaction_style: str  # 交互风格
    purchase_history: List[Dict]  # 购买历史
    feedback_history: List[Dict]  # 反馈历史
    created_time: float
    last_updated: float

@dataclass
class InteractionRecord:
    """交互记录"""
    timestamp: float
    query: str
    intent: str
    response: str
    user_feedback: Optional[str] = None
    products_mentioned: List[str] = None
    satisfaction_score: Optional[float] = None

class PersonalizationEngine:
    """个性化学习引擎"""
    
    def __init__(self, nlp_engine=None, context_engine=None):
        """初始化个性化引擎
        
        Args:
            nlp_engine: NLP引擎实例
            context_engine: 上下文引擎实例
        """
        self.nlp_engine = nlp_engine
        self.context_engine = context_engine
        
        # 用户画像存储
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # 交互记录存储
        self.interaction_records: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 学习参数
        self.learning_rate = 0.1
        self.decay_factor = 0.95
        self.min_interactions = 5  # 最少交互次数才开始个性化
        
        # 偏好类别
        self.preference_categories = {
            'product_types': ['水果', '蔬菜', '肉类', '海鲜', '禽类'],
            'quality_factors': ['新鲜度', '价格', '口感', '营养', '外观'],
            'interaction_styles': ['详细', '简洁', '推荐', '比较'],
            'purchase_factors': ['价格敏感', '品质优先', '便利性', '新奇性']
        }
        
        # 行为模式识别
        self.behavior_patterns = {
            'query_frequency': 'high/medium/low',
            'decision_speed': 'fast/medium/slow',
            'price_sensitivity': 'high/medium/low',
            'exploration_tendency': 'high/medium/low',
            'feedback_frequency': 'high/medium/low'
        }
        
        logger.info("个性化学习引擎初始化完成")
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """获取用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._create_new_profile(user_id)
        return self.user_profiles[user_id]
    
    def _create_new_profile(self, user_id: str) -> UserProfile:
        """创建新的用户画像"""
        current_time = time.time()
        
        return UserProfile(
            user_id=user_id,
            preferences={
                # 产品类型偏好
                '水果': 0.5, '蔬菜': 0.5, '肉类': 0.5, '海鲜': 0.5,
                # 品质因素偏好
                '新鲜度': 0.8, '价格': 0.6, '口感': 0.7, '营养': 0.5,
                # 交互风格偏好
                '详细说明': 0.5, '简洁回复': 0.5, '主动推荐': 0.5
            },
            behavior_patterns={
                'query_frequency': 0.0,
                'decision_speed': 0.0,
                'price_sensitivity': 0.5,
                'exploration_tendency': 0.5,
                'avg_session_length': 0.0,
                'preferred_time_slots': []
            },
            interaction_style='neutral',
            purchase_history=[],
            feedback_history=[],
            created_time=current_time,
            last_updated=current_time
        )
    
    def record_interaction(self, user_id: str, query: str, intent: str, 
                          response: str, products_mentioned: List[str] = None,
                          user_feedback: str = None) -> None:
        """记录用户交互"""
        record = InteractionRecord(
            timestamp=time.time(),
            query=query,
            intent=intent,
            response=response,
            user_feedback=user_feedback,
            products_mentioned=products_mentioned or [],
            satisfaction_score=self._calculate_satisfaction_score(user_feedback)
        )
        
        self.interaction_records[user_id].append(record)
        
        # 触发学习更新
        self._update_user_learning(user_id, record)
    
    def _calculate_satisfaction_score(self, feedback: str) -> Optional[float]:
        """计算满意度分数"""
        if not feedback:
            return None
        
        feedback_lower = feedback.lower()
        
        # 正面反馈
        positive_indicators = ['好', '棒', '赞', '满意', '喜欢', '不错', '谢谢']
        # 负面反馈
        negative_indicators = ['不好', '差', '不满意', '不喜欢', '错误', '不对']
        
        positive_count = sum(1 for word in positive_indicators if word in feedback_lower)
        negative_count = sum(1 for word in negative_indicators if word in feedback_lower)
        
        if positive_count > negative_count:
            return 0.8 + min(0.2, positive_count * 0.1)
        elif negative_count > positive_count:
            return 0.2 - min(0.2, negative_count * 0.1)
        else:
            return 0.5
    
    def _update_user_learning(self, user_id: str, record: InteractionRecord) -> None:
        """更新用户学习"""
        profile = self.get_user_profile(user_id)
        records = self.interaction_records[user_id]
        
        # 只有足够的交互记录才开始学习
        if len(records) < self.min_interactions:
            return
        
        # 更新偏好
        self._update_preferences(profile, record, records)
        
        # 更新行为模式
        self._update_behavior_patterns(profile, records)
        
        # 更新交互风格
        self._update_interaction_style(profile, records)
        
        profile.last_updated = time.time()
        
        logger.debug(f"用户 {user_id} 的个性化模型已更新")
    
    def _update_preferences(self, profile: UserProfile, current_record: InteractionRecord, 
                          all_records: deque) -> None:
        """更新用户偏好"""
        # 基于产品提及更新产品类型偏好
        for product in current_record.products_mentioned:
            # 简单的产品分类
            category = self._classify_product(product)
            if category and category in profile.preferences:
                # 正反馈增加偏好，负反馈减少偏好
                if current_record.satisfaction_score:
                    if current_record.satisfaction_score > 0.6:
                        profile.preferences[category] = min(1.0, 
                            profile.preferences[category] + self.learning_rate * 0.1)
                    elif current_record.satisfaction_score < 0.4:
                        profile.preferences[category] = max(0.0,
                            profile.preferences[category] - self.learning_rate * 0.1)
        
        # 基于查询意图更新交互偏好
        intent_preferences = {
            'recommendation': '主动推荐',
            'price_query': '价格',
            'product_query': '详细说明'
        }
        
        if current_record.intent in intent_preferences:
            pref_key = intent_preferences[current_record.intent]
            if pref_key in profile.preferences:
                profile.preferences[pref_key] = min(1.0,
                    profile.preferences[pref_key] + self.learning_rate * 0.05)
    
    def _classify_product(self, product: str) -> Optional[str]:
        """产品分类"""
        product_categories = {
            '水果': ['苹果', '香蕉', '草莓', '橙子', '葡萄', '西瓜', '梨', '桃子'],
            '蔬菜': ['白菜', '萝卜', '土豆', '番茄', '黄瓜', '茄子', '豆角'],
            '肉类': ['猪肉', '牛肉', '羊肉', '鸡肉', '鸭肉'],
            '海鲜': ['鱼', '虾', '蟹', '贝类', '鱿鱼']
        }
        
        for category, products in product_categories.items():
            if any(p in product for p in products):
                return category
        
        return None
    
    def _update_behavior_patterns(self, profile: UserProfile, records: deque) -> None:
        """更新行为模式"""
        recent_records = list(records)[-20:]  # 最近20次交互
        
        if len(recent_records) < 5:
            return
        
        # 计算查询频率
        time_spans = []
        for i in range(1, len(recent_records)):
            time_span = recent_records[i].timestamp - recent_records[i-1].timestamp
            time_spans.append(time_span)
        
        if time_spans:
            avg_interval = np.mean(time_spans)
            # 转换为频率分数 (0-1)
            frequency_score = max(0, min(1, 1 - avg_interval / 3600))  # 1小时为基准
            profile.behavior_patterns['query_frequency'] = frequency_score
        
        # 计算价格敏感度
        price_queries = sum(1 for r in recent_records if 'price' in r.intent or '价格' in r.query)
        price_sensitivity = price_queries / len(recent_records)
        profile.behavior_patterns['price_sensitivity'] = price_sensitivity
        
        # 计算探索倾向
        unique_products = set()
        for record in recent_records:
            unique_products.update(record.products_mentioned)
        exploration_score = len(unique_products) / max(1, len(recent_records))
        profile.behavior_patterns['exploration_tendency'] = min(1.0, exploration_score)
    
    def _update_interaction_style(self, profile: UserProfile, records: deque) -> None:
        """更新交互风格"""
        recent_records = list(records)[-10:]
        
        # 分析查询长度偏好
        query_lengths = [len(r.query) for r in recent_records]
        avg_query_length = np.mean(query_lengths) if query_lengths else 0
        
        # 分析反馈模式
        feedback_count = sum(1 for r in recent_records if r.user_feedback)
        feedback_ratio = feedback_count / len(recent_records) if recent_records else 0
        
        # 确定交互风格
        if avg_query_length > 20 and feedback_ratio > 0.3:
            profile.interaction_style = 'detailed'  # 详细型
        elif avg_query_length < 10 and feedback_ratio < 0.2:
            profile.interaction_style = 'brief'     # 简洁型
        else:
            profile.interaction_style = 'balanced'  # 平衡型
    
    def get_personalized_recommendations(self, user_id: str, context: str,
                                       candidates: List[Dict]) -> List[Dict]:
        """获取个性化推荐"""
        profile = self.get_user_profile(user_id)
        
        if len(self.interaction_records[user_id]) < self.min_interactions:
            # 新用户，返回默认推荐
            return candidates[:3]
        
        # 基于用户偏好对候选项评分
        scored_candidates = []
        
        for candidate in candidates:
            score = self._calculate_personalized_score(profile, candidate, context)
            scored_candidates.append((candidate, score))
        
        # 按分数排序
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前N个推荐
        return [candidate for candidate, score in scored_candidates[:5]]
    
    def _calculate_personalized_score(self, profile: UserProfile, 
                                    candidate: Dict, context: str) -> float:
        """计算个性化分数"""
        base_score = candidate.get('base_score', 0.5)
        
        # 产品类型偏好
        category = candidate.get('category', '')
        category_preference = profile.preferences.get(category, 0.5)
        
        # 价格偏好
        price_factor = 1.0
        if 'price' in candidate:
            price_sensitivity = profile.behavior_patterns.get('price_sensitivity', 0.5)
            if price_sensitivity > 0.7:  # 价格敏感
                # 偏好低价产品
                price_factor = 1.0 - (candidate['price'] / 100.0)  # 假设价格范围0-100
            elif price_sensitivity < 0.3:  # 不敏感价格
                # 可能偏好高价优质产品
                price_factor = candidate['price'] / 100.0
        
        # 探索vs利用平衡
        exploration_tendency = profile.behavior_patterns.get('exploration_tendency', 0.5)
        novelty_factor = 1.0
        if exploration_tendency > 0.6:
            # 喜欢探索新产品
            novelty_factor = 1.0 + candidate.get('novelty_score', 0.0) * 0.2
        
        # 综合评分
        final_score = (
            base_score * 0.4 +
            category_preference * 0.3 +
            price_factor * 0.2 +
            novelty_factor * 0.1
        )
        
        return min(1.0, max(0.0, final_score))
    
    def get_adaptive_response_style(self, user_id: str) -> Dict[str, Any]:
        """获取自适应回复风格"""
        profile = self.get_user_profile(user_id)
        
        style_config = {
            'detailed': {
                'response_length': 'long',
                'include_details': True,
                'use_examples': True,
                'proactive_suggestions': True
            },
            'brief': {
                'response_length': 'short',
                'include_details': False,
                'use_examples': False,
                'proactive_suggestions': False
            },
            'balanced': {
                'response_length': 'medium',
                'include_details': True,
                'use_examples': False,
                'proactive_suggestions': True
            }
        }
        
        return style_config.get(profile.interaction_style, style_config['balanced'])
    
    def get_learning_stats(self, user_id: str) -> Dict[str, Any]:
        """获取学习统计信息"""
        if user_id not in self.user_profiles:
            return {'status': 'no_profile'}
        
        profile = self.user_profiles[user_id]
        records = self.interaction_records[user_id]
        
        # 计算学习进度
        learning_progress = min(1.0, len(records) / 50)  # 50次交互为完全学习
        
        # 计算满意度趋势
        recent_satisfaction = []
        for record in list(records)[-10:]:
            if record.satisfaction_score is not None:
                recent_satisfaction.append(record.satisfaction_score)
        
        avg_satisfaction = np.mean(recent_satisfaction) if recent_satisfaction else None
        
        return {
            'status': 'active',
            'total_interactions': len(records),
            'learning_progress': learning_progress,
            'interaction_style': profile.interaction_style,
            'top_preferences': sorted(profile.preferences.items(), 
                                    key=lambda x: x[1], reverse=True)[:5],
            'avg_satisfaction': avg_satisfaction,
            'last_updated': profile.last_updated
        }
