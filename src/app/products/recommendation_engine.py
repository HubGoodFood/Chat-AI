"""
产品推荐引擎 - 智能处理产品不可用场景并提供个性化推荐

该模块提供智能的产品推荐功能，特别针对产品不可用的情况，
能够基于产品类别、口感、用途等特征提供相似的替代品推荐，
并生成温暖、人性化的中文回复。
"""

import random
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProductRecommendation:
    """产品推荐数据结构"""
    product_key: str
    product_details: Dict[str, Any]
    similarity_score: float
    recommendation_reason: str
    category_group: str

class ProductRecommendationEngine:
    """
    产品推荐引擎
    
    专门处理产品不可用场景，提供智能的替代品推荐和人性化的中文回复。
    """
    
    def __init__(self, product_manager):
        """
        初始化推荐引擎
        
        Args:
            product_manager: 产品管理器实例
        """
        self.product_manager = product_manager
        
        # 中文回复模板 - 采用友好对话式风格
        self.empathy_templates = [
            "您好！{product_name}确实是很多人都喜欢的健康{category_type}呢~",
            "{product_name}真是个不错的选择呢！很多朋友都很喜欢~",
            "您想要{product_name}，眼光真好！这确实是很受欢迎的{category_type}呢~",
            "{product_name}是很多顾客都喜欢的{category_type}呢，您的品味真不错~",
        ]

        self.unavailable_templates = [
            "不过很遗憾地告诉您，我们目前暂时没有{product_name}在售呢。",
            "可惜的是，{product_name}现在正好缺货呢，真是不好意思~",
            "真不好意思，{product_name}我们店里暂时还没有呢。",
            "抱歉，{product_name}目前暂时没有现货哦。",
        ]

        self.recommendation_intros = [
            "如果您喜欢{category_type}类产品，可以看看这些不错的选择哦：",
            "为您推荐几款我们这里同样优质的{category_type}，都很受欢迎呢：",
            "不过别担心，我们有一些{category_type}也很不错哦：",
            "给您推荐几款相似的{category_type}，口感都很棒呢：",
        ]
        
        # 类别类型映射
        self.category_type_mapping = {
            "时令水果": "水果",
            "新鲜蔬菜": "蔬菜",
            "禽类产品": "禽类",
            "海鲜河鲜": "海鲜",
            "美味熟食/面点": "熟食",
            "面点": "面点",
            "蛋类": "蛋类",
            "优选干货": "干货",
            # 添加更多映射以确保覆盖
            "水果": "水果",
            "蔬菜": "蔬菜",
            "禽类": "禽类",
            "海鲜": "海鲜",
            "熟食": "熟食",
            "干货": "干货"
        }
        
        # 口感特征分组
        self.taste_groups = {
            "甜味": ["甜", "香甜", "清甜", "甘甜", "蜜甜"],
            "酸味": ["酸", "酸甜", "微酸", "酸爽"],
            "鲜味": ["鲜", "鲜美", "鲜嫩", "鲜甜", "汤鲜"],
            "香味": ["香", "浓香", "清香", "蛋香"],
            "脆嫩": ["脆", "嫩", "爽脆", "脆嫩", "清脆"],
            "软糯": ["糯", "软", "松软", "软糯", "粉糯"]
        }

    def find_similar_products(self, 
                            query_product_name: str, 
                            target_category: Optional[str] = None,
                            max_recommendations: int = 3) -> List[ProductRecommendation]:
        """
        查找相似产品
        
        Args:
            query_product_name: 用户查询的产品名称
            target_category: 目标类别（如果已知）
            max_recommendations: 最大推荐数量
            
        Returns:
            推荐产品列表
        """
        if not self.product_manager.product_catalog:
            return []
            
        recommendations = []
        
        # 1. 首先尝试基于类别匹配
        if target_category:
            category_matches = self._find_by_category(target_category, max_recommendations)
            recommendations.extend(category_matches)
        
        # 2. 如果没有指定类别，尝试推断类别
        if not target_category:
            inferred_category = self.product_manager.find_related_category(query_product_name)
            if inferred_category:
                category_matches = self._find_by_category(inferred_category, max_recommendations)
                recommendations.extend(category_matches)
        
        # 3. 基于关键词和名称相似性匹配
        if len(recommendations) < max_recommendations:
            keyword_matches = self._find_by_keywords(query_product_name, max_recommendations - len(recommendations))
            recommendations.extend(keyword_matches)
        
        # 4. 如果仍然不足，添加热门和当季产品
        if len(recommendations) < max_recommendations:
            fallback_matches = self._find_fallback_products(max_recommendations - len(recommendations), target_category)
            recommendations.extend(fallback_matches)
        
        # 去重并按相似度排序
        seen_keys = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.product_key not in seen_keys:
                unique_recommendations.append(rec)
                seen_keys.add(rec.product_key)
                
        unique_recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
        return unique_recommendations[:max_recommendations]

    def _find_by_category(self, category: str, limit: int) -> List[ProductRecommendation]:
        """基于类别查找产品"""
        recommendations = []
        category_products = self.product_manager.get_products_by_category(category, limit * 2)
        
        for product_key, product_details in category_products:
            if len(recommendations) >= limit:
                break
                
            similarity_score = 0.8  # 同类别产品基础相似度
            
            # 根据是否为当季产品调整分数
            if product_details.get('is_seasonal', False):
                similarity_score += 0.1
                
            # 根据热度调整分数
            popularity = product_details.get('popularity', 0)
            if popularity > 0:
                similarity_score += min(0.1, popularity * 0.01)
            
            reason = f"同样是优质的{self.category_type_mapping.get(category, category)}"
            
            recommendations.append(ProductRecommendation(
                product_key=product_key,
                product_details=product_details,
                similarity_score=similarity_score,
                recommendation_reason=reason,
                category_group=category
            ))
            
        return recommendations

    def _find_by_keywords(self, query: str, limit: int) -> List[ProductRecommendation]:
        """基于关键词查找产品"""
        recommendations = []
        
        # 使用现有的模糊匹配功能
        fuzzy_matches = self.product_manager.fuzzy_match_product(query, threshold=0.3)
        
        for product_key, score in fuzzy_matches[:limit]:
            if product_key in self.product_manager.product_catalog:
                product_details = self.product_manager.product_catalog[product_key]
                
                reason = "名称相似的产品"
                if score > 0.7:
                    reason = "非常相似的产品"
                elif score > 0.5:
                    reason = "比较相似的产品"
                
                recommendations.append(ProductRecommendation(
                    product_key=product_key,
                    product_details=product_details,
                    similarity_score=score,
                    recommendation_reason=reason,
                    category_group=product_details.get('category', '其他')
                ))
                
        return recommendations

    def _find_fallback_products(self, limit: int, preferred_category: Optional[str] = None) -> List[ProductRecommendation]:
        """查找备选产品（当季和热门）"""
        recommendations = []
        
        # 优先添加当季产品
        seasonal_products = self.product_manager.get_seasonal_products(limit, preferred_category)
        for product_key, product_details in seasonal_products:
            if len(recommendations) >= limit:
                break
                
            recommendations.append(ProductRecommendation(
                product_key=product_key,
                product_details=product_details,
                similarity_score=0.6,
                recommendation_reason="当季新鲜推荐",
                category_group=product_details.get('category', '其他')
            ))
        
        # 如果还需要更多，添加热门产品
        if len(recommendations) < limit:
            popular_products = self.product_manager.get_popular_products(
                limit - len(recommendations), preferred_category
            )
            for product_key, product_details in popular_products:
                # 避免重复
                if not any(rec.product_key == product_key for rec in recommendations):
                    recommendations.append(ProductRecommendation(
                        product_key=product_key,
                        product_details=product_details,
                        similarity_score=0.5,
                        recommendation_reason="热门好评推荐",
                        category_group=product_details.get('category', '其他')
                    ))
                    
        return recommendations

    def generate_unavailable_response(self,
                                    query_product_name: str,
                                    recommendations: List[ProductRecommendation],
                                    target_category: Optional[str] = None) -> Dict[str, Any]:
        """
        生成产品不可用的回复，包含消息和产品建议按钮

        Args:
            query_product_name: 用户查询的产品名称
            recommendations: 推荐产品列表
            target_category: 目标类别

        Returns:
            包含 'message' 和 'product_suggestions' 的字典
        """
        if not recommendations:
            return self._generate_no_recommendations_response(query_product_name)
        
        # 确定类别类型
        category_type = "产品"
        if target_category:
            category_type = self.category_type_mapping.get(target_category, target_category)
        elif recommendations:
            first_category = recommendations[0].category_group
            category_type = self.category_type_mapping.get(first_category, "产品")
        
        # 第一步：共情与确认
        empathy_text = random.choice(self.empathy_templates).format(
            product_name=query_product_name,
            category_type=category_type
        )
        
        # 第二步：明确告知缺货
        unavailable_text = random.choice(self.unavailable_templates).format(
            product_name=query_product_name
        )
        
        # 第三步：提供替代品
        intro_text = random.choice(self.recommendation_intros).format(
            category_type=category_type
        )
        
        # 构建产品建议按钮数据
        product_suggestions = []
        for rec in recommendations[:3]:  # 最多3个推荐
            product_name = rec.product_details.get('original_display_name', rec.product_key)
            price = rec.product_details.get('price', 0)
            specification = rec.product_details.get('specification', '份')

            # 构建显示文本（包含价格信息）
            display_text = product_name
            if price > 0:
                display_text += f" ({price:.2f}美元/{specification})"

            product_suggestions.append({
                'display_text': display_text,
                'payload': rec.product_key
            })
        
        # 结束语 - 更加友好对话式
        closing_options = [
            "\n\n您可以点击上面的产品按钮了解详情，或者告诉我您想要其他类型的产品哦！",
            "\n\n点击感兴趣的产品了解更多，或者您想看看其他类别的产品吗？",
            "\n\n这些产品您觉得怎么样？点击任意一个了解详情，或者我可以再帮您推荐其他的呢！"
        ]
        closing_text = random.choice(closing_options)

        # 组合完整回复消息
        message = f"{empathy_text}\n{unavailable_text}\n\n{intro_text}{closing_text}"

        return {
            'message': message,
            'product_suggestions': product_suggestions
        }

    def _generate_no_recommendations_response(self, query_product_name: str) -> Dict[str, Any]:
        """当没有推荐产品时的回复 - 友好对话式风格"""
        empathy_options = [
            f"您好！{query_product_name}确实是个不错的选择呢~",
            f"理解您对{query_product_name}的需求，这确实是很受欢迎的呢！"
        ]

        unavailable_options = [
            f"不过很遗憾地告诉您，我们目前暂时没有{query_product_name}在售呢。",
            f"可惜{query_product_name}现在正好缺货呢，真是不好意思~"
        ]

        suggestion_options = [
            "不过，您可以告诉我您更偏好哪种类型的产品吗？比如是水果、蔬菜，还是其他特定的东西呢？这样我也许能帮您找到合适的替代品哦~",
            "要不您看看我们其他的分类？我们有新鲜的水果、蔬菜、海鲜等都很受欢迎呢。您对哪个品类感兴趣呢？"
        ]

        message = f"{random.choice(empathy_options)}\n{random.choice(unavailable_options)}\n\n{random.choice(suggestion_options)}"

        return {
            'message': message,
            'product_suggestions': []
        }
