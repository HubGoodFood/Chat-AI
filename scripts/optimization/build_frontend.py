#!/usr/bin/env python3
"""
前端构建脚本
自动化执行所有优化步骤
"""

import subprocess
import sys
import time
from pathlib import Path

def run_script(script_path, description):
    """运行优化脚本"""
    print(f"\n{'='*50}")
    print(f"运行: {description}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path], 
            capture_output=True, 
            text=True,
            cwd=Path.cwd()
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"成功: {description} 完成 (耗时: {elapsed_time:.2f}秒)")
            return True
        else:
            print(f"失败: {description} 失败")
            print("错误输出:")
            print(result.stderr)
            if result.stdout:
                print("标准输出:")
                print(result.stdout)
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"异常: 运行 {script_path} 时发生异常: {e}")
        print(f"耗时: {elapsed_time:.2f}秒")
        return False

def check_dependencies():
    """检查依赖"""
    print("检查依赖...")

    # 检查Python版本
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        return False

    print(f"Python版本: {sys.version}")

    # 检查Pillow（图片优化需要）
    try:
        import PIL
        print(f"Pillow版本: {PIL.__version__}")
    except ImportError:
        print("警告: 未安装Pillow，将跳过图片优化")
        print("安装命令: pip install Pillow")

    return True

def run_optimization():
    """运行所有优化步骤"""
    print("前端性能优化构建开始")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 优化脚本列表
    optimization_steps = [
        ("scripts/optimization/optimize_css.py", "CSS文件优化"),
        ("scripts/optimization/optimize_js.py", "JavaScript文件优化"),
        ("scripts/optimization/optimize_images.py", "图片文件优化"),
        ("scripts/optimization/generate_manifest.py", "生成资源清单")
    ]
    
    success_count = 0
    total_steps = len(optimization_steps)
    
    for script_path, description in optimization_steps:
        if Path(script_path).exists():
            if run_script(script_path, description):
                success_count += 1
            else:
                print(f"警告: {description} 失败，但继续执行其他步骤...")
        else:
            print(f"错误: 脚本文件不存在: {script_path}")

    # 总结
    print(f"\n{'='*60}")
    print(f"构建总结")
    print(f"{'='*60}")
    print(f"成功步骤: {success_count}/{total_steps}")
    print(f"完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if success_count == total_steps:
        print("前端优化构建完全成功！")
        print("\n后续步骤:")
        print("1. 运行性能测试验证优化效果")
        print("2. 更新Flask应用以使用优化后的文件")
        print("3. 配置生产环境的缓存策略")
        return True
    elif success_count > 0:
        print("警告: 部分优化步骤成功，请检查失败的步骤")
        return False
    else:
        print("错误: 所有优化步骤都失败了")
        return False

def show_help():
    """显示帮助信息"""
    print("""
🔧 前端构建脚本使用说明

功能:
  自动执行所有前端性能优化步骤

包含的优化:
  1. CSS文件压缩和Gzip
  2. JavaScript文件压缩和Gzip  
  3. 图片优化和WebP转换
  4. 资源版本管理清单生成

使用方法:
  python scripts/optimization/build_frontend.py

依赖:
  - Python 3.6+
  - Pillow (可选，用于图片优化)

输出:
  - *.min.css / *.min.js (压缩文件)
  - *.gz (Gzip压缩文件)
  - *.webp (WebP图片)
  - manifest.json (资源清单)
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_help()
    else:
        success = run_optimization()
        if not success:
            exit(1)
