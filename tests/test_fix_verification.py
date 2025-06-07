#!/usr/bin/env python3
"""
验证查询解析bug修复效果
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.app.policy.manager import PolicyManager
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

def test_query_extraction():
    """测试查询提取功能"""
    
    print("测试查询提取功能:")
    print("=" * 50)
    
    # 初始化必要的组件
    product_manager = ProductManager()
    policy_manager = PolicyManager()
    chat_handler = ChatHandler(product_manager, policy_manager)
    
    # 测试用例
    test_cases = [
        ("卖不卖草莓", "草莓"),
        ("有没有苹果", "苹果"),
        ("有草莓吗", "草莓"),
        ("草莓多少钱", "草莓"),
        ("我要买西瓜", "西瓜"),
        ("你们有香蕉吗", "香蕉"),
        ("草莓", "草莓"),  # 单独产品名称
        ("苹果怎么卖", "苹果"),
        ("西瓜一斤多少", "西瓜")
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for query, expected in test_cases:
        extracted = chat_handler._extract_product_name_from_query(query)
        is_correct = extracted == expected
        status = "[OK]" if is_correct else "[FAIL]"
        
        print(f"{status} '{query}' -> 提取: '{extracted}' (期望: '{expected}')")
        
        if is_correct:
            success_count += 1
        else:
            print(f"      详细: 期望提取'{expected}'，实际得到'{extracted}'")
    
    accuracy = success_count / total_count
    print(f"\n提取准确率: {accuracy:.3f} ({success_count}/{total_count})")
    
    return accuracy >= 0.8

def test_end_to_end_scenario():
    """测试端到端场景"""
    
    print("\n测试端到端场景:")
    print("=" * 50)
    
    # 初始化组件
    product_manager = ProductManager()
    policy_manager = PolicyManager()
    chat_handler = ChatHandler(product_manager, policy_manager)
    
    # 模拟用户查询"卖不卖草莓"
    user_input = "卖不卖草莓"
    user_id = "test_user"
    
    print(f"用户输入: '{user_input}'")
    
    try:
        # 处理聊天消息
        response = chat_handler.handle_chat_message(user_input, user_id)
        
        print(f"系统响应类型: {type(response)}")
        
        if isinstance(response, str):
            print(f"系统响应: {response[:200]}...")
            
            # 检查响应是否包含草莓相关信息
            if "草莓" in response and "不草莓" not in response:
                print("[OK] 系统正确识别了草莓，没有出现'不草莓'")
                return True
            elif "不草莓" in response:
                print("[FAIL] 系统响应中仍然包含错误的'不草莓'")
                return False
            else:
                print("[WARNING] 系统响应中没有包含草莓信息，可能是其他问题")
                return False
        elif isinstance(response, dict):
            print(f"系统响应: {response}")
            # 对于字典响应（如澄清选项），检查是否包含草莓
            message = response.get('message', '')
            if "草莓" in message and "不草莓" not in message:
                print("[OK] 系统正确识别了草莓")
                return True
            else:
                print("[FAIL] 系统响应有问题")
                return False
        else:
            print(f"[ERROR] 意外的响应类型: {type(response)}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 处理过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fuzzy_matching():
    """测试模糊匹配功能"""
    
    print("\n测试模糊匹配功能:")
    print("=" * 50)
    
    # 初始化产品管理器
    product_manager = ProductManager()
    
    # 测试用例
    test_queries = [
        "草莓",      # 应该找到草莓
        "不草莓",    # 不应该找到任何产品
        "苹果",      # 应该找到苹果
        "西瓜",      # 应该找到西瓜
    ]
    
    for query in test_queries:
        matches = product_manager.fuzzy_match_product(query)
        print(f"查询 '{query}' 找到 {len(matches)} 个匹配:")
        
        for i, (product_key, score) in enumerate(matches[:3]):  # 只显示前3个
            product_details = product_manager.product_catalog.get(product_key, {})
            product_name = product_details.get('name', product_key)
            print(f"  {i+1}. {product_name} (得分: {score:.3f})")
        
        if query == "不草莓" and len(matches) > 0:
            print(f"  [WARNING] '不草莓' 不应该匹配到任何产品，但找到了 {len(matches)} 个")
        elif query == "草莓" and len(matches) == 0:
            print(f"  [WARNING] '草莓' 应该匹配到产品，但没有找到")

def main():
    """主测试函数"""
    
    print("验证查询解析bug修复效果")
    print("=" * 60)
    
    # 测试1: 查询提取功能
    success1 = test_query_extraction()
    
    # 测试2: 端到端场景
    success2 = test_end_to_end_scenario()
    
    # 测试3: 模糊匹配
    test_fuzzy_matching()
    
    print("\n" + "=" * 60)
    print("修复验证结果:")
    
    if success1 and success2:
        print("[OK] 修复成功！")
        print("- 查询提取功能正常工作")
        print("- '卖不卖草莓' 现在被正确处理为 '草莓'")
        print("- 端到端测试通过")
        print("- 不再出现 '不草莓' 的错误")
        return True
    else:
        print("[FAIL] 修复不完整")
        if not success1:
            print("- 查询提取功能有问题")
        if not success2:
            print("- 端到端测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
