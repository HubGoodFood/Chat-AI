"""
深度上下文理解引擎
实现多轮对话状态跟踪、语义压缩和智能上下文管理
"""

import time
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import deque, defaultdict
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
    COMPARISON = "comparison"
    PURCHASE_INTENT = "purchase_intent"
    CLARIFICATION = "clarification"
    COMPLETED = "completed"

@dataclass
class ContextNode:
    """上下文节点"""
    content: str
    timestamp: float
    node_type: str  # 'query', 'response', 'entity', 'intent', 'emotion'
    metadata: Dict[str, Any]
    importance_score: float = 1.0
    semantic_vector: Optional[np.ndarray] = None
    connections: List[str] = None  # 连接到其他节点的ID

    def __post_init__(self):
        if self.connections is None:
            self.connections = []

@dataclass
class EntityState:
    """实体状态"""
    entity_type: str  # 'product', 'category', 'price', 'preference'
    entity_value: str
    confidence: float
    last_mentioned: float
    mention_count: int = 1
    context_ids: List[str] = None

    def __post_init__(self):
        if self.context_ids is None:
            self.context_ids = []

class DeepContextEngine:
    """深度上下文理解引擎"""
    
    def __init__(self, max_context_nodes: int = 100, 
                 context_window_minutes: int = 60,
                 nlp_engine=None):
        """初始化深度上下文引擎
        
        Args:
            max_context_nodes: 最大上下文节点数
            context_window_minutes: 上下文窗口时间（分钟）
            nlp_engine: NLP引擎实例
        """
        self.max_context_nodes = max_context_nodes
        self.context_window_seconds = context_window_minutes * 60
        self.nlp_engine = nlp_engine
        
        # 用户会话存储
        self.user_sessions: Dict[str, Dict] = {}
        
        # 全局知识图谱
        self.knowledge_graph = {}
        
        # 实体识别模式
        self.entity_patterns = {
            'product': ['苹果', '香蕉', '草莓', '橙子', '葡萄', '西瓜', '梨', '桃子'],
            'category': ['水果', '蔬菜', '肉类', '海鲜', '禽类', '蛋类'],
            'quality': ['新鲜', '甜', '香', '脆', '嫩', '好吃', '优质'],
            'price': ['便宜', '贵', '实惠', '划算', '性价比'],
            'quantity': ['一斤', '一公斤', '半斤', '两斤', '一箱']
        }
        
        logger.info("深度上下文引擎初始化完成")
    
    def get_user_session(self, user_id: str) -> Dict[str, Any]:
        """获取用户会话"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = self._create_new_session()
        return self.user_sessions[user_id]
    
    def _create_new_session(self) -> Dict[str, Any]:
        """创建新的用户会话"""
        return {
            'session_start_time': time.time(),
            'dialogue_state': DialogueState.INITIAL,
            'context_graph': {},  # 上下文图
            'entity_states': {},  # 实体状态跟踪
            'intent_history': deque(maxlen=10),  # 意图历史
            'topic_stack': [],  # 话题栈
            'user_profile': {
                'preferences': {},
                'behavior_patterns': {},
                'interaction_style': 'neutral'
            },
            'semantic_memory': deque(maxlen=50),  # 语义记忆
            'emotional_state': 'neutral',
            'last_activity': time.time()
        }
    
    def update_context(self, user_id: str, content: str, node_type: str,
                      metadata: Optional[Dict] = None, intent: Optional[str] = None) -> str:
        """更新上下文信息
        
        Args:
            user_id: 用户ID
            content: 内容
            node_type: 节点类型
            metadata: 元数据
            intent: 意图
            
        Returns:
            节点ID
        """
        session = self.get_user_session(user_id)
        
        # 创建上下文节点
        node_id = f"{user_id}_{int(time.time() * 1000)}"
        
        # 计算语义向量
        semantic_vector = None
        if self.nlp_engine:
            try:
                semantic_vector = self.nlp_engine.encode_text(content)
            except Exception as e:
                logger.warning(f"语义向量计算失败: {e}")
        
        # 计算重要性分数
        importance_score = self._calculate_importance(content, node_type, metadata)
        
        # 创建节点
        node = ContextNode(
            content=content,
            timestamp=time.time(),
            node_type=node_type,
            metadata=metadata or {},
            importance_score=importance_score,
            semantic_vector=semantic_vector
        )
        
        # 添加到上下文图
        session['context_graph'][node_id] = node
        
        # 更新实体状态
        self._update_entity_states(session, content, node_id)
        
        # 更新对话状态
        if intent:
            self._update_dialogue_state(session, intent)
            session['intent_history'].append((intent, time.time()))
        
        # 更新语义记忆
        self._update_semantic_memory(session, node)
        
        # 建立节点连接
        self._establish_connections(session, node_id)
        
        # 清理过期节点
        self._cleanup_expired_nodes(session)
        
        session['last_activity'] = time.time()
        
        return node_id
    
    def _calculate_importance(self, content: str, node_type: str, metadata: Dict) -> float:
        """计算节点重要性分数"""
        base_scores = {
            'query': 1.0,
            'response': 0.8,
            'entity': 1.2,
            'intent': 0.9,
            'emotion': 0.7
        }
        
        base_score = base_scores.get(node_type, 1.0)
        
        # 根据内容长度调整
        length_factor = min(1.5, len(content) / 50)
        
        # 根据实体数量调整
        entity_count = sum(1 for entities in self.entity_patterns.values() 
                          for entity in entities if entity in content)
        entity_factor = 1.0 + entity_count * 0.1
        
        # 根据元数据调整
        metadata_factor = 1.0
        if metadata:
            if metadata.get('user_feedback') == 'positive':
                metadata_factor += 0.3
            if metadata.get('is_clarification'):
                metadata_factor += 0.2
        
        return base_score * length_factor * entity_factor * metadata_factor
    
    def _update_entity_states(self, session: Dict, content: str, node_id: str):
        """更新实体状态"""
        current_time = time.time()
        
        for entity_type, entities in self.entity_patterns.items():
            for entity in entities:
                if entity in content.lower():
                    entity_key = f"{entity_type}:{entity}"
                    
                    if entity_key in session['entity_states']:
                        # 更新现有实体
                        entity_state = session['entity_states'][entity_key]
                        entity_state.last_mentioned = current_time
                        entity_state.mention_count += 1
                        entity_state.context_ids.append(node_id)
                    else:
                        # 创建新实体
                        session['entity_states'][entity_key] = EntityState(
                            entity_type=entity_type,
                            entity_value=entity,
                            confidence=0.8,
                            last_mentioned=current_time,
                            context_ids=[node_id]
                        )
    
    def _update_dialogue_state(self, session: Dict, intent: str):
        """更新对话状态"""
        state_transitions = {
            'product_query': DialogueState.PRODUCT_INQUIRY,
            'price_query': DialogueState.PRICE_INQUIRY,
            'recommendation': DialogueState.RECOMMENDATION,
            'policy_query': DialogueState.POLICY_INQUIRY,
            'availability': DialogueState.AVAILABILITY_CHECK,
            'comparison': DialogueState.COMPARISON,
            'purchase': DialogueState.PURCHASE_INTENT,
            'clarification': DialogueState.CLARIFICATION
        }
        
        new_state = state_transitions.get(intent, session['dialogue_state'])
        session['dialogue_state'] = new_state
    
    def _update_semantic_memory(self, session: Dict, node: ContextNode):
        """更新语义记忆"""
        if node.semantic_vector is not None:
            session['semantic_memory'].append({
                'vector': node.semantic_vector,
                'content': node.content,
                'timestamp': node.timestamp,
                'importance': node.importance_score
            })
    
    def _establish_connections(self, session: Dict, node_id: str):
        """建立节点连接"""
        if not self.nlp_engine:
            return
        
        current_node = session['context_graph'][node_id]
        if current_node.semantic_vector is None:
            return
        
        # 与最近的节点建立连接
        recent_nodes = []
        current_time = time.time()
        
        for nid, node in session['context_graph'].items():
            if (nid != node_id and 
                node.semantic_vector is not None and
                current_time - node.timestamp < 300):  # 5分钟内
                recent_nodes.append((nid, node))
        
        # 计算语义相似度并建立连接
        for nid, node in recent_nodes:
            try:
                similarity = self._cosine_similarity(
                    current_node.semantic_vector, 
                    node.semantic_vector
                )
                
                if similarity > 0.7:  # 高相似度阈值
                    current_node.connections.append(nid)
                    node.connections.append(node_id)
                    
            except Exception as e:
                logger.warning(f"建立节点连接失败: {e}")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def get_relevant_context(self, user_id: str, query: str, 
                           max_nodes: int = 10) -> List[ContextNode]:
        """获取相关上下文"""
        session = self.get_user_session(user_id)
        
        if not self.nlp_engine:
            # 回退到简单的时间排序
            nodes = list(session['context_graph'].values())
            nodes.sort(key=lambda x: x.timestamp, reverse=True)
            return nodes[:max_nodes]
        
        try:
            query_vector = self.nlp_engine.encode_text(query)
            scored_nodes = []
            
            for node in session['context_graph'].values():
                if node.semantic_vector is not None:
                    similarity = self._cosine_similarity(query_vector, node.semantic_vector)
                    # 综合相似度和重要性分数
                    final_score = similarity * 0.7 + node.importance_score * 0.3
                    scored_nodes.append((node, final_score))
            
            # 按分数排序
            scored_nodes.sort(key=lambda x: x[1], reverse=True)
            
            return [node for node, score in scored_nodes[:max_nodes]]
            
        except Exception as e:
            logger.error(f"获取相关上下文失败: {e}")
            return []
    
    def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """获取上下文摘要"""
        session = self.get_user_session(user_id)
        
        # 统计信息
        total_nodes = len(session['context_graph'])
        active_entities = len([e for e in session['entity_states'].values() 
                             if time.time() - e.last_mentioned < 1800])  # 30分钟内
        
        # 最近的意图
        recent_intents = list(session['intent_history'])[-3:]
        
        # 主要实体
        top_entities = sorted(
            session['entity_states'].items(),
            key=lambda x: x[1].mention_count,
            reverse=True
        )[:5]
        
        return {
            'dialogue_state': session['dialogue_state'].value,
            'total_context_nodes': total_nodes,
            'active_entities': active_entities,
            'recent_intents': [intent for intent, _ in recent_intents],
            'top_entities': [(key.split(':')[1], state.mention_count) 
                           for key, state in top_entities],
            'session_duration': time.time() - session['session_start_time'],
            'emotional_state': session['emotional_state']
        }
    
    def _cleanup_expired_nodes(self, session: Dict):
        """清理过期节点"""
        current_time = time.time()
        expired_nodes = []
        
        for node_id, node in session['context_graph'].items():
            if current_time - node.timestamp > self.context_window_seconds:
                expired_nodes.append(node_id)
        
        for node_id in expired_nodes:
            del session['context_graph'][node_id]
        
        # 限制节点总数
        if len(session['context_graph']) > self.max_context_nodes:
            # 按重要性和时间排序，保留最重要的节点
            nodes = list(session['context_graph'].items())
            nodes.sort(key=lambda x: (x[1].importance_score, x[1].timestamp), reverse=True)
            
            # 保留前N个节点
            keep_nodes = dict(nodes[:self.max_context_nodes])
            session['context_graph'] = keep_nodes
