#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖安装脚本
自动安装Chat AI系统所需的所有依赖
"""

import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {package} 安装失败")
        return False

def main():
    """主函数"""
    print("Chat AI 依赖安装工具")
    print("="*50)
    
    # 核心依赖列表
    core_dependencies = [
        'flask==2.3.3',
        'flask-cors==4.0.0',
        'openai==1.12.0',
        'python-dotenv==1.0.0',
        'jieba==0.42.1',
        'pypinyin==0.49.0',
        'python-Levenshtein==0.23.0',
        'scikit-learn==1.3.2',
        'pandas==2.1.4',
        'joblib==1.3.2'
    ]
    
    # 可选依赖
    optional_dependencies = [
        'redis==5.0.1',
        'psutil==7.0.0'
    ]
    
    print("正在安装核心依赖...")
    success_count = 0
    
    for package in core_dependencies:
        if install_package(package):
            success_count += 1
    
    print(f"\n核心依赖安装完成: {success_count}/{len(core_dependencies)}")
    
    if success_count == len(core_dependencies):
        print("🎉 所有核心依赖安装成功！")
        
        # 询问是否安装可选依赖
        install_optional = input("\n是否安装可选依赖（Redis缓存等）？(y/n): ").lower().strip()
        
        if install_optional == 'y':
            print("\n正在安装可选依赖...")
            for package in optional_dependencies:
                install_package(package)
        
        print("\n✅ 安装完成！现在可以运行演示程序了：")
        print("python demo_hot_integration.py")
    else:
        print("❌ 部分依赖安装失败，请检查网络连接或Python环境")

if __name__ == "__main__":
    main()
