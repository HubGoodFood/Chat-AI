#!/usr/bin/env python3
"""
改进的意图分类器训练脚本
解决模型过度偏向某个类别的问题
"""

import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torch.optim import AdamW
from transformers import BertTokenizer, BertForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
import logging
import os
import json
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 改进的配置参数 ---
MODEL_NAME = 'bert-base-chinese'
TRAINING_DATA_FILE = 'data/intent_training_data.csv'
MODEL_SAVE_PATH = 'src/models/intent_model'
NUM_EPOCHS = 8  # 增加训练轮数
BATCH_SIZE = 4  # 减小批次大小，提高稳定性
LEARNING_RATE = 1e-5  # 降低学习率
MAX_LEN = 64  # 减小序列长度，适合短文本
TEST_SET_SIZE = 0.2
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.01

class IntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len, label_map):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.label_map = label_map

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
            truncation=True
        )

        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.label_map[label], dtype=torch.long)
        }

def train_epoch(model, data_loader, loss_fn, optimizer, device, scheduler, n_examples):
    model = model.train()
    losses = []
    correct_predictions = 0

    for d in data_loader:
        input_ids = d["input_ids"].to(device)
        attention_mask = d["attention_mask"].to(device)
        labels = d["labels"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss
        logits = outputs.logits
        
        _, preds = torch.max(logits, dim=1)
        correct_predictions += torch.sum(preds == labels)
        losses.append(loss.item())

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()

    return correct_predictions.double() / n_examples, sum(losses) / len(losses)

def eval_model(model, data_loader, loss_fn, device, n_examples, label_map):
    model = model.eval()
    losses = []
    correct_predictions = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for d in data_loader:
            input_ids = d["input_ids"].to(device)
            attention_mask = d["attention_mask"].to(device)
            labels = d["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            logits = outputs.logits

            _, preds = torch.max(logits, dim=1)
            correct_predictions += torch.sum(preds == labels)
            losses.append(loss.item())
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # 生成分类报告
    id_to_label = {v: k for k, v in label_map.items()}
    target_names = [id_to_label[i] for i in range(len(label_map))]
    
    logger.info("分类报告:")
    logger.info("\n" + classification_report(all_labels, all_preds, target_names=target_names, zero_division=0))

    return correct_predictions.double() / n_examples, sum(losses) / len(losses)

def main():
    logger.info("开始改进的意图分类器训练...")
    
    # 加载数据
    logger.info(f"从 '{TRAINING_DATA_FILE}' 加载训练数据...")
    if not os.path.exists(TRAINING_DATA_FILE):
        logger.error(f"错误: 训练数据文件 '{TRAINING_DATA_FILE}' 未找到。")
        return
        
    df = pd.read_csv(TRAINING_DATA_FILE)
    df = df.dropna(subset=['text', 'intent'])
    
    # 数据预处理：去除引号和多余空格
    df['text'] = df['text'].str.strip().str.strip('"')
    
    logger.info(f"加载了 {len(df)} 条训练数据")
    
    # 创建标签映射
    unique_intents = sorted(df['intent'].unique())  # 排序确保一致性
    label_map = {intent: i for i, intent in enumerate(unique_intents)}
    num_labels = len(unique_intents)
    logger.info(f"发现 {num_labels} 个意图类别: {', '.join(unique_intents)}")
    
    # 分析数据分布
    intent_counts = df['intent'].value_counts()
    logger.info("数据分布:")
    for intent, count in intent_counts.items():
        logger.info(f"  {intent}: {count} 样本")
    
    # 计算类别权重以处理不平衡数据
    unique_intent_labels = np.array(unique_intents)
    class_weights = compute_class_weight(
        'balanced',
        classes=unique_intent_labels,
        y=df['intent']
    )
    class_weight_dict = dict(zip(unique_intent_labels, class_weights))
    logger.info(f"类别权重: {class_weight_dict}")
    
    # 划分数据集
    df_train, df_val = train_test_split(
        df, 
        test_size=TEST_SET_SIZE, 
        random_state=42, 
        stratify=df['intent']
    )
    logger.info(f"训练集大小: {len(df_train)}, 验证集大小: {len(df_val)}")
    
    # 初始化分词器和模型
    logger.info(f"加载预训练模型: '{MODEL_NAME}'")
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels)
    
    # 创建数据集
    train_dataset = IntentDataset(
        texts=df_train.text.to_numpy(),
        labels=df_train.intent.to_numpy(),
        tokenizer=tokenizer,
        max_len=MAX_LEN,
        label_map=label_map
    )
    
    val_dataset = IntentDataset(
        texts=df_val.text.to_numpy(),
        labels=df_val.intent.to_numpy(),
        tokenizer=tokenizer,
        max_len=MAX_LEN,
        label_map=label_map
    )
    
    # 创建数据加载器
    train_data_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_data_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
    
    # 设置设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    logger.info(f"使用设备: {device}")
    
    # 创建加权损失函数
    weights = torch.tensor([class_weight_dict[unique_intents[i]] for i in range(num_labels)], dtype=torch.float)
    weights = weights.to(device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)
    
    # 设置优化器和调度器
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    total_steps = len(train_data_loader) * NUM_EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATIO)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps
    )
    
    # 训练循环
    best_accuracy = 0
    patience = 3
    patience_counter = 0
    
    for epoch in range(NUM_EPOCHS):
        logger.info(f'--- Epoch {epoch + 1}/{NUM_EPOCHS} ---')
        
        train_acc, train_loss = train_epoch(
            model, train_data_loader, loss_fn, optimizer, device, scheduler, len(df_train)
        )
        logger.info(f'训练集损失: {train_loss:.4f}, 准确率: {train_acc:.4f}')

        val_acc, val_loss = eval_model(
            model, val_data_loader, loss_fn, device, len(df_val), label_map
        )
        logger.info(f'验证集损失: {val_loss:.4f}, 准确率: {val_acc:.4f}')

        if val_acc > best_accuracy:
            logger.info(f"验证集准确率提升 ({best_accuracy:.4f} -> {val_acc:.4f})，保存模型")
            if not os.path.exists(MODEL_SAVE_PATH):
                os.makedirs(MODEL_SAVE_PATH)
            model.save_pretrained(MODEL_SAVE_PATH, safe_serialization=False)
            tokenizer.save_pretrained(MODEL_SAVE_PATH)
            # 保存标签映射
            with open(os.path.join(MODEL_SAVE_PATH, 'label_map.json'), 'w', encoding='utf-8') as f:
                json.dump(label_map, f, ensure_ascii=False, indent=4)
            best_accuracy = val_acc
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"验证集准确率连续 {patience} 轮未提升，提前停止训练")
                break

    logger.info("训练完成！")
    logger.info(f"最佳验证集准确率: {best_accuracy:.4f}")
    logger.info(f"模型已保存到 '{MODEL_SAVE_PATH}' 目录。")

if __name__ == '__main__':
    main()
