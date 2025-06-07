"""
动态增强器
在运行时动态替换和增强现有功能，无需修改源代码
"""

import sys
import types
import logging
from typing import Any, Callable, Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class DynamicEnhancer:
    """动态功能增强器"""
    
    def __init__(self):
        self.original_functions = {}
        self.enhanced_functions = {}
        self.enhancement_stack = []
        
    def enhance_function(self, target_module: str, function_name: str, 
                        enhancement_func: Callable, 
                        preserve_original: bool = True) -> bool:
        """动态增强指定函数
        
        Args:
            target_module: 目标模块名
            function_name: 函数名
            enhancement_func: 增强函数
            preserve_original: 是否保留原函数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取目标模块
            if target_module not in sys.modules:
                logger.error(f"模块 {target_module} 未加载")
                return False
            
            module = sys.modules[target_module]
            
            # 检查函数是否存在
            if not hasattr(module, function_name):
                logger.error(f"模块 {target_module} 中不存在函数 {function_name}")
                return False
            
            original_func = getattr(module, function_name)
            
            # 保存原函数
            key = f"{target_module}.{function_name}"
            if preserve_original:
                self.original_functions[key] = original_func
            
            # 创建增强包装器
            @wraps(original_func)
            def enhanced_wrapper(*args, **kwargs):
                return enhancement_func(original_func, *args, **kwargs)
            
            # 替换函数
            setattr(module, function_name, enhanced_wrapper)
            self.enhanced_functions[key] = enhanced_wrapper
            
            # 记录增强操作
            self.enhancement_stack.append({
                'module': target_module,
                'function': function_name,
                'action': 'enhance'
            })
            
            logger.info(f"成功增强 {key}")
            return True
            
        except Exception as e:
            logger.error(f"增强函数失败: {e}")
            return False
    
    def enhance_method(self, target_class: type, method_name: str,
                      enhancement_func: Callable) -> bool:
        """动态增强类方法"""
        try:
            if not hasattr(target_class, method_name):
                logger.error(f"类 {target_class.__name__} 中不存在方法 {method_name}")
                return False
            
            original_method = getattr(target_class, method_name)
            key = f"{target_class.__module__}.{target_class.__name__}.{method_name}"
            
            # 保存原方法
            self.original_functions[key] = original_method
            
            # 创建增强方法
            @wraps(original_method)
            def enhanced_method(self, *args, **kwargs):
                return enhancement_func(original_method, self, *args, **kwargs)
            
            # 替换方法
            setattr(target_class, method_name, enhanced_method)
            self.enhanced_functions[key] = enhanced_method
            
            logger.info(f"成功增强方法 {key}")
            return True
            
        except Exception as e:
            logger.error(f"增强方法失败: {e}")
            return False
    
    def rollback_enhancement(self, key: str) -> bool:
        """回滚指定的增强"""
        try:
            if key not in self.original_functions:
                logger.warning(f"未找到原函数: {key}")
                return False
            
            parts = key.split('.')
            if len(parts) >= 2:
                module_name = '.'.join(parts[:-1])
                func_name = parts[-1]
                
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    original_func = self.original_functions[key]
                    
                    setattr(module, func_name, original_func)
                    
                    # 清理记录
                    del self.original_functions[key]
                    if key in self.enhanced_functions:
                        del self.enhanced_functions[key]
                    
                    logger.info(f"成功回滚 {key}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"回滚增强失败: {e}")
            return False
    
    def rollback_all(self) -> bool:
        """回滚所有增强"""
        try:
            for key in list(self.original_functions.keys()):
                self.rollback_enhancement(key)
            
            self.enhancement_stack.clear()
            logger.info("所有增强已回滚")
            return True
            
        except Exception as e:
            logger.error(f"回滚所有增强失败: {e}")
            return False


# ==================== 全局增强器实例 ====================

_global_enhancer = DynamicEnhancer()

def enhance_chat_handler_dynamically():
    """动态增强ChatHandler的handle_chat_message方法"""
    try:
        from src.app.chat.handler import ChatHandler
        from src.core.enhanced_chat_router import EnhancedChatRouter
        
        def enhanced_handle_chat_message(original_method, self, user_input: str, user_id: str):
            """增强的handle_chat_message方法"""
            try:
                # 检查是否已经是增强版本
                if hasattr(self, '_enhanced_router'):
                    return self._enhanced_router.handle_chat_message(user_input, user_id)
                
                # 创建增强路由器
                if not hasattr(self, '_enhancement_attempted'):
                    try:
                        self._enhanced_router = EnhancedChatRouter(
                            self,
                            enable_advanced_features=True,
                            enable_deep_context=True,
                            enable_personalization=True,
                            enable_advanced_nlp=False
                        )
                        self._enhancement_attempted = True
                        logger.info(f"为用户 {user_id} 创建了增强路由器")
                        
                        # 使用增强功能
                        return self._enhanced_router.handle_chat_message(user_input, user_id)
                        
                    except Exception as e:
                        logger.warning(f"创建增强路由器失败，使用原功能: {e}")
                        self._enhancement_attempted = True
                        self._enhanced_router = None
                
                # 回退到原方法
                return original_method(self, user_input, user_id)
                
            except Exception as e:
                logger.error(f"增强方法执行失败，回退到原方法: {e}")
                return original_method(self, user_input, user_id)
        
        # 动态增强ChatHandler类的方法
        success = _global_enhancer.enhance_method(
            ChatHandler, 
            'handle_chat_message', 
            enhanced_handle_chat_message
        )
        
        if success:
            logger.info("✅ ChatHandler.handle_chat_message 已动态增强")
            return True
        else:
            logger.error("❌ ChatHandler.handle_chat_message 动态增强失败")
            return False
            
    except Exception as e:
        logger.error(f"动态增强ChatHandler失败: {e}")
        return False

def enhance_flask_chat_route():
    """动态增强Flask的/chat路由"""
    try:
        import src.app.main as main_module
        
        def enhanced_chat_route(original_func, *args, **kwargs):
            """增强的chat路由函数"""
            try:
                # 检查是否有增强的chat_handler
                if hasattr(main_module, 'chat_handler'):
                    handler = main_module.chat_handler
                    
                    # 如果还不是增强版本，尝试增强
                    if not hasattr(handler, 'get_enhancement_stats'):
                        from src.core.enhanced_chat_router import EnhancedChatRouter
                        
                        enhanced_handler = EnhancedChatRouter(
                            handler,
                            enable_advanced_features=True,
                            enable_deep_context=True,
                            enable_personalization=True,
                            enable_advanced_nlp=False
                        )
                        
                        # 替换主模块中的handler
                        main_module.chat_handler = enhanced_handler
                        logger.info("Flask路由中的ChatHandler已动态增强")
                
                # 调用原路由函数
                return original_func(*args, **kwargs)
                
            except Exception as e:
                logger.warning(f"路由增强失败，使用原功能: {e}")
                return original_func(*args, **kwargs)
        
        # 获取Flask应用和路由
        if hasattr(main_module, 'app'):
            app = main_module.app
            
            # 查找chat路由
            for rule in app.url_map.iter_rules():
                if rule.endpoint == 'chat':
                    # 获取路由函数
                    chat_func = app.view_functions.get('chat')
                    if chat_func:
                        # 创建增强包装器
                        @wraps(chat_func)
                        def enhanced_wrapper(*args, **kwargs):
                            return enhanced_chat_route(chat_func, *args, **kwargs)
                        
                        # 替换路由函数
                        app.view_functions['chat'] = enhanced_wrapper
                        
                        logger.info("✅ Flask /chat 路由已动态增强")
                        return True
        
        logger.warning("未找到Flask /chat路由")
        return False
        
    except Exception as e:
        logger.error(f"动态增强Flask路由失败: {e}")
        return False

def apply_all_enhancements():
    """应用所有动态增强"""
    results = []
    
    print("🔧 正在应用动态增强...")
    
    # 1. 增强ChatHandler方法
    print("  • 增强ChatHandler.handle_chat_message...")
    success1 = enhance_chat_handler_dynamically()
    results.append(('ChatHandler方法', success1))
    
    # 2. 增强Flask路由
    print("  • 增强Flask /chat路由...")
    success2 = enhance_flask_chat_route()
    results.append(('Flask路由', success2))
    
    # 统计结果
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n📊 动态增强结果: {successful}/{total} 成功")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    return successful == total

def rollback_all_enhancements():
    """回滚所有动态增强"""
    try:
        success = _global_enhancer.rollback_all()
        if success:
            print("✅ 所有动态增强已回滚")
        else:
            print("❌ 回滚动态增强失败")
        return success
    except Exception as e:
        print(f"❌ 回滚过程出错: {e}")
        return False

def get_enhancement_status():
    """获取增强状态"""
    return {
        'enhanced_functions': list(_global_enhancer.enhanced_functions.keys()),
        'original_functions': list(_global_enhancer.original_functions.keys()),
        'enhancement_count': len(_global_enhancer.enhanced_functions),
        'enhancement_stack': _global_enhancer.enhancement_stack
    }


if __name__ == "__main__":
    # 测试动态增强
    print("动态增强器测试")
    print("=" * 50)
    
    # 应用增强
    success = apply_all_enhancements()
    
    if success:
        print("\n✅ 动态增强应用成功")
        
        # 显示状态
        status = get_enhancement_status()
        print(f"增强函数数量: {status['enhancement_count']}")
        
        # 测试回滚
        input("\n按回车键测试回滚...")
        rollback_all_enhancements()
    else:
        print("\n❌ 动态增强应用失败")
