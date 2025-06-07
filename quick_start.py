#!/usr/bin/env python3
"""
Chat AI 快速启动和导航脚本
帮助用户快速了解项目结构和启动应用
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("🚀 Chat AI 快速启动助手")
    print("=" * 60)
    print()

def check_dependencies():
    """检查依赖是否已安装"""
    print("🔍 检查依赖...")
    
    try:
        import flask
        print("✅ Flask 已安装")
    except ImportError:
        print("❌ Flask 未安装")
        return False
    
    try:
        import redis
        print("✅ Redis 库已安装")
    except ImportError:
        print("⚠️ Redis 库未安装（可选）")
    
    try:
        import psutil
        print("✅ psutil 已安装")
    except ImportError:
        print("⚠️ psutil 未安装（可选）")
    
    return True

def show_project_structure():
    """显示项目结构"""
    print("\n📁 项目结构概览:")
    print("""
Chat AI/
├── 📄 README.md                    # 项目说明
├── 📄 PROJECT_STRUCTURE.md         # 详细结构说明
├── 📄 app.py                       # 应用入口
├── 📄 requirements_lightweight.txt # 轻量级依赖（推荐）
│
├── 📂 docs/                        # 📚 文档目录
│   ├── 📂 optimization/            # 🚀 优化文档
│   ├── 📂 guides/                  # 📖 详细指南
│   └── 📂 deployment/              # 🚀 部署文档
│
├── 📂 scripts/                     # 🛠️ 脚本目录
│   ├── 📂 testing/                 # 🧪 测试脚本
│   └── 📂 optimization/            # 优化脚本
│
├── 📂 config/                      # ⚙️ 配置目录
│   └── 📂 deployment/              # 部署配置
│
└── 📂 src/                         # 源代码
    ├── 📂 app/                     # 应用模块
    └── 📂 core/                    # 核心功能
""")

def show_quick_commands():
    """显示快速命令"""
    print("\n⚡ 快速命令:")
    print("1. 安装轻量级依赖: pip install -r requirements_lightweight.txt")
    print("2. 启动应用: python app.py")
    print("3. 访问主界面: http://localhost:5000/")
    print("4. 访问监控仪表板: http://localhost:5000/monitoring/dashboard")
    print("5. 运行测试: python scripts/testing/test_optimization.py")

def show_documentation_menu():
    """显示文档菜单"""
    print("\n📚 文档导航:")
    docs = {
        "1": ("优化路线图", "docs/optimization/FUTURE_OPTIMIZATION_ROADMAP.md"),
        "2": ("实施检查清单", "docs/optimization/IMPLEMENTATION_CHECKLIST.md"),
        "3": ("数据库迁移指南", "docs/guides/DATABASE_MIGRATION_GUIDE.md"),
        "4": ("前端优化指南", "docs/guides/FRONTEND_OPTIMIZATION_GUIDE.md"),
        "5": ("API安全优化指南", "docs/guides/API_SECURITY_OPTIMIZATION_GUIDE.md"),
        "6": ("Redis监控配置指南", "docs/guides/REDIS_MONITORING_SETUP.md"),
        "7": ("项目结构说明", "PROJECT_STRUCTURE.md"),
    }
    
    for key, (title, path) in docs.items():
        print(f"{key}. {title}")
    
    return docs

def open_documentation(docs):
    """打开文档"""
    choice = input("\n选择要查看的文档 (1-7, 或按 Enter 跳过): ").strip()
    
    if choice in docs:
        title, path = docs[choice]
        if os.path.exists(path):
            print(f"📖 正在打开: {title}")
            if sys.platform.startswith('win'):
                os.startfile(path)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        else:
            print(f"❌ 文件不存在: {path}")

def install_dependencies():
    """安装依赖"""
    print("\n📦 安装依赖...")
    
    choice = input("选择依赖版本 (1: 轻量级[推荐], 2: 原版, Enter: 跳过): ").strip()
    
    if choice == "1":
        requirements_file = "requirements_lightweight.txt"
    elif choice == "2":
        requirements_file = "requirements.txt"
    else:
        print("⏭️ 跳过依赖安装")
        return
    
    if os.path.exists(requirements_file):
        print(f"正在安装 {requirements_file}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
            print("✅ 依赖安装成功")
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败")
    else:
        print(f"❌ 文件不存在: {requirements_file}")

def start_application():
    """启动应用"""
    choice = input("\n🚀 是否启动应用? (y/N): ").strip().lower()
    
    if choice == 'y':
        print("正在启动 Chat AI...")
        try:
            # 启动应用
            subprocess.Popen([sys.executable, "app.py"])
            print("✅ 应用已启动")
            
            # 等待一下让应用启动
            import time
            time.sleep(3)
            
            # 询问是否打开浏览器
            open_browser = input("是否打开浏览器? (Y/n): ").strip().lower()
            if open_browser != 'n':
                print("🌐 正在打开浏览器...")
                webbrowser.open('http://localhost:5000/')
                
                # 询问是否打开监控仪表板
                open_monitoring = input("是否打开监控仪表板? (Y/n): ").strip().lower()
                if open_monitoring != 'n':
                    webbrowser.open('http://localhost:5000/monitoring/dashboard')
                    
        except Exception as e:
            print(f"❌ 启动失败: {e}")

def run_tests():
    """运行测试"""
    choice = input("\n🧪 是否运行测试验证? (y/N): ").strip().lower()
    
    if choice == 'y':
        test_scripts = [
            "scripts/testing/test_optimization.py",
            "scripts/testing/test_redis_monitoring.py"
        ]
        
        for script in test_scripts:
            if os.path.exists(script):
                print(f"运行测试: {script}")
                try:
                    subprocess.run([sys.executable, script], check=True)
                except subprocess.CalledProcessError:
                    print(f"❌ 测试失败: {script}")
            else:
                print(f"⚠️ 测试文件不存在: {script}")

def main():
    """主函数"""
    print_banner()
    
    # 检查当前目录
    if not os.path.exists("app.py"):
        print("❌ 请在 Chat AI 项目根目录中运行此脚本")
        return
    
    # 显示项目结构
    show_project_structure()
    
    # 显示快速命令
    show_quick_commands()
    
    # 检查依赖
    deps_ok = check_dependencies()
    
    # 如果依赖不完整，提供安装选项
    if not deps_ok:
        install_dependencies()
    
    # 显示文档菜单
    docs = show_documentation_menu()
    open_documentation(docs)
    
    # 运行测试
    run_tests()
    
    # 启动应用
    start_application()
    
    print("\n🎉 欢迎使用 Chat AI！")
    print("📖 更多信息请查看 README.md 和 docs/ 目录")
    print("🔧 如需帮助，请查看项目文档或提交 Issue")

if __name__ == "__main__":
    main()
