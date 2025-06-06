import torch
from transformers import BertForSequenceClassification, BertTokenizer
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    使用预训练的BERT模型进行意图分类。
    """
    def __init__(self, model_path: str = "intent_model"):
        """
        初始化意图分类器。

        Args:
            model_path (str): 存放微调后模型的目录路径。
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.label_map = None
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
        if not self.model or not self.tokenizer or not self.label_map:
            logger.warning("意图分类器未初始化，返回 'unknown'。")
            return 'unknown'

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
        
        return id_to_label.get(predicted_class_id, 'unknown')