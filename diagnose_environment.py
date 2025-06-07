#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境诊断脚本
帮助诊断为什么演示程序在用户终端中无法运行
"""

import sys
import os
import platform
import subprocess

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_python_environment():
    """检查Python环境"""
    print_section("Python环境检查")
    
    print(f"Python版本: {sys.version}")
    print(f"Python可执行文件路径: {sys.executable}")
    print(f"平台: {platform.platform()}")
    print(f"架构: {platform.architecture()}")
    
    # 检查Python路径
    print(f"\nPython模块搜索路径 (前5个):")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i+1}. {path}")
    
    if len(sys.path) > 5:
        print(f"  ... 还有 {len(sys.path) - 5} 个路径")

def check_working_directory():
    """检查工作目录"""
    print_section("工作目录检查")
    
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")
    
    # 检查是否在正确的项目目录
    expected_files = ['demo_hot_integration.py', 'src', 'data']
    missing_files = []
    
    print(f"\n检查必要文件/目录:")
    for file in expected_files:
        if os.path.exists(file):
            print(f"  ✓ {file} - 存在")
        else:
            print(f"  ✗ {file} - 缺失")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  警告: 缺失文件/目录: {missing_files}")
        print("请确保您在正确的项目根目录中运行脚本")

def check_dependencies():
    """检查依赖"""
    print_section("依赖检查")
    
    required_packages = [
        'flask',
        'flask_cors',
        'openai',
        'python-dotenv'
    ]
    
    for package in required_packages:
        try:
            if package == 'flask_cors':
                import flask_cors
                print(f"  ✓ {package} - 已安装 (版本: {flask_cors.__version__})")
            elif package == 'flask':
                import flask
                print(f"  ✓ {package} - 已安装 (版本: {flask.__version__})")
            elif package == 'openai':
                import openai
                print(f"  ✓ {package} - 已安装 (版本: {openai.__version__})")
            elif package == 'python-dotenv':
                import dotenv
                print(f"  ✓ {package} - 已安装")
            else:
                __import__(package)
                print(f"  ✓ {package} - 已安装")
        except ImportError as e:
            print(f"  ✗ {package} - 未安装 ({e})")

def test_module_import():
    """测试模块导入"""
    print_section("模块导入测试")
    
    # 确保项目根目录在Python路径中
    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"已添加项目根目录到Python路径: {project_root}")
    
    # 测试导入主要模块
    test_imports = [
        'src.app.main',
        'src.core.enhanced_chat_router',
        'src.core.deep_context_engine',
        'src.app.personalization.learning_engine'
    ]
    
    for module_name in test_imports:
        try:
            module = __import__(module_name, fromlist=[''])
            print(f"  ✓ {module_name} - 导入成功")
        except Exception as e:
            print(f"  ✗ {module_name} - 导入失败: {e}")

def check_encoding():
    """检查编码设置"""
    print_section("编码检查")
    
    print(f"系统默认编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    
    # 检查终端编码
    try:
        print(f"标准输出编码: {sys.stdout.encoding}")
        print(f"标准错误编码: {sys.stderr.encoding}")
    except:
        print("无法获取终端编码信息")

def run_simple_test():
    """运行简单测试"""
    print_section("简单功能测试")
    
    try:
        # 确保路径正确
        project_root = os.getcwd()
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        print("正在测试基本导入...")
        import src.app.main as main_module
        print("  ✓ 主模块导入成功")
        
        if hasattr(main_module, 'chat_handler'):
            print("  ✓ chat_handler 可访问")
            
            # 测试简单对话
            response = main_module.chat_handler.handle_chat_message("你好", "test_user")
            print(f"  ✓ 基本对话测试成功: {str(response)[:50]}...")
        else:
            print("  ✗ chat_handler 不可访问")
            
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def provide_solutions():
    """提供解决方案"""
    print_section("可能的解决方案")
    
    solutions = [
        "1. 确保在正确的项目根目录中运行脚本",
        "2. 检查Python版本是否为3.8+",
        "3. 安装缺失的依赖: pip install flask flask-cors openai python-dotenv",
        "4. 如果使用虚拟环境，确保已激活",
        "5. 尝试使用完整路径运行: python C:/Users/DT/Desktop/Chat\\ AI/demo_hot_integration.py",
        "6. 检查终端编码设置，建议使用UTF-8",
        "7. 如果仍有问题，尝试重新启动终端"
    ]
    
    for solution in solutions:
        print(f"  {solution}")

def main():
    """主函数"""
    print("Chat AI 环境诊断工具")
    print("此工具将帮助诊断为什么演示程序无法在您的终端中运行")
    
    check_python_environment()
    check_working_directory()
    check_dependencies()
    check_encoding()
    test_module_import()
    run_simple_test()
    provide_solutions()
    
    print_section("诊断完成")
    print("请根据上述检查结果和建议的解决方案来修复问题")
    print("如果问题仍然存在，请将此诊断输出发送给开发者")

if __name__ == "__main__":
    main()
