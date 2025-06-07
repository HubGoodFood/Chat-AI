#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试澄清功能调试
调试为什么产品选择按钮没有显示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
import src.config.settings as config

def test_fuzzy_matching_debug():
    """测试模糊匹配的详细过程"""
    
    print("=== 测试模糊匹配调试 ===")
    print()
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    # 测试查询 - 选择可能有多个匹配的产品
    test_queries = [
        "蘑菇",      # 应该匹配: 农场新鲜平菇, 七彩菌菇包
        "玉米",      # 应该匹配: 新鲜农场玉米, 傻小胖糯玉米
        "蛋",        # 应该匹配: 端午特价农场土鸡蛋, 双黄海鸭蛋
        "鸡",        # 应该匹配: 农场素食散养走地萨松母鸡, 农场新鲜童子公鸡
        "有蘑菇吗",
        "玉米有吗"
    ]
    
    print(f"当前配置:")
    print(f"MIN_ACCEPTABLE_MATCH_SCORE = {config.MIN_ACCEPTABLE_MATCH_SCORE}")
    print(f"MAX_CLARIFICATION_OPTIONS = {config.MAX_CLARIFICATION_OPTIONS}")
    print()
    
    for query in test_queries:
        print(f"测试查询: '{query}'")
        print("-" * 40)
        
        # 预处理
        processed_input, original_input = chat_handler.preprocess_user_input(query, "test_user")
        print(f"预处理后: '{processed_input}'")
        
        # 意图识别
        intent = chat_handler.detect_intent(processed_input)
        print(f"识别意图: {intent}")
        
        if intent in ['inquiry_availability', 'inquiry_price_or_buy']:
            # 提取产品名称
            extracted_product = chat_handler._extract_product_name_from_query(processed_input)
            print(f"提取产品: '{extracted_product}'")
            
            # 模糊匹配
            possible_matches = product_manager.fuzzy_match_product(extracted_product)
            print(f"模糊匹配结果 (总数: {len(possible_matches)}):")
            
            for i, (key, score) in enumerate(possible_matches[:10]):  # 显示前10个
                product_details = product_manager.product_catalog.get(key, {})
                product_name = product_details.get('original_display_name', product_details.get('name', key))
                print(f"  {i+1}. {product_name} (key: {key}, 得分: {score:.3f})")
            
            # 可接受的匹配
            acceptable_matches = [(key, score) for key, score in possible_matches if score >= config.MIN_ACCEPTABLE_MATCH_SCORE]
            print(f"\n可接受的匹配 (得分 >= {config.MIN_ACCEPTABLE_MATCH_SCORE}): {len(acceptable_matches)}")
            
            for i, (key, score) in enumerate(acceptable_matches):
                product_details = product_manager.product_catalog.get(key, {})
                product_name = product_details.get('original_display_name', product_details.get('name', key))
                print(f"  {i+1}. {product_name} (key: {key}, 得分: {score:.3f})")
            
            # 澄清逻辑判断
            if len(acceptable_matches) > 1:
                top_score = acceptable_matches[0][1]
                second_score = acceptable_matches[1][1]
                
                print(f"\n澄清逻辑判断:")
                print(f"最高分: {top_score:.3f}")
                print(f"第二高分: {second_score:.3f}")
                print(f"最高分 > 0.9: {top_score > 0.9}")
                print(f"最高分 > 第二高分 * 1.5: {top_score > second_score * 1.5}")
                
                needs_clarification = not (top_score > 0.9 and top_score > second_score * 1.5)
                print(f"需要澄清: {needs_clarification}")
                
                if needs_clarification:
                    # 构建澄清候选项
                    clarification_candidates = []
                    added_candidate_display_names = set()
                    
                    for key, score in acceptable_matches:
                        if len(clarification_candidates) >= config.MAX_CLARIFICATION_OPTIONS:
                            break
                        
                        product_details_cand = product_manager.product_catalog.get(key)
                        if product_details_cand:
                            product_display_name = product_details_cand['original_display_name']
                            if product_display_name not in added_candidate_display_names:
                                clarification_candidates.append((key, product_details_cand, score))
                                added_candidate_display_names.add(product_display_name)
                    
                    print(f"\n澄清候选项 (去重后): {len(clarification_candidates)}")
                    for i, (key, details, score) in enumerate(clarification_candidates):
                        print(f"  {i+1}. {details['original_display_name']} (key: {key}, 得分: {score:.3f})")
                    
                    if len(clarification_candidates) > 1:
                        print(f"\n[OK] 应该显示澄清按钮!")
                        clarification_options_list = [{"display_text": dtls['original_display_name'], "payload": k} for k, dtls, _ in clarification_candidates]
                        print(f"澄清选项:")
                        for opt in clarification_options_list:
                            print(f"  - {opt['display_text']} (payload: {opt['payload']})")
                    else:
                        print(f"\n[FAIL] 去重后只有 {len(clarification_candidates)} 个候选项，不显示澄清按钮")
                else:
                    print(f"\n[FAIL] 最高分过于突出，不需要澄清")
            else:
                print(f"\n[FAIL] 只有 {len(acceptable_matches)} 个可接受匹配，不需要澄清")
        
        print("\n" + "=" * 60 + "\n")

def test_end_to_end_clarification():
    """端到端测试澄清功能"""
    
    print("=== 端到端澄清功能测试 ===")
    print()
    
    # 初始化组件
    product_manager = ProductManager()
    chat_handler = ChatHandler(product_manager=product_manager)
    
    test_queries = [
        "蘑菇",
        "玉米",
        "蛋",
        "鸡",
        "有蘑菇吗",
        "玉米有吗"  # This should work now
    ]
    
    for query in test_queries:
        print(f"测试查询: '{query}'")
        print("-" * 40)
        
        try:
            response = chat_handler.handle_chat_message(query, "test_user")
            
            if isinstance(response, dict) and 'clarification_options' in response:
                print(f"[OK] 返回澄清选项!")
                print(f"消息: {response.get('message', '')}")
                print(f"选项数量: {len(response.get('clarification_options', []))}")
                for i, opt in enumerate(response.get('clarification_options', []), 1):
                    print(f"  {i}. {opt.get('display_text', '')} (payload: {opt.get('payload', '')})")
            elif isinstance(response, str):
                print(f"[FAIL] 返回普通字符串回复")
                print(f"回复: {response[:100]}...")
            else:
                print(f"[FAIL] 返回其他类型: {type(response)}")

        except Exception as e:
            print(f"[ERROR] 处理出错: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    test_fuzzy_matching_debug()
    test_end_to_end_clarification()
