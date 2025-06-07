"""
增强的上下文管理器
提供智能的对话上下文管理和状态跟踪功能
"""

import time
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DialogueState(Enum):
    """对话状态枚举"""
    INITIAL = "initial"
    PRODUCT_INQUIRY = "product_inquiry"
    PRICE_INQUIRY = "price_inquiry"
    RECOMMENDATION = "recommendation"
    POLICY_INQUIRY = "policy_inquiry"
    AVAILABILITY_CHECK = "availability_check"
    CLARIFICATION = "clarification"
    COMPLETED = "completed"

@dataclass
class ContextItem:
    """上下文项"""
    content: str
    timestamp: float
    item_type: str  # 'query', 'response', 'product', 'intent'
    metadata: Dict[str, Any]
    relevance_score: float = 1.0

@dataclass
class UserPreference:
    """用户偏好"""
    categories: List[str]
    products: List[str]
    quality_preferences: List[str]  # 如：新鲜、甜、香等
    price_sensitivity: str  # 'low', 'medium', 'high'
    interaction_style: str  # 'formal', 'casual', 'brief'

class EnhancedContextManager:
    """增强的上下文管理器"""
    
    def __init__(self, max_context_items: int = 50, context_window_minutes: int = 30):
        """初始化上下文管理器"""
        self.max_context_items = max_context_items
        self.context_window_seconds = context_window_minutes * 60
        
        # 用户会话存储
        self.user_sessions: Dict[str, Dict] = {}
        
        # 上下文相关性权重
        self.relevance_weights = {
            'query': 1.0,
            'response': 0.8,
            'product': 1.2,
            'intent': 0.9,
            'preference': 1.1
        }
        
        # 时间衰减因子
        self.time_decay_factor = 0.1
        
        logger.info("增强上下文管理器初始化完成")
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """获取用户上下文"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = self._create_new_session()
        
        session = self.user_sessions[user_id]
        
        # 清理过期的上下文项
        self._cleanup_expired_context(session)
        
        return session
    
    def update_context(self, user_id: str, content: str, item_type: str, 
                      metadata: Optional[Dict] = None, intent: Optional[str] = None) -> None:
        """更新用户上下文"""
        session = self.get_user_context(user_id)
        
        # 创建上下文项
        context_item = ContextItem(
            content=content,
            timestamp=time.time(),
            item_type=item_type,
            metadata=metadata or {},
            relevance_score=self.relevance_weights.get(item_type, 1.0)
        )
        
        # 添加到上下文历史
        session['context_history'].append(context_item)
        
        # 更新当前状态
        if intent:
            self._update_dialogue_state(session, intent)
        
        # 更新最近的查询/响应
        if item_type == 'query':
            session['last_query'] = content
            session['last_query_time'] = time.time()
        elif item_type == 'product':
            session['last_product'] = metadata
            session['last_product_time'] = time.time()
        
        # 限制上下文历史长度
        if len(session['context_history']) > self.max_context_items:
            session['context_history'].pop(0)
        
        # 更新用户偏好
        self._update_user_preferences(session, content, item_type, metadata)
    
    def get_relevant_context(self, user_id: str, current_query: str, 
                           max_items: int = 10) -> List[ContextItem]:
        """获取相关的上下文项"""
        session = self.get_user_context(user_id)
        context_history = session['context_history']
        
        if not context_history:
            return []
        
        # 计算每个上下文项的相关性分数
        scored_items = []
        current_time = time.time()
        
        for item in context_history:
            # 时间衰减
            time_diff = current_time - item.timestamp
            time_factor = max(0, 1 - time_diff * self.time_decay_factor / self.context_window_seconds)
            
            # 内容相关性（简单的关键词匹配）
            content_similarity = self._calculate_content_similarity(current_query, item.content)
            
            # 类型权重
            type_weight = self.relevance_weights.get(item.item_type, 1.0)
            
            # 综合分数
            final_score = item.relevance_score * time_factor * content_similarity * type_weight
            
            scored_items.append((item, final_score))
        
        # 按分数排序并返回前N项
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items[:max_items] if score > 0.1]
    
    def get_dialogue_state(self, user_id: str) -> DialogueState:
        """获取对话状态"""
        session = self.get_user_context(user_id)
        return DialogueState(session.get('dialogue_state', DialogueState.INITIAL.value))
    
    def get_user_preferences(self, user_id: str) -> UserPreference:
        """获取用户偏好"""
        session = self.get_user_context(user_id)
        prefs_data = session.get('preferences', {})
        
        return UserPreference(
            categories=prefs_data.get('categories', []),
            products=prefs_data.get('products', []),
            quality_preferences=prefs_data.get('quality_preferences', []),
            price_sensitivity=prefs_data.get('price_sensitivity', 'medium'),
            interaction_style=prefs_data.get('interaction_style', 'casual')
        )
    
    def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """获取上下文摘要"""
        session = self.get_user_context(user_id)
        
        # 统计信息
        context_stats = defaultdict(int)
        for item in session['context_history']:
            context_stats[item.item_type] += 1
        
        # 最近的关键信息
        recent_products = []
        recent_intents = []

        # 获取最近的上下文项（处理deque切片问题）
        context_history = session['context_history']
        recent_items = list(context_history)[-10:] if len(context_history) > 10 else list(context_history)

        for item in reversed(recent_items):  # 最近10项
            if item.item_type == 'product' and item.metadata:
                recent_products.append(item.metadata.get('name', ''))
            elif item.item_type == 'intent':
                recent_intents.append(item.content)
        
        return {
            'dialogue_state': session.get('dialogue_state'),
            'context_count': len(session['context_history']),
            'context_stats': dict(context_stats),
            'recent_products': list(set(recent_products))[:5],
            'recent_intents': list(set(recent_intents))[:3],
            'last_query': session.get('last_query'),
            'last_query_time': session.get('last_query_time'),
            'session_duration': time.time() - session.get('session_start_time', time.time())
        }
    
    def clear_user_context(self, user_id: str) -> None:
        """清除用户上下文"""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"已清除用户 {user_id} 的上下文")
    
    def _create_new_session(self) -> Dict[str, Any]:
        """创建新的用户会话"""
        return {
            'session_start_time': time.time(),
            'dialogue_state': DialogueState.INITIAL.value,
            'context_history': deque(maxlen=self.max_context_items),
            'last_query': None,
            'last_query_time': None,
            'last_product': None,
            'last_product_time': None,
            'preferences': {
                'categories': [],
                'products': [],
                'quality_preferences': [],
                'price_sensitivity': 'medium',
                'interaction_style': 'casual'
            },
            'intent_stack': [],  # 意图栈，用于处理嵌套意图
            'clarification_needed': False,
            'clarification_context': None
        }
    
    def _cleanup_expired_context(self, session: Dict[str, Any]) -> None:
        """清理过期的上下文项"""
        current_time = time.time()
        context_history = session['context_history']
        
        # 移除过期的上下文项
        while context_history and (current_time - context_history[0].timestamp) > self.context_window_seconds:
            context_history.popleft()
    
    def _update_dialogue_state(self, session: Dict[str, Any], intent: str) -> None:
        """更新对话状态"""
        current_state = DialogueState(session.get('dialogue_state', DialogueState.INITIAL.value))
        
        # 状态转换逻辑
        state_transitions = {
            'product_query': DialogueState.PRODUCT_INQUIRY,
            'price_query': DialogueState.PRICE_INQUIRY,
            'recommendation': DialogueState.RECOMMENDATION,
            'policy_query': DialogueState.POLICY_INQUIRY,
            'availability': DialogueState.AVAILABILITY_CHECK,
            'clarification': DialogueState.CLARIFICATION
        }
        
        new_state = state_transitions.get(intent, current_state)
        session['dialogue_state'] = new_state.value
        
        # 更新意图栈
        intent_stack = session.get('intent_stack', [])
        if intent not in intent_stack[-3:]:  # 避免重复添加相同意图
            intent_stack.append(intent)
            if len(intent_stack) > 10:  # 限制栈大小
                intent_stack.pop(0)
        session['intent_stack'] = intent_stack
    
    def _update_user_preferences(self, session: Dict[str, Any], content: str, 
                                item_type: str, metadata: Optional[Dict]) -> None:
        """更新用户偏好"""
        preferences = session['preferences']
        
        if item_type == 'product' and metadata:
            # 更新产品偏好
            product_name = metadata.get('name', '')
            if product_name and product_name not in preferences['products']:
                preferences['products'].append(product_name)
                if len(preferences['products']) > 20:  # 限制偏好列表长度
                    preferences['products'].pop(0)
            
            # 更新类别偏好
            category = metadata.get('category', '')
            if category and category not in preferences['categories']:
                preferences['categories'].append(category)
                if len(preferences['categories']) > 10:
                    preferences['categories'].pop(0)
        
        elif item_type == 'query':
            # 从查询中提取品质偏好
            quality_words = ['新鲜', '甜', '香', '脆', '嫩', '好吃', '便宜', '实惠']
            for word in quality_words:
                if word in content and word not in preferences['quality_preferences']:
                    preferences['quality_preferences'].append(word)
                    if len(preferences['quality_preferences']) > 10:
                        preferences['quality_preferences'].pop(0)
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """计算内容相似性（简单版本）"""
        if not text1 or not text2:
            return 0.0
        
        # 简单的关键词重叠计算
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
