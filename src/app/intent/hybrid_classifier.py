#!/usr/bin/env python3
"""
混合意图分类器：结合规则和机器学习
针对小数据集优化，提供更好的准确性和可解释性
"""

import pandas as pd
import re
import logging
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
import json

logger = logging.getLogger(__name__)

class HybridIntentClassifier:
    """
    混合意图分类器：
    1. 优先使用规则匹配（高精度）
    2. 回退到机器学习模型（覆盖更多情况）
    3. 最后使用关键词匹配（兜底）
    """
    
    def __init__(self, model_path: str = "src/models/hybrid_intent_model"):
        self.model_path = model_path
        self.ml_model = None
        self.intent_rules = self._build_intent_rules()
        self.keyword_patterns = self._build_keyword_patterns()
        self._load_or_train_model()
    
    def _build_intent_rules(self) -> Dict[str, List[str]]:
        """构建高精度的规则匹配模式"""
        return {
            'greeting': [
                r'^(你好|您好|hi|hello|嗨|早上好|晚上好|在吗)[\?？!！。]*$',
                r'^(你好啊|您好啊)[\?？!！。]*$'
            ],
            'identity_query': [
                r'你是(谁|什么|机器人|AI|助手|真人)',
                r'(介绍|说说)(一下)?(你)?自己',
                r'你叫什么(名字)?'
            ],
            'what_do_you_sell': [
                r'(你们)?(卖|有)(什么|哪些)(产品|商品|东西)',
                r'(商品|产品)列表',
                r'菜单',
                r'都有(什么|哪些|啥)'
            ],
            'inquiry_price_or_buy': [
                r'(多少钱|价格|怎么卖|一斤多少|售价)',
                r'(我要|来|买)(一斤|一个|一袋|一箱)',
                r'(这个|那个)(多少钱|怎么卖|价格)'
            ],
            'inquiry_availability': [
                r'有(没有|吗|卖)?(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓)',
                r'(还有|有没有)(别的|其他的)?(水果|蔬菜|产品)',
                r'(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓)(有吗|还有吗|有没有)',
                # 添加单独产品名称的匹配
                r'^(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓|山楂|芭乐|柠檬|火龙果|猕猴桃|荔枝|龙眼|榴莲|菠萝|椰子)[\?？!！。]*$',
                # 添加"产品名+有？"模式的匹配（修复中文问号问题）
                r'(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓|山楂|芭乐|柠檬|火龙果|猕猴桃|荔枝|龙眼|榴莲|菠萝|椰子)有[\?？!！。]*$',
                # 添加口语化表达的匹配
                r'(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓|山楂|芭乐|柠檬|火龙果|猕猴桃|荔枝|龙眼|榴莲|菠萝|椰子)(卖不|有不)[\?？!！。]*$',
                r'(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓|山楂|芭乐|柠檬|火龙果|猕猴桃|荔枝|龙眼|榴莲|菠萝|椰子)(卖吗|有吗)[\?？!！。]*$',
                r'(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓|山楂|芭乐|柠檬|火龙果|猕猴桃|荔枝|龙眼|榴莲|菠萝|椰子)(卖不卖|有没有|有不有)[\?？!！。]*$',
                r'^(卖不|有不)[\?？!！。]*(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓|山楂|芭乐|柠檬|火龙果|猕猴桃|荔枝|龙眼|榴莲|菠萝|椰子)',
                r'^(卖不卖|有没有|有不有)[\?？!！。]*(苹果|草莓|西瓜|香蕉|橙子|梨|葡萄|桃子|樱桃|芒果|蓝莓|山楂|芭乐|柠檬|火龙果|猕猴桃|荔枝|龙眼|榴莲|菠萝|椰子)'
            ],
            'request_recommendation': [
                r'(推荐|介绍)(点|一些|几样)?(好吃的|东西|产品)',
                r'什么(比较好|值得买|好吃|特色)',
                r'有什么(推荐|好的|特色)的',
                r'当季有什么好的'
            ],
            'inquiry_policy': [
                r'(退货|退款|配送|运费|支付|取货)(政策|方式|流程|怎么|地址)',
                r'质量问题怎么办',
                r'怎么(退货|退款|配送|支付)'
            ]
        }
    
    def _build_keyword_patterns(self) -> Dict[str, List[str]]:
        """构建关键词匹配模式（兜底机制）"""
        return {
            'greeting': ['你好', '您好', 'hi', 'hello', '嗨', '在吗'],
            'identity_query': ['你是', '介绍', '名字', '机器人', 'AI', '助手'],
            'what_do_you_sell': ['卖什么', '有什么', '商品', '产品', '菜单', '列表'],
            'inquiry_price_or_buy': ['多少钱', '价格', '买', '要', '来', '怎么卖', '售价'],
            'inquiry_availability': ['有吗', '有没有', '还有', '卖不卖', '卖不', '有不', '卖吗', '有不有', '苹果', '草莓', '西瓜', '香蕉', '橙子', '梨', '葡萄', '桃子', '樱桃', '芒果', '蓝莓', '山楂', '芭乐', '柠檬', '火龙果', '猕猴桃', '荔枝', '龙眼', '榴莲', '菠萝', '椰子'],
            'request_recommendation': ['推荐', '介绍', '好吃', '值得', '特色', '当季'],
            'inquiry_policy': ['政策', '退货', '退款', '配送', '运费', '支付', '取货']
        }
    
    def _rule_based_classify(self, text: str) -> Optional[str]:
        """基于规则的分类（第一优先级）"""
        text_clean = text.strip().lower()
        
        for intent, patterns in self.intent_rules.items():
            for pattern in patterns:
                if re.search(pattern, text_clean):
                    logger.debug(f"规则匹配: '{text}' -> {intent} (模式: {pattern})")
                    return intent
        return None
    
    def _keyword_based_classify(self, text: str) -> Optional[str]:
        """基于关键词的分类（兜底机制）"""
        text_clean = text.strip().lower()
        
        # 计算每个意图的关键词匹配得分
        intent_scores = {}
        for intent, keywords in self.keyword_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_clean)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            logger.debug(f"关键词匹配: '{text}' -> {best_intent} (得分: {intent_scores})")
            return best_intent
        
        return None
    
    def _load_or_train_model(self):
        """加载或训练机器学习模型"""
        model_file = os.path.join(self.model_path, 'ml_model.joblib')
        
        if os.path.exists(model_file):
            try:
                self.ml_model = joblib.load(model_file)
                logger.info(f"已加载机器学习模型: {model_file}")
                return
            except Exception as e:
                logger.warning(f"加载模型失败: {e}，将重新训练")
        
        # 训练新模型
        self._train_ml_model()
    
    def _train_ml_model(self):
        """训练机器学习模型"""
        try:
            # 加载训练数据
            df = pd.read_csv('data/intent_training_data.csv')
            df['text'] = df['text'].str.strip().str.strip('"')
            
            # 创建简单但有效的特征提取和分类管道
            self.ml_model = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=1000,
                    ngram_range=(1, 2),
                    stop_words=None,  # 保留所有词，因为中文停用词可能重要
                    lowercase=True
                )),
                ('classifier', MultinomialNB(alpha=0.1))
            ])
            
            # 训练模型
            X = df['text']
            y = df['intent']
            
            # 分割数据
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # 训练
            self.ml_model.fit(X_train, y_train)
            
            # 评估
            y_pred = self.ml_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"机器学习模型训练完成，测试准确率: {accuracy:.4f}")
            logger.info("分类报告:")
            logger.info("\n" + classification_report(y_test, y_pred, zero_division=0))
            
            # 保存模型
            os.makedirs(self.model_path, exist_ok=True)
            joblib.dump(self.ml_model, os.path.join(self.model_path, 'ml_model.joblib'))
            logger.info(f"模型已保存到: {self.model_path}")
            
        except Exception as e:
            logger.error(f"训练机器学习模型失败: {e}")
            self.ml_model = None
    
    def predict(self, text: str) -> str:
        """
        预测意图，使用三层策略：
        1. 规则匹配（最高优先级）
        2. 机器学习模型
        3. 关键词匹配（兜底）
        """
        if not text or not text.strip():
            return 'unknown'
        
        text = text.strip()
        
        # 第一层：规则匹配
        rule_result = self._rule_based_classify(text)
        if rule_result:
            return rule_result
        
        # 第二层：机器学习模型
        if self.ml_model:
            try:
                ml_result = self.ml_model.predict([text])[0]
                # 获取预测概率，如果置信度足够高就使用
                proba = self.ml_model.predict_proba([text])[0]
                max_proba = max(proba)
                if max_proba > 0.3:  # 置信度阈值
                    logger.debug(f"ML模型预测: '{text}' -> {ml_result} (置信度: {max_proba:.3f})")
                    return ml_result
            except Exception as e:
                logger.warning(f"ML模型预测失败: {e}")
        
        # 第三层：关键词匹配
        keyword_result = self._keyword_based_classify(text)
        if keyword_result:
            return keyword_result
        
        # 最后兜底
        return 'unknown'
    
    def get_prediction_confidence(self, text: str) -> Tuple[str, float]:
        """获取预测结果和置信度"""
        intent = self.predict(text)
        
        # 规则匹配的置信度最高
        if self._rule_based_classify(text):
            return intent, 0.95
        
        # ML模型的置信度
        if self.ml_model and intent != 'unknown':
            try:
                proba = self.ml_model.predict_proba([text])[0]
                max_proba = max(proba)
                return intent, max_proba
            except:
                pass
        
        # 关键词匹配的置信度中等
        if self._keyword_based_classify(text):
            return intent, 0.6
        
        # 未知的置信度最低
        return intent, 0.1

def main():
    """测试混合分类器"""
    classifier = HybridIntentClassifier()
    
    test_cases = [
        "你好",
        "苹果多少钱",
        "有什么推荐的",
        "有苹果吗",
        "你们卖什么",
        "退货政策",
        "你是谁",
        "今天天气真好",
        "我要买草莓",
        "还有别的水果吗",
        # 新增：测试中文标点符号的情况
        "草莓有？",
        "苹果有？",
        "西瓜有？",
        "香蕉有？"
    ]
    
    print("混合意图分类器测试:")
    print("=" * 50)
    
    for text in test_cases:
        intent, confidence = classifier.get_prediction_confidence(text)
        print(f"'{text}' -> {intent} (置信度: {confidence:.3f})")

if __name__ == '__main__':
    main()
