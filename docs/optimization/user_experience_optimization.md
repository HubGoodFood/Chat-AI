# 用户体验优化实现方案

## 1. 智能推荐系统

### 1.1 政策问题智能推荐引擎

```python
#!/usr/bin/env python3
"""
政策问题智能推荐引擎
基于用户查询历史和问题相关性提供智能推荐
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
import json
import time

logger = logging.getLogger(__name__)

@dataclass
class QuestionRecommendation:
    """问题推荐数据类"""
    question: str
    category: str
    relevance_score: float
    reason: str
    metadata: Dict[str, Any] = None

class PolicyRecommendationEngine:
    """
    政策问题智能推荐引擎
    
    功能特性：
    - 基于查询历史的个性化推荐
    - 问题分类和相关性分析
    - 新用户引导推荐
    - 热门问题推荐
    - 上下文感知推荐
    """
    
    def __init__(self):
        # 预定义问题分类
        self.question_categories = {
            '配送相关': {
                'keywords': ['配送', '送货', '运费', '时间', '范围', '地址'],
                'questions': [
                    "配送时间是什么时候？",
                    "配送范围包括哪些地区？", 
                    "运费是多少？",
                    "什么条件可以免费配送？",
                    "配送时间可以指定吗？",
                    "外围地区配送费用如何计算？"
                ]
            },
            '付款相关': {
                'keywords': ['付款', '支付', 'venmo', '现金', '备注'],
                'questions': [
                    "怎么付款？",
                    "付款时需要备注什么？",
                    "可以用现金付款吗？",
                    "Venmo账号是什么？",
                    "付款备注格式是什么？",
                    "可以分期付款吗？"
                ]
            },
            '取货相关': {
                'keywords': ['取货', '自取', '地点', '时间', '联系'],
                'questions': [
                    "取货地点在哪里？",
                    "取货时间是什么时候？",
                    "取货需要带什么？",
                    "取货点联系方式是什么？",
                    "可以代取货吗？",
                    "取货时需要注意什么？"
                ]
            },
            '质量相关': {
                'keywords': ['质量', '保证', '退款', '换货', '问题'],
                'questions': [
                    "产品质量有保证吗？",
                    "收到有问题的产品怎么办？",
                    "退款政策是什么？",
                    "多长时间内可以反馈质量问题？",
                    "什么情况下可以退款？",
                    "如何申请退换货？"
                ]
            },
            '群规相关': {
                'keywords': ['群规', '规则', '禁止', '违规', '管理'],
                'questions': [
                    "群里有什么规则需要遵守？",
                    "什么行为是被禁止的？",
                    "违反群规会怎样？",
                    "可以在群里发广告吗？",
                    "可以私加群友吗？",
                    "群管理员是谁？"
                ]
            },
            '产品相关': {
                'keywords': ['产品', '商品', '新鲜', '农场', '有机'],
                'questions': [
                    "产品都是新鲜的吗？",
                    "产品来源是哪里？",
                    "有有机产品吗？",
                    "产品价格如何？",
                    "产品规格是什么？",
                    "季节性产品有哪些？"
                ]
            }
        }
        
        # 用户查询历史
        self.user_query_history = defaultdict(list)
        self.global_query_stats = Counter()
        
        # 推荐配置
        self.recommendation_config = {
            'max_recommendations': 5,
            'relevance_threshold': 0.3,
            'history_weight': 0.4,
            'popularity_weight': 0.3,
            'category_weight': 0.3
        }
    
    def get_recommendations(self, 
                          user_id: str = None, 
                          current_query: str = None,
                          context: Dict[str, Any] = None) -> List[QuestionRecommendation]:
        """
        获取智能推荐问题
        
        Args:
            user_id: 用户ID
            current_query: 当前查询
            context: 上下文信息
        
        Returns:
            推荐问题列表
        """
        recommendations = []
        
        # 1. 基于当前查询的相关推荐
        if current_query:
            query_related = self._get_query_related_recommendations(current_query)
            recommendations.extend(query_related)
        
        # 2. 基于用户历史的个性化推荐
        if user_id:
            history_based = self._get_history_based_recommendations(user_id)
            recommendations.extend(history_based)
        
        # 3. 热门问题推荐
        popular_questions = self._get_popular_recommendations()
        recommendations.extend(popular_questions)
        
        # 4. 新用户引导推荐
        if not user_id or len(self.user_query_history.get(user_id, [])) < 3:
            newbie_recommendations = self._get_newbie_recommendations()
            recommendations.extend(newbie_recommendations)
        
        # 去重和排序
        final_recommendations = self._rank_and_deduplicate_recommendations(recommendations)
        
        return final_recommendations[:self.recommendation_config['max_recommendations']]
    
    def _get_query_related_recommendations(self, query: str) -> List[QuestionRecommendation]:
        """基于当前查询获取相关推荐"""
        recommendations = []
        query_lower = query.lower()
        
        # 分析查询属于哪个类别
        query_category = self._classify_query(query_lower)
        
        if query_category:
            category_info = self.question_categories[query_category]
            
            # 推荐同类别的其他问题
            for question in category_info['questions']:
                if question.lower() != query_lower:  # 避免推荐相同问题
                    relevance_score = self._calculate_query_relevance(query_lower, question.lower())
                    
                    if relevance_score >= self.recommendation_config['relevance_threshold']:
                        recommendations.append(QuestionRecommendation(
                            question=question,
                            category=query_category,
                            relevance_score=relevance_score,
                            reason=f"与您的查询"{query}"相关",
                            metadata={'source': 'query_related'}
                        ))
        
        return recommendations
    
    def _get_history_based_recommendations(self, user_id: str) -> List[QuestionRecommendation]:
        """基于用户历史获取个性化推荐"""
        recommendations = []
        user_history = self.user_query_history.get(user_id, [])
        
        if not user_history:
            return recommendations
        
        # 分析用户查询偏好
        user_categories = self._analyze_user_preferences(user_history)
        
        # 基于偏好推荐问题
        for category, preference_score in user_categories.items():
            if preference_score > 0.2:  # 偏好阈值
                category_questions = self.question_categories[category]['questions']
                
                for question in category_questions[:2]:  # 每个类别推荐2个
                    # 检查是否已经查询过
                    if not self._has_user_asked_similar(user_id, question):
                        recommendations.append(QuestionRecommendation(
                            question=question,
                            category=category,
                            relevance_score=preference_score,
                            reason=f"基于您对{category}的关注",
                            metadata={'source': 'history_based', 'preference_score': preference_score}
                        ))
        
        return recommendations
    
    def _get_popular_recommendations(self) -> List[QuestionRecommendation]:
        """获取热门问题推荐"""
        recommendations = []
        
        # 获取最热门的问题类别
        popular_categories = self._get_popular_categories()
        
        for category, popularity_score in popular_categories[:3]:  # 前3个热门类别
            category_questions = self.question_categories[category]['questions']
            
            # 推荐该类别最具代表性的问题
            representative_question = category_questions[0]  # 第一个通常是最基础的
            
            recommendations.append(QuestionRecommendation(
                question=representative_question,
                category=category,
                relevance_score=popularity_score,
                reason="热门问题",
                metadata={'source': 'popular', 'popularity_score': popularity_score}
            ))
        
        return recommendations
    
    def _get_newbie_recommendations(self) -> List[QuestionRecommendation]:
        """获取新用户引导推荐"""
        newbie_questions = [
            ("配送时间是什么时候？", "配送相关", "新用户必知"),
            ("怎么付款？", "付款相关", "新用户必知"),
            ("取货地点在哪里？", "取货相关", "新用户必知"),
            ("群里有什么规则需要遵守？", "群规相关", "新用户必知")
        ]
        
        recommendations = []
        for question, category, reason in newbie_questions:
            recommendations.append(QuestionRecommendation(
                question=question,
                category=category,
                relevance_score=0.8,
                reason=reason,
                metadata={'source': 'newbie_guide'}
            ))
        
        return recommendations
    
    def _classify_query(self, query: str) -> Optional[str]:
        """分类查询属于哪个类别"""
        max_score = 0
        best_category = None
        
        for category, info in self.question_categories.items():
            score = 0
            for keyword in info['keywords']:
                if keyword in query:
                    score += len(keyword) / len(query)
            
            if score > max_score:
                max_score = score
                best_category = category
        
        return best_category if max_score > 0.1 else None
    
    def _calculate_query_relevance(self, query1: str, query2: str) -> float:
        """计算两个查询的相关性"""
        # 简单的词汇重叠计算
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _analyze_user_preferences(self, user_history: List[str]) -> Dict[str, float]:
        """分析用户查询偏好"""
        category_counts = defaultdict(int)
        total_queries = len(user_history)
        
        for query in user_history:
            category = self._classify_query(query.lower())
            if category:
                category_counts[category] += 1
        
        # 计算偏好分数
        preferences = {}
        for category, count in category_counts.items():
            preferences[category] = count / total_queries
        
        return preferences
    
    def _has_user_asked_similar(self, user_id: str, question: str) -> bool:
        """检查用户是否问过类似问题"""
        user_history = self.user_query_history.get(user_id, [])
        
        for past_query in user_history:
            if self._calculate_query_relevance(past_query.lower(), question.lower()) > 0.7:
                return True
        
        return False
    
    def _get_popular_categories(self) -> List[Tuple[str, float]]:
        """获取热门类别"""
        category_popularity = defaultdict(int)
        
        # 统计全局查询中各类别的热度
        for query, count in self.global_query_stats.items():
            category = self._classify_query(query.lower())
            if category:
                category_popularity[category] += count
        
        # 计算相对热度
        total_queries = sum(category_popularity.values())
        if total_queries == 0:
            return []
        
        popularity_scores = [
            (category, count / total_queries) 
            for category, count in category_popularity.items()
        ]
        
        return sorted(popularity_scores, key=lambda x: x[1], reverse=True)
    
    def _rank_and_deduplicate_recommendations(self, 
                                            recommendations: List[QuestionRecommendation]) -> List[QuestionRecommendation]:
        """排序和去重推荐"""
        # 去重（基于问题内容）
        seen_questions = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec.question not in seen_questions:
                seen_questions.add(rec.question)
                unique_recommendations.append(rec)
        
        # 按相关性分数排序
        unique_recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_recommendations
    
    def record_user_query(self, user_id: str, query: str):
        """记录用户查询"""
        if user_id:
            self.user_query_history[user_id].append(query)
            
            # 限制历史记录长度
            if len(self.user_query_history[user_id]) > 50:
                self.user_query_history[user_id] = self.user_query_history[user_id][-50:]
        
        # 更新全局统计
        self.global_query_stats[query.lower()] += 1
    
    def get_recommendation_stats(self) -> Dict[str, Any]:
        """获取推荐系统统计"""
        total_users = len(self.user_query_history)
        total_queries = sum(len(history) for history in self.user_query_history.values())
        
        category_distribution = defaultdict(int)
        for query in self.global_query_stats:
            category = self._classify_query(query)
            if category:
                category_distribution[category] += self.global_query_stats[query]
        
        return {
            'total_users': total_users,
            'total_queries': total_queries,
            'average_queries_per_user': total_queries / total_users if total_users > 0 else 0,
            'category_distribution': dict(category_distribution),
            'most_popular_queries': self.global_query_stats.most_common(10)
        }
```

