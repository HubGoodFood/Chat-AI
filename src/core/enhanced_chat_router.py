"""
增强聊天路由器
提供与现有ChatHandler完全兼容的接口，同时集成高级功能
不修改任何现有代码，通过智能路由实现功能增强
"""

import time
import logging
from typing import Union, Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class EnhancedChatRouter:
    """增强聊天路由器 - 完全兼容现有ChatHandler接口"""
    
    def __init__(self, original_chat_handler, 
                 enable_advanced_features: bool = True,
                 enable_deep_context: bool = True,
                 enable_personalization: bool = True,
                 enable_advanced_nlp: bool = False):
        """初始化增强聊天路由器
        
        Args:
            original_chat_handler: 原有的ChatHandler实例
            enable_advanced_features: 是否启用高级功能
            enable_deep_context: 是否启用深度上下文
            enable_personalization: 是否启用个性化
            enable_advanced_nlp: 是否启用高级NLP
        """
        # 保存原有处理器
        self.original_handler = original_chat_handler
        
        # 功能开关
        self.enable_advanced_features = enable_advanced_features
        self.enable_deep_context = enable_deep_context
        self.enable_personalization = enable_personalization
        self.enable_advanced_nlp = enable_advanced_nlp
        
        # 高级功能组件（懒加载）
        self._advanced_engine = None
        self._context_engine = None
        self._personalization_engine = None
        self._nlp_engine = None
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'advanced_requests': 0,
            'fallback_requests': 0,
            'error_count': 0,
            'avg_response_time': 0.0
        }
        
        # 错误阈值（连续错误超过此值将禁用高级功能）
        self.error_threshold = 5
        self.consecutive_errors = 0
        
        logger.info(f"增强聊天路由器初始化完成 - 高级功能: {enable_advanced_features}")
    
    def _lazy_load_advanced_engine(self):
        """懒加载高级聊天引擎"""
        if self._advanced_engine is None and self.enable_advanced_features:
            try:
                from src.core.advanced_chat_engine import AdvancedChatEngine
                
                self._advanced_engine = AdvancedChatEngine(
                    product_manager=self.original_handler.product_manager,
                    policy_manager=self.original_handler.policy_manager,
                    cache_manager=self.original_handler.cache_manager,
                    enable_advanced_nlp=self.enable_advanced_nlp,
                    enable_deep_context=self.enable_deep_context,
                    enable_personalization=self.enable_personalization
                )
                logger.info("高级聊天引擎加载成功")
                
            except Exception as e:
                logger.warning(f"高级聊天引擎加载失败，将使用原有功能: {e}")
                self.enable_advanced_features = False
        
        return self._advanced_engine
    
    def _should_use_advanced_features(self, user_input: str, user_id: str) -> bool:
        """判断是否应该使用高级功能"""
        # 如果高级功能被禁用
        if not self.enable_advanced_features:
            return False
        
        # 如果连续错误过多，暂时禁用
        if self.consecutive_errors >= self.error_threshold:
            return False
        
        # 对于简单的问候语，使用原有功能即可
        simple_greetings = ["你好", "您好", "hi", "hello", "在吗"]
        if user_input.lower().strip() in simple_greetings:
            return False
        
        # 其他情况使用高级功能
        return True
    
    def _safe_execute_advanced(self, func, *args, **kwargs):
        """安全执行高级功能，出错时自动回退"""
        try:
            result = func(*args, **kwargs)
            self.consecutive_errors = 0  # 重置错误计数
            return result, True
        except Exception as e:
            self.consecutive_errors += 1
            self.stats['error_count'] += 1
            logger.warning(f"高级功能执行失败 (错误计数: {self.consecutive_errors}): {e}")
            return None, False
    
    # ==================== 兼容性接口方法 ====================
    
    def handle_chat_message(self, user_input: str, user_id: str) -> Union[str, Dict, None]:
        """处理聊天消息 - 与原有ChatHandler完全兼容的接口"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # 判断是否使用高级功能
            if self._should_use_advanced_features(user_input, user_id):
                # 尝试使用高级功能
                advanced_engine = self._lazy_load_advanced_engine()
                
                if advanced_engine:
                    response, success = self._safe_execute_advanced(
                        advanced_engine.process_message,
                        user_id, user_input
                    )
                    
                    if success and response:
                        self.stats['advanced_requests'] += 1
                        
                        # 转换响应格式以兼容原有接口
                        if hasattr(response, 'content'):
                            final_response = response.content
                        else:
                            final_response = str(response)
                        
                        logger.debug(f"使用高级功能处理: {user_input[:30]}...")
                        return self._finalize_response(final_response, start_time)
            
            # 回退到原有功能
            self.stats['fallback_requests'] += 1
            logger.debug(f"使用原有功能处理: {user_input[:30]}...")
            response = self.original_handler.handle_chat_message(user_input, user_id)
            
            return self._finalize_response(response, start_time)
            
        except Exception as e:
            logger.error(f"聊天消息处理失败: {e}")
            self.stats['error_count'] += 1
            
            # 最后的回退
            try:
                return self.original_handler.handle_chat_message(user_input, user_id)
            except:
                return "抱歉，系统暂时遇到问题，请稍后再试。"
    
    def _finalize_response(self, response, start_time):
        """完成响应处理"""
        # 更新响应时间统计
        response_time = time.time() - start_time
        self.stats['avg_response_time'] = (
            (self.stats['avg_response_time'] * (self.stats['total_requests'] - 1) + response_time) /
            self.stats['total_requests']
        )
        
        return response
    
    # ==================== 代理所有原有方法 ====================
    
    def __getattr__(self, name):
        """代理所有其他方法到原有处理器"""
        if hasattr(self.original_handler, name):
            attr = getattr(self.original_handler, name)
            if callable(attr):
                @wraps(attr)
                def wrapper(*args, **kwargs):
                    return attr(*args, **kwargs)
                return wrapper
            return attr
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    # ==================== 管理和监控方法 ====================
    
    def get_enhancement_stats(self) -> Dict[str, Any]:
        """获取增强功能统计"""
        total = self.stats['total_requests']
        return {
            'total_requests': total,
            'advanced_usage_rate': self.stats['advanced_requests'] / total if total > 0 else 0,
            'fallback_usage_rate': self.stats['fallback_requests'] / total if total > 0 else 0,
            'error_rate': self.stats['error_count'] / total if total > 0 else 0,
            'avg_response_time': self.stats['avg_response_time'],
            'consecutive_errors': self.consecutive_errors,
            'features_enabled': {
                'advanced_features': self.enable_advanced_features,
                'deep_context': self.enable_deep_context,
                'personalization': self.enable_personalization,
                'advanced_nlp': self.enable_advanced_nlp
            }
        }
    
    def toggle_advanced_features(self, enabled: bool):
        """动态开启/关闭高级功能"""
        self.enable_advanced_features = enabled
        if enabled:
            self.consecutive_errors = 0  # 重置错误计数
        logger.info(f"高级功能已{'启用' if enabled else '禁用'}")
    
    def reset_error_count(self):
        """重置错误计数"""
        self.consecutive_errors = 0
        logger.info("错误计数已重置")
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """获取用户洞察（如果高级功能可用）"""
        if self.enable_advanced_features and self._advanced_engine:
            try:
                return self._advanced_engine.get_user_insights(user_id)
            except Exception as e:
                logger.warning(f"获取用户洞察失败: {e}")
        
        return {"status": "advanced_features_not_available"}


def create_enhanced_chat_handler(original_chat_handler, **kwargs):
    """工厂函数：创建增强的聊天处理器
    
    Args:
        original_chat_handler: 原有的ChatHandler实例
        **kwargs: 增强功能配置参数
        
    Returns:
        EnhancedChatRouter: 增强的聊天路由器
    """
    return EnhancedChatRouter(original_chat_handler, **kwargs)


# ==================== 装饰器方式集成 ====================

def enhance_chat_handler(enable_advanced_features=True, 
                        enable_deep_context=True,
                        enable_personalization=True,
                        enable_advanced_nlp=False):
    """装饰器：增强现有的聊天处理器"""
    def decorator(original_handler_class):
        class EnhancedChatHandler(original_handler_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._router = EnhancedChatRouter(
                    self,
                    enable_advanced_features=enable_advanced_features,
                    enable_deep_context=enable_deep_context,
                    enable_personalization=enable_personalization,
                    enable_advanced_nlp=enable_advanced_nlp
                )
            
            def handle_chat_message(self, user_input: str, user_id: str):
                return self._router.handle_chat_message(user_input, user_id)
            
            def get_enhancement_stats(self):
                return self._router.get_enhancement_stats()
        
        return EnhancedChatHandler
    return decorator


# ==================== 全局增强函数 ====================

def enhance_existing_chat_handler(chat_handler_instance, **enhancement_options):
    """增强现有的聊天处理器实例
    
    Args:
        chat_handler_instance: 现有的ChatHandler实例
        **enhancement_options: 增强选项
        
    Returns:
        EnhancedChatRouter: 增强后的处理器
    """
    return EnhancedChatRouter(chat_handler_instance, **enhancement_options)
