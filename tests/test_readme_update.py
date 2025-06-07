#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
README.md 更新验证测试
验证 README.md 文件是否正确反映了最新的项目状态
"""

import os
import sys
from pathlib import Path

def test_readme_update():
    """验证 README.md 更新的结果"""
    print("开始 README.md 更新验证测试...")
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    readme_path = project_root / "README.md"
    
    if not readme_path.exists():
        print("X README.md 文件不存在")
        return False
    
    # 读取 README.md 内容
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"X 读取 README.md 失败: {e}")
        return False
    
    results = []
    
    # 1. 验证轻量级优化特性部分
    print("\n1. 验证轻量级优化特性...")
    
    if "轻量级优化特性" in content:
        results.append("OK 包含轻量级优化特性部分")
    else:
        results.append("X 缺少轻量级优化特性部分")
    
    if "98.6%" in content and "50MB" in content:
        results.append("OK 包含正确的性能数据")
    else:
        results.append("X 缺少性能数据")
    
    # 2. 验证安装说明更新
    print("\n2. 验证安装说明...")
    
    if "requirements_lightweight.txt" not in content:
        results.append("OK 已移除 requirements_lightweight.txt 引用")
    else:
        results.append("X 仍包含 requirements_lightweight.txt 引用")
    
    if "config/backup/requirements_original.txt" in content:
        results.append("OK 包含备份文件说明")
    else:
        results.append("X 缺少备份文件说明")
    
    # 3. 验证性能对比表格
    print("\n3. 验证性能对比表格...")
    
    if "性能对比" in content and "轻量级版本（当前）" in content:
        results.append("OK 包含性能对比表格")
    else:
        results.append("X 缺少性能对比表格")
    
    # 4. 验证配置版本说明
    print("\n4. 验证配置版本说明...")
    
    if "配置版本说明" in content and "回滚到原版重型配置" in content:
        results.append("OK 包含配置版本说明")
    else:
        results.append("X 缺少配置版本说明")
    
    # 5. 验证项目结构更新
    print("\n5. 验证项目结构...")
    
    if "config/deployment/" not in content:
        results.append("OK 已移除 config/deployment/ 引用")
    else:
        results.append("X 仍包含 config/deployment/ 引用")
    
    if "config/backup/" in content:
        results.append("OK 包含 config/backup/ 说明")
    else:
        results.append("X 缺少 config/backup/ 说明")
    
    # 6. 验证部署指南
    print("\n6. 验证部署指南...")
    
    if "部署指南" in content and "Render 部署" in content:
        results.append("OK 包含部署指南")
    else:
        results.append("X 缺少部署指南")
    
    if "Starter计划" in content:
        results.append("OK 包含 Starter 计划说明")
    else:
        results.append("X 缺少 Starter 计划说明")
    
    # 7. 验证最新改进部分
    print("\n7. 验证最新改进...")
    
    if "v2.1 - 配置清理和轻量级优化" in content:
        results.append("OK 包含最新改进说明")
    else:
        results.append("X 缺少最新改进说明")
    
    if "配置清理总结" in content:
        results.append("OK 包含配置清理总结链接")
    else:
        results.append("X 缺少配置清理总结链接")
    
    # 输出结果
    print("\n" + "="*60)
    print("README.md 更新验证结果:")
    print("="*60)
    
    success_count = 0
    error_count = 0
    
    for result in results:
        print(result)
        if result.startswith("OK"):
            success_count += 1
        elif result.startswith("X"):
            error_count += 1
    
    print("\n" + "="*60)
    print(f"统计结果:")
    print(f"成功: {success_count}")
    print(f"错误: {error_count}")
    print(f"成功率: {success_count/(success_count+error_count)*100:.1f}%")
    
    if error_count == 0:
        print("\nREADME.md 更新验证通过！")
        return True
    else:
        print(f"\n发现 {error_count} 个问题需要修复")
        return False

if __name__ == "__main__":
    success = test_readme_update()
    sys.exit(0 if success else 1)
