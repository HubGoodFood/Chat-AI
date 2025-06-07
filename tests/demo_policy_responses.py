#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示优化后的政策回复效果
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.policy.manager import PolicyManager
from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

def demo_policy_responses():
    """演示政策回复效果"""
    print("🎭 演示优化后的政策回复效果")
    print("=" * 60)
    
    # 初始化组件
    product_manager = ProductManager()
    product_manager.load_product_data()
    policy_manager = PolicyManager()
    cache_manager = CacheManager()
    chat_handler = ChatHandler(product_manager, policy_manager, cache_manager)
    
    # 测试查询列表
    test_queries = [
        "你们的拼台理念是什么？",
        "配送时间和费用怎么算？",
        "支付方式有哪些？",
        "取货点在哪里？",
        "质量有问题怎么办？",
        "群规有什么要求？",
        "社区互助是怎么回事？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 查询 {i}: {query}")
        print("-" * 50)
        
        try:
            response = chat_handler.handle_chat_message(query, f'demo_user_{i}')
            
            if isinstance(response, str):
                print(response)
            elif isinstance(response, dict):
                if 'message' in response:
                    print(response['message'])
                else:
                    print(f"字典回复: {response}")
            else:
                print(f"其他类型回复: {type(response)}")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 政策回复演示完成！")

def compare_old_vs_new():
    """对比优化前后的效果"""
    print("\n📊 优化效果对比")
    print("=" * 60)
    
    print("🔄 优化前的问题:")
    print("• 政策内容不完整，缺少拼台宗旨、取货信息、社区互助等重要分类")
    print("• 语言表达过于简化，缺少温度和人情味")
    print("• 信息分散，用户难以快速找到需要的信息")
    print("• 代码中定义了8个分类，但JSON中只有5个")
    
    print("\n✅ 优化后的改进:")
    print("• 补全了所有8个政策分类，内容更加完整")
    print("• 优化了语言表达，更加自然友好，富有温度")
    print("• 重新组织了信息结构，逻辑更清晰")
    print("• 增加了详细的操作指南和注意事项")
    print("• 强化了社区互助和人文关怀的理念")
    
    print("\n📈 具体数据对比:")
    
    policy_manager = PolicyManager()
    sections = policy_manager.get_all_sections()
    
    print(f"• 政策分类数量: 5 → {len(sections)}")
    print(f"• 政策版本: 1.0.0 → {policy_manager.get_policy_version()}")
    print(f"• 最后更新: 2025-06-04 → {policy_manager.get_policy_last_updated()}")
    
    # 统计各分类的条目数
    total_items = 0
    for section in sections:
        items = policy_manager.get_policy_section(section)
        total_items += len(items)
        print(f"• {section}: {len(items)} 条政策")
    
    print(f"• 总政策条目数: 约15条 → {total_items}条")

def main():
    """主函数"""
    print("🚀 政策优化效果展示")
    print("=" * 60)
    
    # 演示政策回复
    demo_policy_responses()
    
    # 对比优化效果
    compare_old_vs_new()
    
    print("\n🎯 优化总结:")
    print("✅ 政策内容更加完整和详细")
    print("✅ 语言表达更加自然友好")
    print("✅ 信息结构更加清晰合理")
    print("✅ 语义搜索效果更加准确")
    print("✅ 用户体验显著提升")

if __name__ == "__main__":
    main()
