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
- **分布式缓存**：Redis + 本地缓存的多层缓存架构
- **性能监控**：实时性能监控和可视化仪表板
- **轻量级ML**：优化的意图分类，减少98.6%依赖大小
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
   # 推荐使用轻量级依赖（优化版）
   pip install -r requirements_lightweight.txt

   # 或使用原版依赖
   pip install -r requirements.txt
   ```

4. **配置环境变量**（可选）
   ```bash
   # DeepSeek LLM API Key（可选）
   export DEEPSEEK_API_KEY=你的_api_key

   # 优化配置（推荐）
   export MODEL_TYPE=lightweight
   export REDIS_ENABLED=true
   export MONITORING_ENABLED=true
   export CACHE_ENABLED=true

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

   - **主聊天界面**: `http://localhost:5000/`
   - **性能监控仪表板**: `http://localhost:5000/monitoring/dashboard`

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
├── 📄 README.md                    # 项目说明（本文件）
├── 📄 PROJECT_STRUCTURE.md         # 详细项目结构说明
├── 📄 app.py                       # 应用入口
├── 📄 requirements_lightweight.txt # 轻量级依赖（推荐）
├── 📄 requirements.txt             # 原版依赖
│
├── 📂 src/                         # 源代码
│   ├── 📂 app/                     # Flask 应用
│   │   ├── 📂 chat/                # 聊天处理逻辑
│   │   ├── 📂 intent/              # 意图识别（轻量级+混合）
│   │   ├── 📂 products/            # 产品管理
│   │   ├── 📂 policy/              # 政策管理
│   │   ├── 📂 monitoring/          # 监控仪表板
│   │   └── 📄 main.py              # 应用入口
│   ├── 📂 core/                    # 核心功能
│   │   ├── 📄 cache.py             # 缓存管理
│   │   ├── 📄 redis_cache.py       # Redis分布式缓存
│   │   └── 📄 performance_monitor.py # 性能监控
│   ├── 📂 config/                  # 配置管理
│   └── 📂 models/                  # 训练模型
│
├── 📂 docs/                        # 📚 文档目录
│   ├── 📂 optimization/            # 🚀 优化文档
│   ├── 📂 guides/                  # 📖 详细指南
│   └── 📂 deployment/              # 🚀 部署文档
│
├── 📂 scripts/                     # 🛠️ 脚本目录
│   ├── 📂 testing/                 # 🧪 测试脚本
│   ├── 📂 optimization/            # 优化脚本
│   └── 📂 migration/               # 迁移脚本
│
├── 📂 config/                      # ⚙️ 配置目录
│   └── 📂 deployment/              # 部署配置
│
├── 📂 data/                        # 📊 数据文件
├── 📂 static/                      # 🎨 静态资源
├── 📂 templates/                   # 🖼️ HTML模板
├── 📂 cache/                       # 💾 缓存文件
└── 📂 tests/                       # 🧪 测试文件
```

> 📖 **详细结构说明**: 查看 `PROJECT_STRUCTURE.md` 了解完整的目录结构和文件组织方式

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
| `MODEL_TYPE` | 模型类型 | `lightweight` |
| `REDIS_ENABLED` | Redis缓存 | `true` |
| `MONITORING_ENABLED` | 性能监控 | `true` |

## 📚 文档导航

### 🚀 **优化和性能**
- **[优化路线图](docs/optimization/FUTURE_OPTIMIZATION_ROADMAP.md)** - 完整的优化计划和优先级
- **[实施检查清单](docs/optimization/IMPLEMENTATION_CHECKLIST.md)** - 逐步实施指南
- **[优化总指南](docs/optimization/OPTIMIZATION_GUIDE.md)** - 轻量级优化总结

### 📖 **详细指南**
- **[数据库迁移指南](docs/guides/DATABASE_MIGRATION_GUIDE.md)** - 从CSV到数据库的完整迁移
- **[前端优化指南](docs/guides/FRONTEND_OPTIMIZATION_GUIDE.md)** - 静态资源优化和CDN配置
- **[API安全优化指南](docs/guides/API_SECURITY_OPTIMIZATION_GUIDE.md)** - API性能和安全加固
- **[Redis监控配置指南](docs/guides/REDIS_MONITORING_SETUP.md)** - 分布式缓存和监控配置

### 🚀 **部署相关**
- **[部署修复指南](docs/deployment/DEPLOYMENT_FIX.md)** - 部署问题解决方案
- **[优化部署配置](config/deployment/)** - 生产环境优化配置

### 🧪 **测试和验证**
- **[测试脚本](scripts/testing/)** - 功能和性能测试脚本
- **[验证工具](scripts/testing/verify_*.py)** - 部署和功能验证工具

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
