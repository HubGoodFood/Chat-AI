#!/usr/bin/env python3
"""
Render部署修复脚本
解决Redis连接问题和其他常见部署问题
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path

def print_status(message, status="INFO"):
    """打印状态信息"""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m", 
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['RESET']}")

def check_render_yaml():
    """检查render.yaml配置"""
    print_status("检查render.yaml配置...")
    
    render_yaml_path = Path("render.yaml")
    if not render_yaml_path.exists():
        print_status("render.yaml文件不存在", "ERROR")
        return False
    
    try:
        with open(render_yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查环境变量
        env_vars = {}
        if 'services' in config and len(config['services']) > 0:
            service = config['services'][0]
            if 'envVars' in service:
                for var in service['envVars']:
                    env_vars[var['key']] = var['value']
        
        # 检查Redis配置
        redis_enabled = env_vars.get('REDIS_ENABLED', 'true').lower()
        if redis_enabled == 'true':
            print_status("发现Redis已启用，但Render环境可能没有Redis服务", "WARNING")
            print_status("建议禁用Redis使用内存缓存", "WARNING")
            return False
        else:
            print_status("Redis已正确禁用", "SUCCESS")
        
        # 检查其他重要配置
        model_type = env_vars.get('MODEL_TYPE', 'full')
        if model_type != 'lightweight':
            print_status(f"模型类型为{model_type}，建议使用lightweight", "WARNING")
        
        print_status("render.yaml配置检查完成", "SUCCESS")
        return True
        
    except Exception as e:
        print_status(f"读取render.yaml失败: {e}", "ERROR")
        return False

def fix_render_yaml():
    """修复render.yaml配置"""
    print_status("修复render.yaml配置...")
    
    render_yaml_path = Path("render.yaml")
    if not render_yaml_path.exists():
        print_status("render.yaml文件不存在，无法修复", "ERROR")
        return False
    
    try:
        with open(render_yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有REDIS_ENABLED配置
        if 'REDIS_ENABLED' not in content:
            print_status("添加REDIS_ENABLED=false配置...")
            
            # 在envVars部分添加Redis配置
            redis_config = """      # Redis配置 - 在Render环境中禁用Redis，使用内存缓存
      - key: REDIS_ENABLED
        value: false
      - key: MONITORING_ENABLED
        value: true"""
            
            # 查找插入位置（在DEEPSEEK_API_KEY之前）
            if 'DEEPSEEK_API_KEY' in content:
                content = content.replace(
                    '      # API密钥从Render环境变量中获取',
                    f'{redis_config}\n      # API密钥从Render环境变量中获取'
                )
            else:
                # 如果没有DEEPSEEK_API_KEY，在envVars末尾添加
                content = content.replace(
                    '        value: true',
                    f'        value: true\n{redis_config}',
                    1  # 只替换第一个匹配项
                )
            
            with open(render_yaml_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_status("render.yaml已更新", "SUCCESS")
        else:
            print_status("REDIS_ENABLED配置已存在", "INFO")
        
        return True
        
    except Exception as e:
        print_status(f"修复render.yaml失败: {e}", "ERROR")
        return False

def check_git_status():
    """检查Git状态"""
    print_status("检查Git状态...")
    
    try:
        # 检查是否有未提交的更改
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print_status("发现未提交的更改:", "INFO")
            print(result.stdout)
            return True
        else:
            print_status("没有未提交的更改", "INFO")
            return False
            
    except subprocess.CalledProcessError as e:
        print_status(f"检查Git状态失败: {e}", "ERROR")
        return False

def commit_and_push():
    """提交并推送更改"""
    print_status("提交并推送更改...")
    
    try:
        # 添加render.yaml到暂存区
        subprocess.run(['git', 'add', 'render.yaml'], check=True)
        
        # 提交更改
        subprocess.run(['git', 'commit', '-m', '修复Render部署Redis连接问题'], check=True)
        
        # 推送到远程仓库
        subprocess.run(['git', 'push'], check=True)
        
        print_status("更改已成功推送到远程仓库", "SUCCESS")
        return True
        
    except subprocess.CalledProcessError as e:
        print_status(f"Git操作失败: {e}", "ERROR")
        return False

def main():
    """主函数"""
    print_status("开始Render部署修复...")
    print_status("=" * 50)
    
    # 检查当前配置
    if check_render_yaml():
        print_status("配置检查通过，无需修复", "SUCCESS")
    else:
        print_status("需要修复配置", "WARNING")
        
        # 修复配置
        if not fix_render_yaml():
            print_status("配置修复失败", "ERROR")
            sys.exit(1)
    
    # 检查Git状态
    has_changes = check_git_status()
    
    if has_changes:
        response = input("\n是否要提交并推送更改到远程仓库？(y/n): ")
        if response.lower() in ['y', 'yes', '是']:
            if commit_and_push():
                print_status("修复完成！Render将自动重新部署", "SUCCESS")
                print_status("请在Render Dashboard中查看部署状态", "INFO")
            else:
                print_status("推送失败，请手动提交更改", "ERROR")
        else:
            print_status("请手动提交更改:", "INFO")
            print("git add render.yaml")
            print("git commit -m '修复Render部署Redis连接问题'")
            print("git push")
    
    print_status("=" * 50)
    print_status("修复脚本执行完成", "SUCCESS")
    
    # 显示后续步骤
    print("\n📋 后续步骤:")
    print("1. 在Render Dashboard中查看部署日志")
    print("2. 确认没有Redis连接错误")
    print("3. 测试应用功能是否正常")
    print("4. 如有问题，查看 docs/deployment/render_troubleshooting.md")

if __name__ == "__main__":
    main()