## 2. 政策回复格式优化

### 2.1 富文本格式化器

```python
class PolicyResponseFormatter:
    """
    政策回复格式化器
    
    功能特性：
    - 结构化回复格式
    - 多媒体内容支持
    - 情感化表达
    - 可读性优化
    """
    
    def __init__(self):
        self.emoji_map = {
            '配送相关': '📦',
            '付款相关': '💰',
            '取货相关': '📍',
            '质量相关': '✅',
            '群规相关': '📋',
            '产品相关': '🥬'
        }
        
        self.templates = {
            'delivery': self._format_delivery_response,
            'payment': self._format_payment_response,
            'pickup': self._format_pickup_response,
            'quality': self._format_quality_response,
            'rules': self._format_rules_response,
            'general': self._format_general_response
        }
    
    def format_policy_response(self, 
                             policy_content: List[str], 
                             query: str,
                             category: str = None) -> Dict[str, Any]:
        """格式化政策回复"""
        
        # 自动检测类别
        if not category:
            category = self._detect_category(query)
        
        # 选择合适的格式化模板
        formatter = self.templates.get(category, self.templates['general'])
        
        # 格式化内容
        formatted_response = formatter(policy_content, query)
        
        # 添加推荐问题
        recommendations = self._get_related_questions(category)
        
        return {
            'message': formatted_response,
            'category': category,
            'recommendations': recommendations,
            'source': 'policy_database',
            'timestamp': time.time()
        }
    
    def _format_delivery_response(self, content: List[str], query: str) -> str:
        """格式化配送相关回复"""
        emoji = self.emoji_map.get('配送相关', '📦')
        
        formatted = f"{emoji} **配送信息**\n\n"
        
        for item in content:
            formatted += f"• {item}\n"
        
        formatted += f"\n💡 **温馨提示**：\n"
        formatted += f"• 请提前关注群内配送通知\n"
        formatted += f"• 如有特殊情况请及时联系义工\n"
        formatted += f"• 珍惜义工们的辛勤付出 ❤️"
        
        return formatted
    
    def _format_payment_response(self, content: List[str], query: str) -> str:
        """格式化付款相关回复"""
        emoji = self.emoji_map.get('付款相关', '💰')
        
        formatted = f"{emoji} **付款指南**\n\n"
        
        for item in content:
            if 'venmo' in item.lower():
                formatted += f"💳 {item}\n"
            elif '备注' in item:
                formatted += f"📝 {item}\n"
            else:
                formatted += f"• {item}\n"
        
        formatted += f"\n⚠️ **重要提醒**：\n"
        formatted += f"• 付款备注信息务必完整准确\n"
        formatted += f"• 选择'friends and family'避免手续费"
        
        return formatted
    
    def _format_pickup_response(self, content: List[str], query: str) -> str:
        """格式化取货相关回复"""
        emoji = self.emoji_map.get('取货相关', '📍')
        
        formatted = f"{emoji} **取货指南**\n\n"
        
        for item in content:
            if '地址' in item or 'st' in item.lower():
                formatted += f"🏠 {item}\n"
            elif '电话' in item or '联系' in item:
                formatted += f"📞 {item}\n"
            elif '时间' in item:
                formatted += f"⏰ {item}\n"
            else:
                formatted += f"• {item}\n"
        
        formatted += f"\n🙏 **取货提醒**：\n"
        formatted += f"• 请按时取货，减少义工负担\n"
        formatted += f"• 取货时请在名单上打勾确认"
        
        return formatted
    
    def _format_quality_response(self, content: List[str], query: str) -> str:
        """格式化质量相关回复"""
        emoji = self.emoji_map.get('质量相关', '✅')
        
        formatted = f"{emoji} **质量保证**\n\n"
        
        for item in content:
            if '24小时' in item:
                formatted += f"⏱️ {item}\n"
            elif '退款' in item:
                formatted += f"💸 {item}\n"
            else:
                formatted += f"• {item}\n"
        
        formatted += f"\n🔍 **质量承诺**：\n"
        formatted += f"• 不好不拼，不新鲜不拼，不好吃不拼\n"
        formatted += f"• 义工多重检查，确保品质"
        
        return formatted
    
    def _format_rules_response(self, content: List[str], query: str) -> str:
        """格式化群规相关回复"""
        emoji = self.emoji_map.get('群规相关', '📋')
        
        formatted = f"{emoji} **群规须知**\n\n"
        
        for item in content:
            if '禁止' in item:
                formatted += f"❌ {item}\n"
            elif '违反' in item:
                formatted += f"⚠️ {item}\n"
            else:
                formatted += f"• {item}\n"
        
        formatted += f"\n🤝 **共建和谐社区**：\n"
        formatted += f"• 遵守群规，人人有责\n"
        formatted += f"• 维护良好的拼单环境"
        
        return formatted
    
    def _format_general_response(self, content: List[str], query: str) -> str:
        """格式化通用回复"""
        formatted = "📋 **相关信息**\n\n"
        
        for item in content:
            formatted += f"• {item}\n"
        
        formatted += f"\n💬 如需了解更多信息，请随时询问！"
        
        return formatted
    
    def _detect_category(self, query: str) -> str:
        """检测查询类别"""
        query_lower = query.lower()
        
        category_keywords = {
            'delivery': ['配送', '送货', '运费', '时间', '范围'],
            'payment': ['付款', '支付', 'venmo', '现金', '备注'],
            'pickup': ['取货', '自取', '地点', '联系'],
            'quality': ['质量', '保证', '退款', '换货', '问题'],
            'rules': ['群规', '规则', '禁止', '违规']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _get_related_questions(self, category: str) -> List[str]:
        """获取相关问题推荐"""
        related_questions = {
            'delivery': [
                "配送范围包括哪些地区？",
                "什么条件可以免费配送？",
                "外围地区运费如何计算？"
            ],
            'payment': [
                "付款备注格式是什么？",
                "可以用现金付款吗？",
                "如何避免手续费？"
            ],
            'pickup': [
                "取货时需要带什么？",
                "可以代取货吗？",
                "取货时间可以调整吗？"
            ],
            'quality': [
                "什么情况下可以退款？",
                "如何申请退换货？",
                "质量问题如何反馈？"
            ],
            'rules': [
                "什么行为是被禁止的？",
                "违反群规会怎样？",
                "可以在群里发广告吗？"
            ]
        }
        
        return related_questions.get(category, [
            "还有其他问题吗？",
            "需要了解更多信息吗？"
        ])
```

这个用户体验优化方案将显著提升Chat-AI的交互质量，通过智能推荐和格式化回复，为用户提供更加友好和有用的服务体验。
