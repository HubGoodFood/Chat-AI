#!/usr/bin/env python3
"""
测试查询解析bug：验证"卖不卖草莓"被错误处理为"不草莓"的问题
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import settings as config

def test_current_stopword_removal():
    """测试当前的停用词移除逻辑"""
    
    print("测试当前的停用词移除逻辑:")
    print("=" * 50)
    
    # 模拟当前handler.py中的逻辑
    test_queries = [
        "卖不卖草莓",
        "有没有苹果",
        "有草莓吗",
        "你们卖什么",
        "草莓多少钱",
        "我要买草莓"
    ]
    
    # 获取所有停用词（模拟handler.py中的逻辑）
    all_stopwords = (config.PRICE_QUERY_KEYWORDS +
                     config.BUY_INTENT_KEYWORDS +
                     config.GENERAL_QUERY_KEYWORDS +
                     config.POLICY_KEYWORD_MAP.get('return_policy', []) +
                     config.POLICY_KEYWORD_MAP.get('shipping_policy', []) +
                     ["你们", "我们", "我", "你", "他", "她", "它", "的", "地", "得", "了", "着", "过", "吗", "呢", "吧", "呀", "啊", "什么", "是", "不是", "想", "要", "请问", "那个", "这个"])
    
    print(f"停用词列表: {all_stopwords}")
    print()
    
    for query in test_queries:
        query_for_matching = query
        
        # 当前的错误逻辑：直接使用str.replace
        for stopword in set(all_stopwords):
            query_for_matching = query_for_matching.replace(stopword, '')
        query_for_matching = query_for_matching.strip()
        
        print(f"原始查询: '{query}' -> 处理后: '{query_for_matching}'")
        
        # 检查是否出现问题
        if query == "卖不卖草莓" and query_for_matching == "不草莓":
            print("  [BUG CONFIRMED] 发现问题：'卖不卖草莓' 被错误处理为 '不草莓'")
        elif "不" in query_for_matching and query_for_matching != query:
            print(f"  [POTENTIAL ISSUE] 可能的问题：包含'不'字")

def test_improved_stopword_removal():
    """测试改进的停用词移除逻辑"""
    
    print("\n测试改进的停用词移除逻辑:")
    print("=" * 50)
    
    import re
    
    test_queries = [
        "卖不卖草莓",
        "有没有苹果", 
        "有草莓吗",
        "你们卖什么",
        "草莓多少钱",
        "我要买草莓"
    ]
    
    # 改进的停用词移除逻辑
    def improved_query_cleaning(query):
        """改进的查询清洗逻辑"""
        
        # 定义需要移除的模式（使用正则表达式）
        patterns_to_remove = [
            r'^卖不卖',      # 开头的"卖不卖"
            r'^有没有',      # 开头的"有没有"
            r'^有',          # 开头的"有"
            r'吗$',          # 结尾的"吗"
            r'呢$',          # 结尾的"呢"
            r'啊$',          # 结尾的"啊"
            r'多少钱',       # "多少钱"
            r'价格',         # "价格"
            r'我要',         # "我要"
            r'你们',         # "你们"
        ]
        
        cleaned_query = query
        for pattern in patterns_to_remove:
            cleaned_query = re.sub(pattern, '', cleaned_query)
        
        return cleaned_query.strip()
    
    for query in test_queries:
        cleaned = improved_query_cleaning(query)
        print(f"原始查询: '{query}' -> 改进处理: '{cleaned}'")
        
        # 验证结果
        if query == "卖不卖草莓":
            if cleaned == "草莓":
                print("  [OK] 正确提取产品名称")
            else:
                print(f"  [FAIL] 期望'草莓'，实际得到'{cleaned}'")

def test_regex_based_extraction():
    """测试基于正则表达式的产品名称提取"""
    
    print("\n测试基于正则表达式的产品名称提取:")
    print("=" * 50)
    
    import re
    
    # 常见的产品名称
    common_products = ["草莓", "苹果", "西瓜", "香蕉", "橙子", "梨", "葡萄", "桃子", "樱桃", "芒果"]
    
    # 构建产品名称的正则表达式
    product_pattern = '|'.join(common_products)
    
    test_queries = [
        "卖不卖草莓",
        "有没有苹果",
        "有草莓吗", 
        "草莓多少钱",
        "我要买西瓜",
        "你们有香蕉吗"
    ]
    
    def extract_product_name(query):
        """使用正则表达式提取产品名称"""
        match = re.search(f'({product_pattern})', query)
        return match.group(1) if match else None
    
    for query in test_queries:
        product = extract_product_name(query)
        print(f"查询: '{query}' -> 提取的产品: '{product}'")

if __name__ == "__main__":
    test_current_stopword_removal()
    test_improved_stopword_removal()
    test_regex_based_extraction()
