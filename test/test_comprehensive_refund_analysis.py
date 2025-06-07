#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退货意图识别系统全面分析测试
深入测试各种实际用户场景，发现潜在问题和边缘情况
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.chat.handler import ChatHandler
from src.app.intent.lightweight_classifier import LightweightIntentClassifier
from src.app.products.manager import ProductManager

class RefundIntentAnalyzer:
    def __init__(self):
        self.product_manager = ProductManager()
        self.chat_handler = ChatHandler(self.product_manager)
        self.intent_classifier = LightweightIntentClassifier()
        
        # 测试结果统计
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'failed_cases': []
        }
    
    def test_category(self, category_name, test_cases):
        """测试特定类别的用例"""
        print(f"\n=== {category_name} ===")
        category_passed = 0
        category_total = len(test_cases)
        
        for test_input, expected_intent, description in test_cases:
            actual_intent = self.chat_handler.detect_intent(test_input)
            classifier_intent = self.intent_classifier.predict(test_input)
            
            is_success = actual_intent == expected_intent
            status = "PASS" if is_success else "FAIL"
            
            print(f"{status} \"{test_input}\" -> {actual_intent} (期望: {expected_intent})")
            print(f"     分类器: {classifier_intent} | 描述: {description}")
            
            self.results['total_tests'] += 1
            if is_success:
                self.results['passed'] += 1
                category_passed += 1
            else:
                self.results['failed'] += 1
                self.results['failed_cases'].append({
                    'category': category_name,
                    'input': test_input,
                    'expected': expected_intent,
                    'actual': actual_intent,
                    'classifier': classifier_intent,
                    'description': description
                })
        
        print(f"类别成功率: {category_passed}/{category_total} ({category_passed/category_total*100:.1f}%)")
        return category_passed == category_total
    
    def run_comprehensive_analysis(self):
        """运行全面分析"""
        print("退货意图识别系统全面分析")
        print("=" * 60)
        
        # 1. 真实用户场景测试
        real_user_scenarios = [
            ("这个苹果有虫子，能退吗", "refund_request", "质量问题+退货询问"),
            ("买的香蕉太生了，怎么退", "refund_request", "成熟度问题+退货询问"),
            ("西瓜不甜，可以退货吗", "refund_request", "口味问题+退货询问"),
            ("这个芒果烂了一半，要退货", "refund_request", "部分损坏+退货声明"),
            ("葡萄酸得不行，能不能退", "refund_request", "口味问题+退货询问"),
            ("买错品种了，想退货", "refund_request", "购买错误+退货意愿"),
            ("这批水果都不新鲜，全退", "refund_request", "批量质量问题+退货"),
            ("收到的时候就坏了，怎么办", "refund_request", "收货时损坏+求助"),
            ("不喜欢这个味道，能退吗", "refund_request", "个人偏好+退货询问"),
            ("太贵了，想退掉重新买", "refund_request", "价格原因+退货"),
        ]
        
        # 2. 产品名称+退货组合测试
        product_refund_combinations = [
            ("苹果坏了", "refund_request", "产品+质量问题"),
            ("香蕉烂了", "refund_request", "产品+质量问题"),
            ("西瓜不好", "refund_request", "产品+质量评价"),
            ("芒果有问题", "refund_request", "产品+问题描述"),
            ("葡萄变质", "refund_request", "产品+变质"),
            ("桃子软了", "refund_request", "产品+状态变化"),
            ("橙子酸", "refund_request", "产品+口味问题"),
            ("草莓坏掉了", "refund_request", "产品+损坏"),
            ("蓝莓不甜", "refund_request", "产品+口味问题"),
            ("樱桃有虫", "refund_request", "产品+质量问题"),
        ]
        
        # 3. 语言表达多样性测试
        expression_variety = [
            ("能不能退货啊", "refund_request", "口语化退货询问"),
            ("可以退不", "refund_request", "简化退货询问"),
            ("退得了吗", "refund_request", "方言式退货询问"),
            ("这个退不退得了", "refund_request", "复杂退货询问"),
            ("想退掉这个", "refund_request", "简单退货意愿"),
            ("不要了，退吧", "refund_request", "放弃+退货"),
            ("退回去行吗", "refund_request", "退货可行性询问"),
            ("能换个好的吗", "refund_request", "换货请求"),
            ("这个有问题，换一下", "refund_request", "问题+换货"),
            ("质量不行，退了", "refund_request", "质量评价+退货决定"),
        ]
        
        # 4. 边缘情况和容易混淆的查询
        edge_cases = [
            ("退货政策是什么", "inquiry_policy", "政策查询，不是退货请求"),
            ("你们的退货规定", "inquiry_policy", "规定查询，不是退货请求"),
            ("退货流程怎么样", "inquiry_policy", "流程查询，可能混淆"),
            ("退货", "refund_request", "单独退货词汇"),
            ("退", "refund_request", "单独退字"),
            ("怎么办", "unknown", "单独求助，无具体上下文"),
            ("有问题", "unknown", "单独问题描述，无退货意图"),
            ("不好", "unknown", "单独评价，无退货意图"),
            ("坏了", "unknown", "单独状态描述，无退货意图"),
            ("质量问题", "unknown", "单独质量描述，无退货意图"),
        ]
        
        # 5. 复杂场景测试
        complex_scenarios = [
            ("昨天买的那个芒果今天发现坏了一半，这种情况能退吗", "refund_request", "时间+产品+问题+退货询问"),
            ("我买了一箱苹果，有几个坏的，可以只退坏的吗", "refund_request", "批量+部分问题+部分退货"),
            ("这个水果看起来不错但是吃起来不甜，算质量问题吗，能退吗", "refund_request", "外观vs口味+质量判断+退货"),
            ("快递送来的时候包装就破了，里面的水果也坏了，找谁退", "refund_request", "物流问题+损坏+退货对象"),
            ("买的时候说是进口的，但是感觉不像，这种能退吗", "refund_request", "描述不符+退货询问"),
            ("朋友说这个牌子不好，我还没开封，能退吗", "refund_request", "他人意见+未使用+退货"),
            ("价格比别家贵了很多，发现后能退货重新买吗", "refund_request", "价格比较+退货重购"),
            ("买了但是家里人不喜欢吃，这种情况能退吗", "refund_request", "他人偏好+退货询问"),
        ]
        
        # 6. 负面测试 - 不应该被识别为退货的查询
        negative_tests = [
            ("有苹果吗", "inquiry_availability", "产品可用性查询"),
            ("苹果多少钱", "inquiry_price_or_buy", "价格查询"),
            ("推荐点好吃的水果", "request_recommendation", "推荐请求"),
            ("你好", "greeting", "问候语"),
            ("你是谁", "identity_query", "身份查询"),
            ("苹果好吃吗", "unknown", "产品评价询问"),
            ("这个水果怎么样", "unknown", "产品评价询问"),
            ("有什么新鲜的", "request_recommendation", "新鲜产品询问"),
            ("今天有什么特价", "what_do_you_sell", "特价询问"),
            ("怎么付款", "inquiry_policy", "付款方式询问"),
        ]
        
        # 运行所有测试
        all_passed = True
        all_passed &= self.test_category("真实用户场景", real_user_scenarios)
        all_passed &= self.test_category("产品+退货组合", product_refund_combinations)
        all_passed &= self.test_category("语言表达多样性", expression_variety)
        all_passed &= self.test_category("边缘情况", edge_cases)
        all_passed &= self.test_category("复杂场景", complex_scenarios)
        all_passed &= self.test_category("负面测试", negative_tests)
        
        return all_passed
    
    def generate_analysis_report(self):
        """生成分析报告"""
        print("\n" + "=" * 60)
        print("全面分析报告")
        print("=" * 60)
        
        total = self.results['total_tests']
        passed = self.results['passed']
        failed = self.results['failed']
        
        print(f"总测试用例: {total}")
        print(f"通过: {passed} ({passed/total*100:.1f}%)")
        print(f"失败: {failed} ({failed/total*100:.1f}%)")
        
        if self.results['failed_cases']:
            print(f"\n失败案例详细分析:")
            print("-" * 40)
            
            # 按类别分组失败案例
            by_category = {}
            for case in self.results['failed_cases']:
                category = case['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(case)
            
            for category, cases in by_category.items():
                print(f"\n{category} ({len(cases)}个失败):")
                for case in cases:
                    print(f"  输入: \"{case['input']}\"")
                    print(f"  期望: {case['expected']} | 实际: {case['actual']} | 分类器: {case['classifier']}")
                    print(f"  描述: {case['description']}")
                    print()
        
        return len(self.results['failed_cases']) == 0

def main():
    analyzer = RefundIntentAnalyzer()
    
    print("开始退货意图识别系统全面分析...")
    
    # 运行全面分析
    all_passed = analyzer.run_comprehensive_analysis()
    
    # 生成分析报告
    report_clean = analyzer.generate_analysis_report()
    
    print("\n" + "=" * 60)
    if all_passed and report_clean:
        print("所有测试通过！系统运行正常。")
    else:
        print("发现问题！需要进一步改进。")
    
    return analyzer.results

if __name__ == "__main__":
    results = main()
