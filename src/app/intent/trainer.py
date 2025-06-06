import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import BertTokenizer, BertForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import logging
import os
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 配置参数 ---
MODEL_NAME = 'bert-base-chinese'
TRAINING_DATA_FILE = 'data/intent_training_data.csv'
MODEL_SAVE_PATH = 'src/models/intent_model'
NUM_EPOCHS = 4
BATCH_SIZE = 8
LEARNING_RATE = 2e-5
MAX_LEN = 128
TEST_SET_SIZE = 0.25 # 提高测试集比例

# --- 数据集类 ---
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

# --- 训练函数 ---
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

# --- 评估函数 ---
def eval_model(model, data_loader, loss_fn, device, n_examples):
    model = model.eval()
    losses = []
    correct_predictions = 0

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

    return correct_predictions.double() / n_examples, sum(losses) / len(losses)

# --- 主逻辑 ---
def main():
    # 检查依赖
    try:
        import transformers
        import sklearn
    except ImportError:
        logging.info("正在安装所需的库: transformers, scikit-learn, torch...")
        os.system("pip install transformers scikit-learn torch")
        logging.info("库安装完成。")

    # 加载数据
    logging.info(f"从 '{TRAINING_DATA_FILE}' 加载训练数据...")
    if not os.path.exists(TRAINING_DATA_FILE):
        logging.error(f"错误: 训练数据文件 '{TRAINING_DATA_FILE}' 未找到。")
        return
        
    df = pd.read_csv(TRAINING_DATA_FILE)
    df = df.dropna(subset=['text', 'intent']) # 确保没有空值

    # 创建标签映射
    unique_intents = df['intent'].unique()
    label_map = {intent: i for i, intent in enumerate(unique_intents)}
    num_labels = len(unique_intents)
    logging.info(f"发现 {num_labels} 个意图类别: {', '.join(unique_intents)}")

    # 检查类别样本数是否足够进行分层抽样
    intent_counts = df['intent'].value_counts()
    min_samples = intent_counts.min()
    num_classes = len(intent_counts)
    
    stratify_param = df['intent']
    # 检查验证集是否能覆盖所有类别
    # test_size * len(df) 必须大于等于 num_classes
    required_total_samples = num_classes / TEST_SET_SIZE
    if len(df) < required_total_samples:
        logging.warning(f"总样本数 ({len(df)}) 过少，无法保证验证集覆盖所有 {num_classes} 个类别。将禁用分层抽样。")
        stratify_param = None
    elif min_samples < 2:
        logging.warning(f"意图 '{intent_counts.idxmin()}' 的样本数 ({min_samples}) 过少，无法进行分层抽样。将禁用分层。")
        stratify_param = None

    # 划分数据集
    df_train, df_val = train_test_split(df, test_size=TEST_SET_SIZE, random_state=42, stratify=stratify_param)
    logging.info(f"训练集大小: {len(df_train)}, 验证集大小: {len(df_val)}")

    # 初始化分词器和模型
    logging.info(f"加载预训练模型: '{MODEL_NAME}'")
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels)

    # 创建数据加载器
    train_dataset = IntentDataset(
        texts=df_train.text.to_numpy(),
        labels=df_train.intent.to_numpy(),
        tokenizer=tokenizer,
        max_len=MAX_LEN,
        label_map=label_map
    )
    train_data_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

    val_dataset = IntentDataset(
        texts=df_val.text.to_numpy(),
        labels=df_val.intent.to_numpy(),
        tokenizer=tokenizer,
        max_len=MAX_LEN,
        label_map=label_map
    )
    val_data_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

    # 设置设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    logging.info(f"使用设备: {device}")

    # 设置优化器和调度器
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE) # correct_bias is deprecated and default is False
    total_steps = len(train_data_loader) * NUM_EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=total_steps
    )

    loss_fn = torch.nn.CrossEntropyLoss().to(device)

    # 训练循环
    best_accuracy = 0
    for epoch in range(NUM_EPOCHS):
        logging.info(f'--- Epoch {epoch + 1}/{NUM_EPOCHS} ---')
        
        train_acc, train_loss = train_epoch(
            model, train_data_loader, loss_fn, optimizer, device, scheduler, len(df_train)
        )
        logging.info(f'训练集损失: {train_loss:.4f}, 准确率: {train_acc:.4f}')

        val_acc, val_loss = eval_model(
            model, val_data_loader, loss_fn, device, len(df_val)
        )
        logging.info(f'验证集损失: {val_loss:.4f}, 准确率: {val_acc:.4f}')

        if val_acc > best_accuracy:
            logging.info(f"验证集准确率提升，保存模型到 '{MODEL_SAVE_PATH}'")
            if not os.path.exists(MODEL_SAVE_PATH):
                os.makedirs(MODEL_SAVE_PATH)
            model.save_pretrained(MODEL_SAVE_PATH, safe_serialization=False)
            tokenizer.save_pretrained(MODEL_SAVE_PATH)
            # 保存标签映射
            with open(os.path.join(MODEL_SAVE_PATH, 'label_map.json'), 'w', encoding='utf-8') as f:
                json.dump(label_map, f, ensure_ascii=False, indent=4)
            best_accuracy = val_acc

    logging.info("训练完成！")
    logging.info(f"最佳验证集准确率: {best_accuracy:.4f}")
    logging.info(f"模型已保存到 '{MODEL_SAVE_PATH}' 目录。")
    logging.info("现在可以运行主应用，新的意图分类器将会生效。")

if __name__ == '__main__':
    main()