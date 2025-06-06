# 聊天机器人意图模型使用与维护手册

## 1. 简介

欢迎使用由机器学习驱动的新一代意图识别系统！

本系统采用 `transformers` 框架下的中文预训练模型（如 `bert-base-chinese`）进行微调，能够更精准、更智能地理解用户的自然语言查询。与旧的纯规则系统相比，它最大的优势在于**可学习、可进化**。

本手册将指导您如何进行初次设置，以及如何在日常使用中不断优化和扩展您的意图识别模型。

---

## 2. 系统核心文件

了解以下几个关键文件将帮助您更好地维护本系统：

-   **`src/models/intent_model/` (目录)**
    -   **作用**: 存放微调后最终生成的模型文件、分词器配置文件以及意图标签映射表 (`label_map.json`)。
    -   **注意**: 这个目录是自动生成的，您**不应**手动修改其中的内容。

-   **`data/intent_training_data.csv` (数据文件)**
    -   **作用**: **这是您最常打交道的文件**。它包含了所有用于训练模型的“教材”（用户语料和对应的意图标签）。模型的表现好坏直接取决于这份数据的质量。

-   **`src/app/intent/trainer.py` (训练脚本)**
    -   **作用**: 用于训练模型的独立脚本。它会读取 `data/intent_training_data.csv` 的内容，运行训练流程，并最终将生成的新模型保存在 `src/models/intent_model/` 目录中。

-   **`src/app/intent/classifier.py` (分类器模块)**
    -   **作用**: 一个封装了模型加载和预测逻辑的Python类。主应用通过它来使用训练好的模型。

-   **`src/app/chat/handler.py` (核心聊天逻辑)**
    -   **作用**: 在这个文件中，我们调用 `IntentClassifier` 来识别意图，并根据识别出的意图执行相应的业务逻辑（如回答价格、推荐商品等）。

---

## 3. 首次安装与设置

在您第一次运行或部署此项目时，请遵循以下步骤：

#### 第1步：安装项目依赖

打开您的项目终端，运行以下命令来安装所有必需的Python库。此命令会读取 `requirements.txt` 文件并自动完成安装。

```bash
pip install -r requirements.txt
```

#### 第2步：首次训练模型

在依赖安装完成后，运行训练脚本来生成您的第一个意图识别模型。

```bash
python src/app/intent/trainer.py
```

这个过程可能需要几分钟，因为它需要从网上下载预训练的BERT模型。当您看到类似以下的输出，并且程序没有报错时，就代表训练成功了。

```
...
INFO - 验证集准确率提升，保存模型到 'src/models/intent_model'
...
INFO - 训练完成！
INFO - 模型已保存到 'src/models/intent_model' 目录。
```

训练成功后，您的项目根目录下会出现一个新的 `src/models/intent_model` 文件夹。

**完成以上两步后，您的系统便已准备就绪，可以正常启动和使用了。**

---

## 4. 如何优化与扩展模型（日常维护）

这是本手册的核心。您的工作流程将是：**发现问题 -> 标注数据 -> 重新训练 -> 重启服务**。

### 场景一：修正一个错误的意图识别

当您发现机器人错误地理解了用户的某句话时，您可以像教一个学生一样“纠正”它。

**示例**: 用户说 “除了苹果还有别的吗”，机器人错误地识别为 `request_recommendation` (请求推荐)，但您希望它被识别为 `inquiry_availability` (询问库存)。

#### 操作流程：

1.  **打开数据文件**:
    用编辑器打开 [`data/intent_training_data.csv`](data/intent_training_data.csv)。

2.  **添加正确标注**:
    在文件末尾添加一行或多行“正确答案”，告诉模型这类句子应该是什么意图。

    ```csv
    # data/intent_training_data.csv

    text,intent
    ... (已有数据)
    "除了苹果还有别的吗",inquiry_availability
    "还有其他水果吗",inquiry_availability
    ```

3.  **重新训练**:
    保存文件后，回到终端，再次运行训练脚本。

    ```bash
    python src/app/intent/trainer.py
    ```
    脚本会自动加载包含新数据的完整数据集，训练一个更聪明的模型，并覆盖 `src/models/intent_model/` 里的旧模型。

4.  **重启服务**:
    训练完成后，重启您的主应用（例如 `src/app/main.py`）。新的模型将被加载，下次机器人再遇到类似问题时，就会做出正确的判断。

### 场景二：增加一个全新的意图

假设您希望机器人能够处理用户的“投诉” (`complaint`) 意图。

#### 操作流程：

1.  **添加新意图的数据**:
    在 [`data/intent_training_data.csv`](data/intent_training_data.csv) 文件中，添加几个描述新意图的典型句子。

    ```csv
    # data/intent_training_data.csv

    text,intent
    ... (已有数据)
    "你们的水果不新鲜",complaint
    "送货太慢了，我很不满意",complaint
    "客服态度不好",complaint
    ```

2.  **在代码中处理新意图**:
    打开 [`src/app/chat/handler.py`](src/app/chat/handler.py)，在 `handle_chat_message` 方法中，找到意图分发的 `if/elif` 逻辑块，为新的 `complaint` 意图添加一个处理分支。

    ```python
    # src/app/chat/handler.py -> handle_chat_message()

    ...
    elif intent == 'inquiry_policy':
        final_response = self.handle_policy_question(user_input_processed)

    # --- 新增的处理分支 ---
    elif intent == 'complaint':
        final_response = "非常抱歉给您带来了不好的体验，我们会立刻跟进处理您反馈的问题。"
    # --- 新增结束 ---

    elif intent == 'inquiry_price_or_buy' or intent == 'inquiry_availability':
    ...
    ```

3.  **重新训练和重启**:
    和场景一完全一样：
    -   运行 `python src/app/intent/trainer.py` 进行训练。
    -   重启您的主应用。

现在，您的机器人就学会了如何识别并回应投诉了！

---

## 5. 最佳实践

-   **数据越多越好**: 模型的表现与数据量正相关。为每个意图类别提供至少10-20个不同说法、不同措辞的样本，模型效果会更好。
-   **数据要均衡**: 尽量保证每个意图类别的样本数量大致相当，避免某个类别样本过多而其他类别过少。
-   **定期回顾**: 可以定期检查机器人的聊天记录，找出识别错误的例子，并将其作为新的训练数据加入到您的 `.csv` 文件中，持续迭代优化。

祝您使用愉快！