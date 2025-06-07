"""
高级聊天引擎
集成所有先进的NLP、上下文理解和个性化学习组件
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# 导入新的高级组件
from src.app.nlp.advanced_nlp_engine import AdvancedNLPEngine
from src.core.deep_context_engine import DeepContextEngine
from src.app.personalization.learning_engine import PersonalizationEngine

# 导入现有组件
from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.app.policy.manager import PolicyManager
from src.core.cache import CacheManager

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """聊天响应结构"""
    content: str
    intent: str
    confidence: float
    personalized: bool
    context_used: bool
    response_time: float
    metadata: Dict[str, Any]

class AdvancedChatEngine:
    """高级聊天引擎"""
    
    def __init__(self, 
                 product_manager: ProductManager,
                 policy_manager: PolicyManager = None,
                 cache_manager: CacheManager = None,
                 enable_advanced_nlp: bool = True,
                 enable_deep_context: bool = True,
                 enable_personalization: bool = True):
        """初始化高级聊天引擎
        
        Args:
            product_manager: 产品管理器
            policy_manager: 政策管理器
            cache_manager: 缓存管理器
            enable_advanced_nlp: 是否启用高级NLP
            enable_deep_context: 是否启用深度上下文
            enable_personalization: 是否启用个性化
        """
        self.product_manager = product_manager
        self.policy_manager = policy_manager or PolicyManager(lazy_load=True)
        self.cache_manager = cache_manager or CacheManager()
        
        # 功能开关
        self.enable_advanced_nlp = enable_advanced_nlp
        self.enable_deep_context = enable_deep_context
        self.enable_personalization = enable_personalization
        
        # 初始化高级组件
        self.nlp_engine = None
        self.context_engine = None
        self.personalization_engine = None
        self.base_chat_handler = None
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'advanced_nlp_usage': 0,
            'context_usage': 0,
            'personalization_usage': 0,
            'avg_response_time': 0.0,
            'error_count': 0
        }
        
        self._initialize_components()
        
        logger.info("高级聊天引擎初始化完成")
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 初始化基础聊天处理器
            self.base_chat_handler = ChatHandler(
                product_manager=self.product_manager,
                policy_manager=self.policy_manager,
                cache_manager=self.cache_manager
            )
            
            # 初始化高级NLP引擎
            if self.enable_advanced_nlp:
                try:
                    self.nlp_engine = AdvancedNLPEngine(lazy_load=True)
                    logger.info("高级NLP引擎已启用")
                except Exception as e:
                    logger.warning(f"高级NLP引擎初始化失败，将使用基础功能: {e}")
                    self.enable_advanced_nlp = False
            
            # 初始化深度上下文引擎
            if self.enable_deep_context:
                try:
                    self.context_engine = DeepContextEngine(nlp_engine=self.nlp_engine)
                    logger.info("深度上下文引擎已启用")
                except Exception as e:
                    logger.warning(f"深度上下文引擎初始化失败: {e}")
                    self.enable_deep_context = False
            
            # 初始化个性化引擎
            if self.enable_personalization:
                try:
                    self.personalization_engine = PersonalizationEngine(
                        nlp_engine=self.nlp_engine,
                        context_engine=self.context_engine
                    )
                    logger.info("个性化学习引擎已启用")
                except Exception as e:
                    logger.warning(f"个性化引擎初始化失败: {e}")
                    self.enable_personalization = False
                    
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def process_message(self, user_id: str, message: str, 
                       context: Optional[Dict] = None) -> ChatResponse:
        """处理用户消息
        
        Args:
            user_id: 用户ID
            message: 用户消息
            context: 额外上下文信息
            
        Returns:
            聊天响应
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # 1. 预处理和意图识别
            intent, confidence = self._detect_intent_advanced(user_id, message)
            
            # 2. 获取相关上下文
            relevant_context = self._get_relevant_context(user_id, message, intent)
            
            # 3. 生成基础响应
            base_response = self._generate_base_response(user_id, message, intent, context)
            
            # 4. 个性化优化
            personalized_response = self._apply_personalization(
                user_id, message, intent, base_response, relevant_context
            )
            
            # 5. 更新上下文和学习
            self._update_context_and_learning(
                user_id, message, intent, personalized_response
            )
            
            # 6. 构建响应
            response_time = time.time() - start_time
            self.stats['avg_response_time'] = (
                (self.stats['avg_response_time'] * (self.stats['total_requests'] - 1) + response_time) /
                self.stats['total_requests']
            )
            
            return ChatResponse(
                content=personalized_response,
                intent=intent,
                confidence=confidence,
                personalized=self.enable_personalization,
                context_used=self.enable_deep_context and len(relevant_context) > 0,
                response_time=response_time,
                metadata={
                    'context_nodes': len(relevant_context) if relevant_context else 0,
                    'nlp_engine_used': self.enable_advanced_nlp,
                    'user_id': user_id
                }
            )
            
        except Exception as e:
            self.stats['error_count'] += 1
            logger.error(f"处理消息失败: {e}")
            
            # 回退到基础处理
            return self._fallback_response(user_id, message, start_time)
    
    def _detect_intent_advanced(self, user_id: str, message: str) -> Tuple[str, float]:
        """高级意图识别"""
        try:
            # 使用基础意图识别
            base_intent = self.base_chat_handler.detect_intent(message)
            base_confidence = 0.8  # 基础置信度
            
            if not self.enable_advanced_nlp or not self.nlp_engine:
                return base_intent, base_confidence
            
            # 使用高级NLP进行语义分析
            self.stats['advanced_nlp_usage'] += 1
            
            # 获取语义特征
            semantic_features = self._extract_semantic_features(message)
            
            # 结合上下文信息调整意图识别
            if self.enable_deep_context and self.context_engine:
                context_intent = self._get_context_influenced_intent(user_id, message, base_intent)
                if context_intent != base_intent:
                    logger.debug(f"上下文调整意图: {base_intent} -> {context_intent}")
                    return context_intent, min(0.95, base_confidence + 0.1)
            
            return base_intent, base_confidence
            
        except Exception as e:
            logger.warning(f"高级意图识别失败，回退到基础识别: {e}")
            return self.base_chat_handler.detect_intent(message), 0.7
    
    def _extract_semantic_features(self, message: str) -> Dict[str, Any]:
        """提取语义特征"""
        if not self.nlp_engine:
            return {}
        
        try:
            return {
                'keywords': self.nlp_engine.extract_keywords(message),
                'sentiment': self.nlp_engine.analyze_sentiment(message),
                'semantic_vector': self.nlp_engine.encode_text(message)
            }
        except Exception as e:
            logger.warning(f"语义特征提取失败: {e}")
            return {}
    
    def _get_context_influenced_intent(self, user_id: str, message: str, base_intent: str) -> str:
        """基于上下文调整意图"""
        if not self.context_engine:
            return base_intent
        
        try:
            # 获取用户会话
            session = self.context_engine.get_user_session(user_id)
            
            # 检查对话状态
            dialogue_state = session['dialogue_state']
            
            # 根据对话状态调整意图
            if dialogue_state.value == 'product_inquiry' and '多少钱' in message:
                return 'price_query'
            elif dialogue_state.value == 'recommendation' and ('还有' in message or '其他' in message):
                return 'recommendation'
            
            return base_intent
            
        except Exception as e:
            logger.warning(f"上下文意图调整失败: {e}")
            return base_intent
    
    def _get_relevant_context(self, user_id: str, message: str, intent: str) -> List[Any]:
        """获取相关上下文"""
        if not self.enable_deep_context or not self.context_engine:
            return []
        
        try:
            self.stats['context_usage'] += 1
            return self.context_engine.get_relevant_context(user_id, message, max_nodes=5)
        except Exception as e:
            logger.warning(f"获取上下文失败: {e}")
            return []
    
    def _generate_base_response(self, user_id: str, message: str, intent: str, 
                              context: Optional[Dict]) -> str:
        """生成基础响应"""
        try:
            # 使用基础聊天处理器生成响应
            return self.base_chat_handler.handle_message(message, user_id)
        except Exception as e:
            logger.error(f"基础响应生成失败: {e}")
            return "抱歉，我现在无法处理您的请求，请稍后再试。"
    
    def _apply_personalization(self, user_id: str, message: str, intent: str,
                             base_response: str, context: List[Any]) -> str:
        """应用个性化优化"""
        if not self.enable_personalization or not self.personalization_engine:
            return base_response
        
        try:
            self.stats['personalization_usage'] += 1
            
            # 获取个性化回复风格
            style_config = self.personalization_engine.get_adaptive_response_style(user_id)
            
            # 根据用户偏好调整响应
            if style_config['response_length'] == 'short':
                # 简化响应
                return self._simplify_response(base_response)
            elif style_config['response_length'] == 'long':
                # 详细化响应
                return self._elaborate_response(base_response, context)
            
            return base_response
            
        except Exception as e:
            logger.warning(f"个性化处理失败: {e}")
            return base_response
    
    def _simplify_response(self, response: str) -> str:
        """简化响应"""
        # 简单的响应简化逻辑
        sentences = response.split('。')
        if len(sentences) > 2:
            return '。'.join(sentences[:2]) + '。'
        return response
    
    def _elaborate_response(self, response: str, context: List[Any]) -> str:
        """详细化响应"""
        # 简单的响应详细化逻辑
        if context and len(context) > 0:
            return response + "\n\n根据您之前的询问，我还可以为您提供更多相关信息。"
        return response
    
    def _update_context_and_learning(self, user_id: str, message: str, 
                                   intent: str, response: str) -> None:
        """更新上下文和学习"""
        try:
            # 更新深度上下文
            if self.enable_deep_context and self.context_engine:
                self.context_engine.update_context(
                    user_id=user_id,
                    content=message,
                    node_type='query',
                    intent=intent
                )
                
                self.context_engine.update_context(
                    user_id=user_id,
                    content=response,
                    node_type='response'
                )
            
            # 更新个性化学习
            if self.enable_personalization and self.personalization_engine:
                self.personalization_engine.record_interaction(
                    user_id=user_id,
                    query=message,
                    intent=intent,
                    response=response
                )
                
        except Exception as e:
            logger.warning(f"上下文和学习更新失败: {e}")
    
    def _fallback_response(self, user_id: str, message: str, start_time: float) -> ChatResponse:
        """回退响应"""
        try:
            fallback_content = self.base_chat_handler.handle_message(message, user_id)
        except:
            fallback_content = "抱歉，我现在无法处理您的请求，请稍后再试。"
        
        return ChatResponse(
            content=fallback_content,
            intent='unknown',
            confidence=0.3,
            personalized=False,
            context_used=False,
            response_time=time.time() - start_time,
            metadata={'fallback': True}
        )
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        stats = self.stats.copy()
        
        # 添加组件状态
        stats['components'] = {
            'advanced_nlp': self.enable_advanced_nlp,
            'deep_context': self.enable_deep_context,
            'personalization': self.enable_personalization
        }
        
        # 添加组件性能统计
        if self.nlp_engine:
            stats['nlp_performance'] = self.nlp_engine.get_performance_stats()
        
        return stats
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """获取用户洞察"""
        insights = {}
        
        # 上下文洞察
        if self.enable_deep_context and self.context_engine:
            insights['context'] = self.context_engine.get_context_summary(user_id)
        
        # 个性化洞察
        if self.enable_personalization and self.personalization_engine:
            insights['personalization'] = self.personalization_engine.get_learning_stats(user_id)
        
        return insights
