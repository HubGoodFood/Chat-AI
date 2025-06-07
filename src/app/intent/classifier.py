import torch
from transformers import BertForSequenceClassification, BertTokenizer
import logging
import os
from typing import List, Dict, Tuple
from .hybrid_classifier import HybridIntentClassifier

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    意图分类器：优先使用混合分类器，BERT作为备选
    """
    def __init__(self, model_path: str = "src/models/intent_model"):
        """
        初始化意图分类器。

        Args:
            model_path (str): 存放微调后模型的目录路径。
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.label_map = None

        # 初始化混合分类器（主要方法）
        try:
            self.hybrid_classifier = HybridIntentClassifier()
            logger.info("混合意图分类器初始化成功")
        except Exception as e:
            logger.warning(f"混合分类器初始化失败: {e}，将使用BERT模型")
            self.hybrid_classifier = None

        # 加载BERT模型（备选方法）
        self._load_model()

    def _load_model(self):
        """
        从指定路径加载模型、分词器和标签映射。
        """
        if not os.path.exists(self.model_path) or not os.listdir(self.model_path):
            logger.warning(f"模型路径 '{self.model_path}' 不存在或为空。")
            logger.warning("请先运行 'train_intent_model.py' 脚本来训练和保存模型。")
            logger.warning("在模型准备好之前，意图分类将无法工作。")
            return

        try:
            logger.info(f"从 '{self.model_path}' 加载模型...")
            self.model = BertForSequenceClassification.from_pretrained(self.model_path)
            self.tokenizer = BertTokenizer.from_pretrained(self.model_path)
            
            # 加载标签映射
            import json
            label_map_path = os.path.join(self.model_path, 'label_map.json')
            if os.path.exists(label_map_path):
                with open(label_map_path, 'r', encoding='utf-8') as f:
                    self.label_map = json.load(f)
            else:
                logger.error(f"在 '{label_map_path}' 未找到 label_map.json。")
                self.model = None # 加载失败

            if self.model and self.tokenizer and self.label_map:
                logger.info("意图分类模型加载成功。")

        except Exception as e:
            logger.error(f"加载意图分类模型失败: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None
            self.label_map = None

    def predict(self, text: str) -> str:
        """
        预测给定文本的意图。

        Args:
            text (str): 用户输入的文本。

        Returns:
            str: 预测的意图标签。如果模型未加载，则返回 'unknown'。
        """
        # 优先使用混合分类器
        if self.hybrid_classifier:
            try:
                result = self.hybrid_classifier.predict(text)
                logger.debug(f"混合分类器预测: '{text}' -> {result}")
                return result
            except Exception as e:
                logger.warning(f"混合分类器预测失败: {e}，回退到BERT模型")

        # 回退到BERT模型
        if not self.model or not self.tokenizer or not self.label_map:
            logger.warning("所有意图分类器都不可用，返回 'unknown'。")
            return 'unknown'

        try:
            # 准备输入
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)

            # 模型预测
            with torch.no_grad():
                outputs = self.model(**inputs)

            logits = outputs.logits
            predicted_class_id = torch.argmax(logits, dim=1).item()

            # 将ID转换回标签
            # label_map 的格式是 {"label": id}, 我们需要反转它
            id_to_label = {v: k for k, v in self.label_map.items()}

            result = id_to_label.get(predicted_class_id, 'unknown')
            logger.debug(f"BERT模型预测: '{text}' -> {result}")
            return result
        except Exception as e:
            logger.error(f"BERT模型预测失败: {e}")
            return 'unknown'

    def get_prediction_confidence(self, text: str) -> Tuple[str, float]:
        """
        获取预测结果和置信度

        Args:
            text (str): 用户输入的文本

        Returns:
            Tuple[str, float]: (预测的意图, 置信度)
        """
        if self.hybrid_classifier:
            try:
                return self.hybrid_classifier.get_prediction_confidence(text)
            except Exception as e:
                logger.warning(f"获取混合分类器置信度失败: {e}")

        # BERT模型的置信度计算
        intent = self.predict(text)
        return intent, 0.5 if intent != 'unknown' else 0.1