#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复脚本
自动修复常见的环境问题
"""

import sys
import os
import subprocess

def fix_python_path():
    """修复Python路径问题"""
    print("🔧 修复Python路径...")
    
    # 确保项目根目录在Python路径中
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"✓ 已添加项目根目录到Python路径: {project_root}")
    
    return project_root

def install_dependencies():
    """安装缺失的依赖"""
    print("🔧 检查并安装依赖...")
    
    required_packages = [
        'flask',
        'flask-cors',
        'openai',
        'python-dotenv'
    ]
    
    for package in required_packages:
        try:
            if package == 'flask-cors':
                import flask_cors
            elif package == 'flask':
                import flask
            elif package == 'openai':
                import openai
            elif package == 'python-dotenv':
                import dotenv
            else:
                __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"⚠️  正在安装 {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✓ {package} 安装成功")
            except subprocess.CalledProcessError:
                print(f"✗ {package} 安装失败")

def run_demo():
    """运行演示程序"""
    print("🚀 运行演示程序...")
    
    try:
        # 导入并运行演示
        import demo_hot_integration
        print("✓ 演示程序启动成功")
        return True
    except Exception as e:
        print(f"✗ 演示程序启动失败: {e}")
        return False

def main():
    """主函数"""
    print("Chat AI 快速修复工具")
    print("="*50)
    
    # 修复路径
    project_root = fix_python_path()
    
    # 检查工作目录
    if not os.path.exists('demo_hot_integration.py'):
        print("⚠️  警告: 未在正确的项目目录中")
        print(f"请切换到: {project_root}")
        return
    
    # 安装依赖
    install_dependencies()
    
    # 运行演示
    success = run_demo()
    
    if success:
        print("\n🎉 修复成功！演示程序已启动")
    else:
        print("\n❌ 修复失败，请运行 diagnose_environment.py 获取详细信息")

if __name__ == "__main__":
    main()
