# 智能生鲜聊天助手 (Smart Fresh AI Chat)

一个基于 Flask 构建的智能生鲜购物聊天助手，支持中文自然语言交互、智能意图识别、产品推荐和多轮对话。集成了先进的混合意图分类器和智能推荐引擎，为用户提供流畅的购物体验。

## ✨ 核心特性

### 🧠 智能意图识别
- **混合分类器架构**：结合规则匹配、机器学习模型和关键词匹配的三层策略
- **中文口语化支持**：准确识别"卖不？"、"有不？"等口语化表达
- **高准确率**：意图识别准确率达到 100%（关键测试用例）
- **多种意图支持**：商品查询、价格询问、推荐请求、问候等

### 🛒 智能产品管理
- **快速模糊匹配**：支持产品名称的模糊搜索和智能纠错
- **分类推荐**：基于产品类别的智能推荐系统
- **当季推荐**：自动推荐当季新鲜产品
- **热门产品**：基于用户偏好的热门产品推荐

### 💬 自然对话体验
- **多轮对话**：支持上下文理解和对话历史
- **澄清交互**：当查询不明确时主动澄清用户需求
- **个性化回复**：温暖友好的中文回复风格
- **按钮交互**：支持点击式产品选择

### 🔧 技术架构
- **Flask Web 框架**：轻量级、高性能的 Web 服务
- **RESTful API**：标准化的 API 接口设计
- **缓存优化**：智能缓存机制提升响应速度
- **可选 LLM 集成**：支持 DeepSeek 等大语言模型增强对话能力

## 🚀 快速开始

### 前置条件

- Python 3.11 及以上版本
- pip 包管理器
- (可选) DeepSeek API Key，用于启用高级对话功能

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/HubGoodFood/Chat-AI.git
   cd Chat-AI
   ```

2. **创建虚拟环境**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**（可选）
   ```bash
   # DeepSeek LLM API Key（可选）
   export DEEPSEEK_API_KEY=你的_api_key
   
   # 其他配置（使用默认值即可）
   export PRODUCT_DATA_FILE=data/products.csv
   export INTENT_TRAINING_DATA_FILE=data/intent_training_data.csv
   export POLICY_FILE=data/policy.json
   export PORT=5000
   export FLASK_DEBUG=true
   export APP_ENV=development
   ```

5. **启动应用**
   ```bash
   python src/app/main.py
   ```

6. **访问界面**
   
   打开浏览器访问 `http://localhost:5000/`

## 📊 数据格式

### 产品数据 (CSV)

产品数据文件 `data/products.csv` 需包含以下列：

| 列名 | 描述 | 示例 | 必需 |
|------|------|------|------|
| ProductName | 产品名称 | 苹果 | ✅ |
| Specification | 规格 | 1kg | ✅ |
| Price | 单价 | 3.5 | ✅ |
| Unit | 单位 | kg | ✅ |
| Category | 分类 | 水果 | ✅ |
| Description | 产品描述 | 新鲜红富士苹果 | ❌ |
| IsSeasonal | 是否当季 | True/False | ❌ |
| Keywords | 搜索关键词 | 红富士,水果 | ❌ |

**示例数据：**
```csv
ProductName,Specification,Price,Unit,Category,Description,IsSeasonal,Keywords
苹果,1kg,3.5,kg,水果,新鲜红富士苹果,True,红富士,水果
香蕉,500g,2.8,斤,水果,进口香蕉,True,进口,热带水果
```

### 意图训练数据

系统支持以下意图类型：
- `inquiry_availability` - 商品可用性查询
- `inquiry_price_or_buy` - 价格查询或购买意图
- `request_recommendation` - 推荐请求
- `greeting` - 问候语
- `identity_query` - 身份查询

## 🏗️ 项目结构

```
Chat-AI/
├── data/                           # 数据文件
│   ├── products.csv               # 产品数据
│   ├── intent_training_data.csv   # 意图训练数据
│   └── policy.json               # 平台政策
├── src/                          # 源代码
│   ├── app/                      # Flask 应用
│   │   ├── chat/                 # 聊天处理逻辑
│   │   │   └── handler.py        # 主要聊天处理器
│   │   ├── intent/               # 意图识别
│   │   │   ├── classifier.py     # 意图分类器
│   │   │   ├── hybrid_classifier.py  # 混合分类器
│   │   │   └── improved_trainer.py   # 改进的训练器
│   │   ├── products/             # 产品管理
│   │   │   ├── manager.py        # 产品管理器
│   │   │   └── recommendation_engine.py  # 推荐引擎
│   │   ├── policy/               # 政策管理
│   │   └── main.py               # 应用入口
│   ├── config/                   # 配置管理
│   │   └── settings.py           # 配置设置
│   ├── core/                     # 核心模块
│   └── models/                   # 训练模型
│       └── hybrid_intent_model/  # 混合意图模型
├── templates/                    # HTML 模板
│   └── index.html               # 主页面
├── static/                      # 静态资源
│   ├── style.css               # 样式文件
│   ├── chat.js                 # 前端交互
│   └── images/                 # 图片资源
├── docs/                       # 文档
├── tests/                      # 测试文件
├── requirements.txt            # Python 依赖
└── README.md                   # 项目说明
```

## 🔧 配置选项

通过环境变量自定义运行参数：

| 环境变量 | 描述 | 默认值 |
|----------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek LLM API Key | 无 |
| `PRODUCT_DATA_FILE` | 产品数据文件路径 | `data/products.csv` |
| `INTENT_TRAINING_DATA_FILE` | 意图训练数据路径 | `data/intent_training_data.csv` |
| `POLICY_FILE` | 平台政策文件路径 | `data/policy.json` |
| `PORT` | Flask 应用端口 | `5000` |
| `FLASK_DEBUG` | 调试模式 | `true` |
| `APP_ENV` | 应用环境 | `development` |

## 📡 API 接口

### 聊天接口

**POST** `/chat`

```json
{
  "message": "苹果多少钱？",
  "user_id": "user123"
}
```

**响应示例：**
```json
{
  "response": "我们的苹果现在是3.5元/kg，新鲜红富士苹果，您需要多少？",
  "product_suggestions": [
    {
      "text": "苹果 - 3.5元/kg",
      "payload": "苹果"
    }
  ]
}
```

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行特定测试
python -m pytest tests/test_intent.py -v

# 运行意图识别测试
python test_intent_improvement.py
```

## 📈 最新改进

### v2.0 - 中文意图识别优化 (2024)

- ✅ **解决口语化表达识别问题**：完美支持"卖不？"、"有不？"等表达
- ✅ **混合分类器架构**：三层策略确保高准确率
- ✅ **智能推荐引擎**：基于类别和相似度的智能推荐
- ✅ **中文标点符号优化**：正确处理中文标点符号
- ✅ **训练数据扩充**：新增大量口语化训练样本

详细改进内容请查看 [INTENT_IMPROVEMENT_SUMMARY.md](INTENT_IMPROVEMENT_SUMMARY.md)

## 🤝 贡献指南

欢迎提出 Issue 或提交 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范

- 保持代码风格一致
- 添加适当的测试用例
- 更新相关文档
- 确保所有测试通过

## 📄 许可证

本项目采用 MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目地址：[https://github.com/HubGoodFood/Chat-AI](https://github.com/HubGoodFood/Chat-AI)
- 问题反馈：[Issues](https://github.com/HubGoodFood/Chat-AI/issues)

---

**Made with ❤️ for fresh food lovers**
