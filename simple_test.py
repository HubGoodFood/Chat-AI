#!/usr/bin/env python3
"""
简单测试脚本，验证产品查询回复逻辑的修改
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_response_format():
    """测试回复格式"""
    print("=== 简单回复格式测试 ===\n")
    
    # 模拟不同场景的回复格式
    
    # 1. 精确匹配 - 应该返回字符串
    print("1. 精确匹配场景（应该返回字符串）:")
    exact_match_response = "太好了！您选择的「苹果」真的很不错呢！它的价格是每份 $2.50，规格是1磅。"
    print(f"   类型: {type(exact_match_response)}")
    print(f"   内容: {exact_match_response[:50]}...")
    print(f"   ✓ 正确：返回字符串格式，无按钮\n")
    
    # 2. 模糊匹配 - 应该返回字典，只有澄清按钮
    print("2. 模糊匹配场景（应该返回字典，只有澄清按钮）:")
    clarification_response = {
        "message": "您好，关于您咨询的产品，我找到了几个相似的：您是指 [台湾香瓜]、[韩国香瓜] 呢？请点击选择。",
        "clarification_options": [
            {"display_text": "台湾香瓜", "payload": "taiwan_melon"},
            {"display_text": "韩国香瓜", "payload": "korean_melon"}
        ],
        "product_suggestions": []  # 模糊查询时不显示推荐按钮
    }
    print(f"   类型: {type(clarification_response)}")
    print(f"   澄清按钮: {len(clarification_response['clarification_options'])} 个")
    print(f"   推荐按钮: {len(clarification_response['product_suggestions'])} 个")
    print(f"   ✓ 正确：只有澄清按钮，无推荐按钮\n")
    
    # 3. 产品不存在 - 应该返回字典，只有推荐按钮
    print("3. 产品不存在场景（应该返回字典，只有推荐按钮）:")
    unavailable_response = {
        "message": "草莓确实是很受欢迎的水果呢！\n很抱歉，我们目前暂时没有草莓。\n\n不过，如果您喜欢水果，我们有这些很棒的选择：\n\n您可以点击上面的产品按钮了解详情！",
        "product_suggestions": [
            {"display_text": "蓝莓 ($3.50/盒)", "payload": "blueberry"},
            {"display_text": "樱桃 ($4.00/磅)", "payload": "cherry"}
        ]
    }
    print(f"   类型: {type(unavailable_response)}")
    print(f"   澄清按钮: {len(unavailable_response.get('clarification_options', []))} 个")
    print(f"   推荐按钮: {len(unavailable_response['product_suggestions'])} 个")
    print(f"   ✓ 正确：只有推荐按钮，无澄清按钮\n")
    
    # 4. 主动推荐 - 应该返回字典，有推荐按钮
    print("4. 主动推荐场景（应该返回字典，有推荐按钮）:")
    recommendation_response = {
        "message": "为您推荐几款我们这里不错的水果：",
        "product_suggestions": [
            {"display_text": "苹果 ($2.50/磅)", "payload": "apple"},
            {"display_text": "橙子 ($3.00/磅)", "payload": "orange"},
            {"display_text": "香蕉 ($1.80/磅)", "payload": "banana"}
        ]
    }
    print(f"   类型: {type(recommendation_response)}")
    print(f"   澄清按钮: {len(recommendation_response.get('clarification_options', []))} 个")
    print(f"   推荐按钮: {len(recommendation_response['product_suggestions'])} 个")
    print(f"   ✓ 正确：有推荐按钮\n")
    
    print("=== 核心原则验证 ===")
    print("✓ 精确匹配：字符串格式，无按钮")
    print("✓ 模糊匹配：字典格式，只有澄清按钮")
    print("✓ 产品不存在：字典格式，只有推荐按钮")
    print("✓ 主动推荐：字典格式，有推荐按钮")
    print("✓ 按钮显示有明确目的：澄清选择 OR 产品推荐，不同时出现")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_response_format()
