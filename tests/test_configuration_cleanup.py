#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件清理验证测试
验证配置文件清理后的项目状态
"""

import os
import sys
import subprocess
from pathlib import Path

def test_configuration_cleanup():
    """验证配置文件清理的结果"""
    print("开始配置文件清理验证测试...")

    # 项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    results = []

    # 1. 验证重复文件已删除
    print("\n1. 验证重复配置文件已删除...")
    
    duplicate_files = [
        "config/deployment/gunicorn_optimized.conf.py",
        "config/deployment/render_optimized.yaml",
        "requirements_lightweight.txt"
    ]
    
    for file_path in duplicate_files:
        if os.path.exists(file_path):
            results.append(f"X 重复文件仍存在: {file_path}")
        else:
            results.append(f"OK 重复文件已删除: {file_path}")

    # 2. 验证主要配置文件存在
    print("\n2. 验证主要配置文件存在...")

    main_files = [
        "requirements.txt",
        "gunicorn.conf.py",
        "render.yaml"
    ]

    for file_path in main_files:
        if os.path.exists(file_path):
            results.append(f"OK 主要配置文件存在: {file_path}")
        else:
            results.append(f"X 主要配置文件缺失: {file_path}")

    # 3. 验证备份文件存在
    print("\n3. 验证备份文件存在...")

    backup_files = [
        "config/backup/requirements_original.txt",
        "config/backup/README.md"
    ]

    for file_path in backup_files:
        if os.path.exists(file_path):
            results.append(f"OK 备份文件存在: {file_path}")
        else:
            results.append(f"X 备份文件缺失: {file_path}")

    # 4. 验证requirements.txt内容
    print("\n4. 验证requirements.txt内容...")
    
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "轻量级依赖配置" in content:
            results.append("OK requirements.txt是轻量级版本")
        else:
            results.append("X requirements.txt不是轻量级版本")

        # 检查是否有未注释的重型ML库依赖
        lines = content.split('\n')
        heavy_libs_found = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if 'torch' in line or 'transformers' in line:
                    heavy_libs_found.append(line)

        if not heavy_libs_found:
            results.append("OK 重型ML库已移除")
        else:
            results.append(f"X 仍包含重型ML库: {heavy_libs_found}")

        if "redis" in content and "psutil" in content:
            results.append("OK 包含优化库")
        else:
            results.append("X 缺少优化库")

    except Exception as e:
        results.append(f"X 读取requirements.txt失败: {e}")

    # 5. 验证空目录已删除
    print("\n5. 验证空目录已删除...")

    if not os.path.exists("config/deployment"):
        results.append("OK 空的config/deployment目录已删除")
    else:
        results.append("X config/deployment目录仍存在")

    # 6. 验证依赖可以正常安装
    print("\n6. 验证依赖可以正常解析...")
    
    try:
        # 使用pip-compile检查依赖
        result = subprocess.run([
            sys.executable, "-m", "pip", "check"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            results.append("OK 当前依赖状态正常")
        else:
            results.append(f"WARN 依赖检查警告: {result.stdout}")

    except subprocess.TimeoutExpired:
        results.append("WARN 依赖检查超时")
    except Exception as e:
        results.append(f"WARN 依赖检查失败: {e}")

    # 输出结果
    print("\n" + "="*60)
    print("配置文件清理验证结果:")
    print("="*60)

    success_count = 0
    warning_count = 0
    error_count = 0

    for result in results:
        print(result)
        if result.startswith("OK"):
            success_count += 1
        elif result.startswith("WARN"):
            warning_count += 1
        elif result.startswith("X"):
            error_count += 1

    print("\n" + "="*60)
    print(f"统计结果:")
    print(f"成功: {success_count}")
    print(f"警告: {warning_count}")
    print(f"错误: {error_count}")
    print(f"成功率: {success_count/(success_count+warning_count+error_count)*100:.1f}%")

    if error_count == 0:
        print("\n配置文件清理验证通过！")
        return True
    else:
        print(f"\n发现 {error_count} 个问题需要修复")
        return False

if __name__ == "__main__":
    success = test_configuration_cleanup()
    sys.exit(0 if success else 1)
