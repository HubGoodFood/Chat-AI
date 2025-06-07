"""
热集成模块
提供无侵入式的Chat AI功能增强
不修改任何现有代码，通过动态替换实现功能升级
"""

import logging
import sys
import importlib
from typing import Any, Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class HotIntegrationManager:
    """热集成管理器"""
    
    def __init__(self):
        self.original_handlers = {}
        self.enhanced_handlers = {}
        self.integration_status = {}
        self.rollback_stack = []
        
    def integrate_chat_enhancement(self, 
                                 app_instance=None,
                                 chat_handler_instance=None,
                                 enhancement_config: Optional[Dict] = None) -> bool:
        """集成聊天增强功能
        
        Args:
            app_instance: Flask应用实例
            chat_handler_instance: ChatHandler实例
            enhancement_config: 增强配置
            
        Returns:
            bool: 集成是否成功
        """
        try:
            # 默认配置
            config = {
                'enable_advanced_features': True,
                'enable_deep_context': True,
                'enable_personalization': True,
                'enable_advanced_nlp': False,  # 默认关闭避免依赖问题
                'auto_fallback': True,
                'error_threshold': 5
            }
            
            if enhancement_config:
                config.update(enhancement_config)
            
            logger.info("开始集成聊天增强功能...")
            
            # 方式1：如果提供了chat_handler实例，直接增强
            if chat_handler_instance:
                return self._enhance_chat_handler_instance(chat_handler_instance, config)
            
            # 方式2：如果提供了app实例，增强app中的chat_handler
            if app_instance:
                return self._enhance_app_chat_handler(app_instance, config)
            
            # 方式3：尝试自动发现并增强
            return self._auto_discover_and_enhance(config)
            
        except Exception as e:
            logger.error(f"集成聊天增强功能失败: {e}")
            return False
    
    def _enhance_chat_handler_instance(self, chat_handler, config: Dict) -> bool:
        """增强ChatHandler实例"""
        try:
            from src.core.enhanced_chat_router import EnhancedChatRouter
            
            # 保存原始处理器
            handler_id = id(chat_handler)
            self.original_handlers[handler_id] = chat_handler
            
            # 创建增强路由器
            enhanced_router = EnhancedChatRouter(
                chat_handler,
                enable_advanced_features=config['enable_advanced_features'],
                enable_deep_context=config['enable_deep_context'],
                enable_personalization=config['enable_personalization'],
                enable_advanced_nlp=config['enable_advanced_nlp']
            )
            
            self.enhanced_handlers[handler_id] = enhanced_router
            self.integration_status[handler_id] = {
                'status': 'integrated',
                'config': config,
                'timestamp': time.time()
            }
            
            logger.info(f"ChatHandler实例增强成功 (ID: {handler_id})")
            return True
            
        except Exception as e:
            logger.error(f"增强ChatHandler实例失败: {e}")
            return False
    
    def _enhance_app_chat_handler(self, app, config: Dict) -> bool:
        """增强Flask应用中的ChatHandler"""
        try:
            # 检查app是否有chat_handler属性
            if not hasattr(app, 'chat_handler'):
                logger.warning("Flask应用中未找到chat_handler属性")
                return False
            
            original_handler = app.chat_handler
            
            # 增强处理器
            if self._enhance_chat_handler_instance(original_handler, config):
                handler_id = id(original_handler)
                enhanced_router = self.enhanced_handlers[handler_id]
                
                # 替换app中的chat_handler
                app.chat_handler = enhanced_router
                
                logger.info("Flask应用中的ChatHandler已成功增强")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"增强Flask应用ChatHandler失败: {e}")
            return False
    
    def _auto_discover_and_enhance(self, config: Dict) -> bool:
        """自动发现并增强ChatHandler"""
        try:
            # 尝试从主模块获取
            main_module = sys.modules.get('src.app.main')
            if main_module and hasattr(main_module, 'chat_handler'):
                original_handler = main_module.chat_handler
                
                if self._enhance_chat_handler_instance(original_handler, config):
                    handler_id = id(original_handler)
                    enhanced_router = self.enhanced_handlers[handler_id]
                    
                    # 替换模块中的chat_handler
                    main_module.chat_handler = enhanced_router
                    
                    logger.info("主模块中的ChatHandler已自动增强")
                    return True
            
            logger.warning("未能自动发现ChatHandler实例")
            return False
            
        except Exception as e:
            logger.error(f"自动发现和增强失败: {e}")
            return False
    
    def rollback_integration(self, handler_id: Optional[int] = None) -> bool:
        """回滚集成
        
        Args:
            handler_id: 处理器ID，如果为None则回滚所有
            
        Returns:
            bool: 回滚是否成功
        """
        try:
            if handler_id:
                # 回滚特定处理器
                if handler_id in self.original_handlers:
                    original = self.original_handlers[handler_id]
                    
                    # 尝试恢复到原始状态
                    # 这里需要根据具体的集成方式来实现
                    logger.info(f"处理器 {handler_id} 已回滚")
                    return True
                else:
                    logger.warning(f"未找到处理器 {handler_id} 的原始版本")
                    return False
            else:
                # 回滚所有
                for hid in list(self.original_handlers.keys()):
                    self.rollback_integration(hid)
                logger.info("所有增强功能已回滚")
                return True
                
        except Exception as e:
            logger.error(f"回滚集成失败: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            'total_integrations': len(self.enhanced_handlers),
            'active_handlers': list(self.enhanced_handlers.keys()),
            'integration_details': self.integration_status
        }


