# Smart Chat AI

一个基于 Flask 构建的智能聊天助手示例，支持本地 CSV 产品数据管理与快速模糊匹配，可选接入 DeepSeek LLM 实现高级对话与智能推荐。

## 前置条件

- Python 3.11 及以上版本
- pip
- (可选) DeepSeek API Key，用于启用 LLM 功能

## 安装与运行

1. 克隆仓库：
   ```bash
   git clone <仓库地址>
   cd Smart-Chat-AI
   ```

2. 创建并激活虚拟环境：
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   ```bash
   # DeepSeek LLM API Key（可选）
   export DEEPSEEK_API_KEY=你的_api_key
   # 产品 CSV 文件路径（默认 data/products.csv）
   export PRODUCT_DATA_FILE=data/products.csv
   # 意图训练数据路径（默认 data/intent_training_data.csv）
   export INTENT_TRAINING_DATA_FILE=data/intent_training_data.csv
   # 平台政策文件路径（默认 data/policy.json）
   export POLICY_FILE=data/policy.json
   # Flask 端口（默认 5000）
   export PORT=5000
   # 调试模式（true/false）
   export FLASK_DEBUG=true
   # 应用环境（development / production）
   export APP_ENV=development
   ```

5. 启动应用：
   ```bash
   python src/app/main.py
   ```

6. 访问界面：
   打开浏览器访问 `http://localhost:5000/`。

## 产品 CSV 格式

CSV 文件需包含以下列：

- **ProductName**: 产品名称（例如：`苹果`）
- **Specification**: 规格（例如：`1kg`）
- **Price**: 单价（数字）
- **Unit**: 单位（例如：`kg`、`斤`）
- **Category**: 分类（例如：`水果`）
- **Description**: 产品描述（可选）
- **IsSeasonal**: 是否当季，`True` 或 `False`（可选）
- **Keywords**: 自定义搜索关键词，多个关键词使用逗号或空格分隔（可选）

示例：

```csv
ProductName,Specification,Price,Unit,Category,Description,IsSeasonal,Keywords
苹果,1kg,3.5,kg,水果,新鲜红富士苹果,True,红富士,水果
```

## 功能特性

- 基于 Flask 的网页聊天界面，支持自然语言交互。
- 使用 DeepSeek LLM 进行智能产品推荐（可选）。
- 本地 CSV 产品数据缓存与快速模糊匹配。
- 多轮对话与澄清交互，提升用户体验。
- RESTful API 端点，便于二次集成。

## 项目结构

```
.
├── data/               # 原始数据，如 products.csv、policy.json、intent_training_data.csv
├── docs/               # 文档及说明
├── src/                # 源代码目录
│   ├── app/            # Flask 应用及路由、处理逻辑
│   ├── config/         # 配置文件与环境变量加载
│   ├── core/           # 核心模块，如缓存管理
│   ├── app/chat/       # 聊天处理逻辑
│   ├── app/products/   # 产品管理与搜索
│   ├── app/policy/     # 政策管理
│   └── tests/          # 单元测试
├── templates/          # 前端 HTML 模板
├── static/             # 静态资源 (CSS、JS、图片)
├── requirements.txt    # Python 依赖列表
└── README.md           # 项目说明
```

## 配置说明

可通过环境变量自定义运行参数：

- `DEEPSEEK_API_KEY`：DeepSeek LLM API Key，可选，启用高级聊天功能。
- `PRODUCT_DATA_FILE`：产品 CSV 路径，默认为 `data/products.csv`。
- `INTENT_TRAINING_DATA_FILE`：意图训练数据路径，默认为 `data/intent_training_data.csv`。
- `POLICY_FILE`：平台政策文件路径，默认为 `data/policy.json`。
- `PORT`：Flask 应用运行端口，默认为 `5000`。
- `FLASK_DEBUG`：调试模式开关，设置为 `true` 或 `false`。
- `APP_ENV`：应用环境标识（`development` / `production`），影响错误处理和退出策略。

## 使用示例

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 设置环境变量并启动：
   ```bash
   export DEEPSEEK_API_KEY=你的_api_key
   export PRODUCT_DATA_FILE=data/products.csv
   python src/app/main.py
   ```

3. 访问网页界面：
   打开浏览器并访问 `http://localhost:5000/`。

4. 使用 API 调用：
   ```bash
   curl -X POST http://localhost:5000/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "苹果多少钱？", "user_id": "test"}'
   ```

## 测试

```bash
pytest
```

## 贡献指南

欢迎提出 Issue 或提交 PR，
请遵循以下规范：

- Fork 本仓库并在 feature 分支上开发。
- 保持代码风格一致。
- 提交前请确保所有测试通过。
- 在 PR 中详细描述修改内容和动机。

## 许可证

本项目采用 MIT License。