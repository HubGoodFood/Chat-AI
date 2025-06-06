# Smart Chat AI

一个基于 Flask 的简易聊天助手示例，可读取本地产品 CSV 文件并在聊天中推荐商品。

## 安装与运行

1. **准备 Python 环境**
   - 推荐使用 **Python 3.11** 及以上版本。
2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
3. **配置环境变量**
   - `DEEPSEEK_API_KEY`：用于调用 DeepSeek LLM 的 API key（可选）。
   - `PRODUCT_DATA_FILE`：自定义产品 CSV 路径，默认为 `data/products.csv`。
4. **启动应用**
   ```bash
   python src/app/main.py
   ```
   启动后访问 `http://localhost:5000/` 即可进入聊天界面。

## 产品 CSV 格式

CSV 文件需包含以下列：

`ProductName, Specification, Price, Unit, Category, Description (可选), IsSeasonal (可选), Keywords (可选)`

其中 `Keywords` 列可以填入与产品相关的自定义搜索关键词，使用逗号或空格分隔。