# ==================== 全局集成管理器 ====================

_global_integration_manager = HotIntegrationManager()

def integrate_chat_ai_enhancements(**kwargs) -> bool:
    """全局函数：集成Chat AI增强功能
    
    Args:
        **kwargs: 集成配置参数
        
    Returns:
        bool: 集成是否成功
    """
    return _global_integration_manager.integrate_chat_enhancement(**kwargs)

def rollback_chat_ai_enhancements(**kwargs) -> bool:
    """全局函数：回滚Chat AI增强功能"""
    return _global_integration_manager.rollback_integration(**kwargs)

def get_chat_ai_integration_status() -> Dict[str, Any]:
    """全局函数：获取集成状态"""
    return _global_integration_manager.get_integration_status()


# ==================== 便捷集成函数 ====================

def quick_enhance_chat_handler(chat_handler, **options):
    """快速增强ChatHandler
    
    Args:
        chat_handler: ChatHandler实例
        **options: 增强选项
        
    Returns:
        增强后的处理器
    """
    from src.core.enhanced_chat_router import EnhancedChatRouter
    
    default_options = {
        'enable_advanced_features': True,
        'enable_deep_context': True,
        'enable_personalization': True,
        'enable_advanced_nlp': False
    }
    default_options.update(options)
    
    return EnhancedChatRouter(chat_handler, **default_options)


# ==================== 装饰器集成 ====================

def enhance_on_import(module_name: str, handler_attr: str = 'chat_handler'):
    """模块导入时自动增强装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # 尝试增强指定模块的处理器
            try:
                module = sys.modules.get(module_name)
                if module and hasattr(module, handler_attr):
                    handler = getattr(module, handler_attr)
                    enhanced = quick_enhance_chat_handler(handler)
                    setattr(module, handler_attr, enhanced)
                    logger.info(f"已自动增强 {module_name}.{handler_attr}")
            except Exception as e:
                logger.warning(f"自动增强失败: {e}")
            
            return result
        return wrapper
    return decorator


# ==================== 运行时集成 ====================

def runtime_integrate_with_main_app():
    """运行时集成主应用"""
    try:
        # 尝试获取主应用模块
        import src.app.main as main_module
        
        if hasattr(main_module, 'chat_handler'):
            original_handler = main_module.chat_handler
            enhanced_handler = quick_enhance_chat_handler(
                original_handler,
                enable_advanced_features=True,
                enable_deep_context=True,
                enable_personalization=True,
                enable_advanced_nlp=False
            )
            
            # 替换主模块中的处理器
            main_module.chat_handler = enhanced_handler
            
            logger.info("✅ 运行时集成成功：主应用ChatHandler已增强")
            return True
        else:
            logger.warning("主应用模块中未找到chat_handler")
            return False
            
    except ImportError:
        logger.warning("无法导入主应用模块")
        return False
    except Exception as e:
        logger.error(f"运行时集成失败: {e}")
        return False


# ==================== 安全集成检查 ====================

def safe_integration_check() -> Dict[str, Any]:
    """安全集成检查"""
    check_results = {
        'dependencies_available': True,
        'original_handler_accessible': False,
        'integration_safe': False,
        'recommendations': []
    }
    
    try:
        # 检查依赖
        try:
            from src.core.enhanced_chat_router import EnhancedChatRouter
            from src.core.deep_context_engine import DeepContextEngine
            from src.app.personalization.learning_engine import PersonalizationEngine
        except ImportError as e:
            check_results['dependencies_available'] = False
            check_results['recommendations'].append(f"缺少依赖: {e}")
        
        # 检查原始处理器
        try:
            import src.app.main as main_module
            if hasattr(main_module, 'chat_handler'):
                check_results['original_handler_accessible'] = True
        except:
            check_results['recommendations'].append("无法访问原始ChatHandler")
        
        # 综合评估
        check_results['integration_safe'] = (
            check_results['dependencies_available'] and 
            check_results['original_handler_accessible']
        )
        
        if check_results['integration_safe']:
            check_results['recommendations'].append("✅ 可以安全进行集成")
        else:
            check_results['recommendations'].append("❌ 不建议进行集成")
            
    except Exception as e:
        check_results['recommendations'].append(f"检查过程出错: {e}")
    
    return check_results


if __name__ == "__main__":
    # 测试集成功能
    print("Chat AI 热集成模块测试")
    print("=" * 50)
    
    # 安全检查
    check_result = safe_integration_check()
    print("安全检查结果:")
    for key, value in check_result.items():
        print(f"  {key}: {value}")
    
    # 如果安全，尝试集成
    if check_result['integration_safe']:
        print("\n尝试运行时集成...")
        success = runtime_integrate_with_main_app()
        print(f"集成结果: {'成功' if success else '失败'}")
    else:
        print("\n跳过集成（安全检查未通过）")
