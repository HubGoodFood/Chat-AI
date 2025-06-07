# 测试文件夹

这个文件夹包含了项目的所有测试、调试和验证文件。

## 文件分类

### 🧪 单元测试文件
- `test_*.py` - 各种功能模块的单元测试
- `test_numbers.py` - 数字处理测试
- `test_policy.py` - 政策管理测试

### 🔍 功能测试文件
- `test_intent_*.py` - 意图识别相关测试
- `test_chat_*.py` - 聊天功能测试
- `test_product_*.py` - 产品管理测试
- `test_recommendation_*.py` - 推荐引擎测试
- `test_api_*.py` - API接口测试

### 🐛 调试文件
- `debug_*.py` - 各种调试脚本
- `check_*.py` - 问题检查脚本

### 📊 综合测试
- `comprehensive_*.py` - 综合功能测试
- `final_*.py` - 最终验证测试
- `verify_*.py` - 验证脚本

### 🎭 演示和模拟
- `demo_*.py` - 功能演示脚本
- `simulate_*.py` - 问题模拟脚本

### 🌐 前端测试
- `test_frontend.html` - 前端功能测试页面

## 运行测试

### 运行所有测试
```bash
# 从项目根目录运行
python -m pytest tests/ -v
```

### 运行特定测试
```bash
# 运行意图识别测试
python tests/test_intent_improvement.py

# 运行聊天集成测试
python tests/test_chat_integration.py

# 运行推荐引擎测试
python tests/test_recommendation_engine.py
```

### 运行调试脚本
```bash
# 调试推荐引擎
python tests/debug_recommendation_engine.py

# 检查特定问题
python tests/check_specific_issues.py
```

## 注意事项

1. **文件命名规范**：
   - 测试文件以 `test_` 开头
   - 调试文件以 `debug_` 开头
   - 检查文件以 `check_` 开头

2. **新增测试文件**：
   - 所有新的测试文件都应该放在这个文件夹中
   - 根目录的 `.gitignore` 会忽略根目录中的测试文件

3. **测试数据**：
   - 测试使用的数据文件应该放在 `data/` 文件夹中
   - 或者在测试文件中使用模拟数据

4. **依赖关系**：
   - 运行测试前确保已安装所有依赖：`pip install -r requirements.txt`
   - 某些测试可能需要特定的环境变量或配置
