#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat AI 增强功能一键集成脚本
无需修改任何现有代码，安全地集成高级功能
"""

import sys
import os
import time
import logging
from typing import Dict, Any

# 确保项目根目录在Python路径中
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print(">> Chat AI 增强功能集成工具")
    print("=" * 60)
    print("本工具将为您的Chat AI系统添加以下增强功能：")
    print("• 深度上下文理解 - 多轮对话记忆和连贯性")
    print("• 个性化学习机制 - 用户偏好学习和自适应")
    print("• 智能语义匹配 - 更准确的意图识别")
    print("• 安全回退机制 - 出错时自动回退到原功能")
    print()
    print("√ 完全兼容现有系统，不修改任何现有代码")
    print("√ 支持动态开启/关闭，随时可以回滚")
    print("√ 内置性能监控和错误处理")
    print("=" * 60)

def check_system_compatibility() -> Dict[str, Any]:
    """检查系统兼容性"""
    print("\n>> 正在检查系统兼容性...")
    
    results = {
        'compatible': True,
        'issues': [],
        'warnings': [],
        'recommendations': []
    }
    
    try:
        # 检查Python版本
        if sys.version_info < (3, 7):
            results['compatible'] = False
            results['issues'].append("Python版本过低，需要3.7+")
        else:
            print(f"√ Python版本: {sys.version.split()[0]}")

        # 检查必要的模块
        required_modules = [
            'src.app.main',
            'src.app.chat.handler',
            'src.app.products.manager'
        ]

        for module in required_modules:
            try:
                __import__(module)
                print(f"√ 模块可用: {module}")
            except ImportError as e:
                results['compatible'] = False
                results['issues'].append(f"缺少必要模块: {module}")

        # 检查增强功能模块
        enhancement_modules = [
            'src.core.enhanced_chat_router',
            'src.core.deep_context_engine',
            'src.app.personalization.learning_engine'
        ]

        for module in enhancement_modules:
            try:
                __import__(module)
                print(f"√ 增强模块: {module}")
            except ImportError as e:
                results['warnings'].append(f"增强模块不可用: {module}")

        # 检查现有ChatHandler
        try:
            from src.app.main import chat_handler
            if chat_handler:
                print("√ 现有ChatHandler可访问")
            else:
                results['warnings'].append("ChatHandler为None，可能影响集成")
        except Exception as e:
            results['warnings'].append(f"无法访问ChatHandler: {e}")

        # 检查可选依赖
        optional_deps = ['numpy', 'jieba']
        for dep in optional_deps:
            try:
                __import__(dep)
                print(f"√ 可选依赖: {dep}")
            except ImportError:
                results['warnings'].append(f"可选依赖缺失: {dep} (不影响基础功能)")
        
    except Exception as e:
        results['compatible'] = False
        results['issues'].append(f"兼容性检查失败: {e}")
    
    return results

def perform_integration(config: Dict[str, Any]) -> bool:
    """执行集成"""
    print("\n>> 正在集成增强功能...")
    
    try:
        from src.integration.hot_integration import runtime_integrate_with_main_app
        
        # 执行运行时集成
        success = runtime_integrate_with_main_app()
        
        if success:
            print("√ 增强功能集成成功！")

            # 验证集成效果
            print("\n>> 验证集成效果...")
            return verify_integration()
        else:
            print("X 增强功能集成失败")
            return False

    except Exception as e:
        print(f"X 集成过程出错: {e}")
        logger.exception("集成失败详情")
        return False

def verify_integration() -> bool:
    """验证集成效果"""
    try:
        from src.app.main import chat_handler
        
        # 检查是否为增强版本
        if hasattr(chat_handler, 'get_enhancement_stats'):
            print("√ 检测到增强版ChatHandler")

            # 测试基本功能
            test_response = chat_handler.handle_chat_message("你好", "test_user")
            if test_response:
                print("√ 基本聊天功能正常")

                # 获取增强统计
                stats = chat_handler.get_enhancement_stats()
                print(f"√ 增强功能状态: {stats['features_enabled']}")

                return True
            else:
                print("X 基本聊天功能异常")
                return False
        else:
            print("X 未检测到增强功能")
            return False

    except Exception as e:
        print(f"X 验证过程出错: {e}")
        return False

def show_usage_guide():
    """显示使用指南"""
    print("\n📖 使用指南")
    print("=" * 60)
    print("集成完成后，您的Chat AI系统已具备以下新能力：")
    print()
    
    print("🧠 深度上下文理解：")
    print("  • 系统现在能记住多轮对话的内容")
    print("  • 支持上下文相关的智能回复")
    print("  • 自动跟踪对话状态和实体")
    print()
    
    print("🎨 个性化学习：")
    print("  • 系统会学习用户的偏好和行为模式")
    print("  • 根据用户习惯调整回复风格")
    print("  • 提供个性化的产品推荐")
    print()
    
    print("🔧 管理和监控：")
    print("  • 访问 /admin/enhancement-stats 查看增强功能统计")
    print("  • 所有原有功能保持不变")
    print("  • 出现问题时自动回退到原功能")
    print()
    
    print("💡 测试建议：")
    print("  1. 尝试多轮对话，观察上下文连贯性")
    print("  2. 重复询问相似问题，观察个性化效果")
    print("  3. 监控系统性能和响应时间")
    print("=" * 60)

def create_monitoring_endpoint():
    """创建监控端点"""
    try:
        # 创建监控路由文件
        monitoring_code = '''
from flask import jsonify
from src.app.main import app, chat_handler

@app.route('/admin/enhancement-stats')
def enhancement_stats():
    """增强功能统计端点"""
    try:
        if hasattr(chat_handler, 'get_enhancement_stats'):
            stats = chat_handler.get_enhancement_stats()
            return jsonify({
                'status': 'enhanced',
                'stats': stats,
                'timestamp': time.time()
            })
        else:
            return jsonify({
                'status': 'not_enhanced',
                'message': '增强功能未启用'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/admin/toggle-enhancements', methods=['POST'])
def toggle_enhancements():
    """动态开启/关闭增强功能"""
    try:
        if hasattr(chat_handler, 'toggle_advanced_features'):
            from flask import request
            data = request.get_json()
            enabled = data.get('enabled', True)
            
            chat_handler.toggle_advanced_features(enabled)
            
            return jsonify({
                'status': 'success',
                'message': f'增强功能已{"启用" if enabled else "禁用"}',
                'enabled': enabled
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '增强功能不可用'
            }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
'''
        
        with open('src/app/monitoring_routes.py', 'w', encoding='utf-8') as f:
            f.write(monitoring_code)

        print("√ 监控端点已创建")
        return True

    except Exception as e:
        print(f"X 创建监控端点失败: {e}")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 兼容性检查
    compat_results = check_system_compatibility()
    
    if not compat_results['compatible']:
        print("\n❌ 系统兼容性检查失败：")
        for issue in compat_results['issues']:
            print(f"  • {issue}")
        print("\n请解决上述问题后重试。")
        return False
    
    if compat_results['warnings']:
        print("\n!! 发现以下警告：")
        for warning in compat_results['warnings']:
            print(f"  • {warning}")
        print("\n这些警告不会阻止集成，但可能影响某些功能。")

    # 询问用户是否继续
    print(f"\n√ 系统兼容性检查通过")
    
    try:
        user_input = input("\n是否继续集成增强功能？(y/N): ").strip().lower()
        if user_input not in ['y', 'yes', '是']:
            print("集成已取消。")
            return False
    except KeyboardInterrupt:
        print("\n集成已取消。")
        return False
    
    # 配置选项
    config = {
        'enable_deep_context': True,
        'enable_personalization': True,
        'enable_advanced_nlp': False,  # 默认关闭避免依赖问题
        'auto_fallback': True
    }
    
    # 执行集成
    success = perform_integration(config)
    
    if success:
        print("\n>> 集成完成！")

        # 创建监控端点
        create_monitoring_endpoint()

        # 显示使用指南
        show_usage_guide()

        print("\n>> 您的Chat AI系统现在已具备增强功能！")
        print("重启应用后即可体验新功能。")

        return True
    else:
        print("\nX 集成失败，系统保持原有功能不变。")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作。")
        sys.exit(1)
    except Exception as e:
        logger.exception("集成脚本执行失败")
        print(f"\nX 意外错误: {e}")
        sys.exit(1)
