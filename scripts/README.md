# 🛠️ Chat AI 脚本目录

## 📋 目录结构

### 🧪 testing/ - 测试脚本
包含各种功能测试、性能测试和验证脚本。

**主要文件:**
- `test_optimization.py` - 轻量级优化效果测试
- `test_redis_monitoring.py` - Redis缓存和监控功能测试
- `test_comprehensive_performance.py` - 综合性能测试
- `test_deployment_fix.py` - 部署修复验证测试
- `verify_deployment.py` - 部署验证脚本
- `verify_fixes.py` - 修复验证脚本

### 🚀 optimization/ - 优化脚本
包含自动化优化工具和性能调优脚本。

**计划添加的脚本:**
- `optimize_css.py` - CSS文件压缩优化
- `optimize_js.py` - JavaScript文件压缩优化
- `optimize_images.py` - 图片压缩优化
- `generate_manifest.py` - 资源清单生成
- `build_frontend.py` - 前端自动化构建

### 🔄 migration/ - 迁移脚本
包含数据库迁移和版本升级脚本。

**计划添加的脚本:**
- `migrate_data.py` - 数据库迁移主脚本
- `migrate_products.py` - 产品数据迁移
- `migrate_policies.py` - 政策数据迁移
- `verify_migration.py` - 迁移验证脚本

## 🎯 使用指南

### 🧪 运行测试
```bash
# 测试轻量级优化效果
python scripts/testing/test_optimization.py

# 测试Redis和监控功能
python scripts/testing/test_redis_monitoring.py

# 综合性能测试
python scripts/testing/test_comprehensive_performance.py

# 验证部署状态
python scripts/testing/verify_deployment.py
```

### 🚀 执行优化
```bash
# 前端资源优化（计划中）
python scripts/optimization/build_frontend.py

# 数据库迁移（计划中）
python scripts/migration/migrate_data.py
```

## 📝 脚本开发规范

### 🔧 脚本结构
每个脚本应包含：
1. **文档字符串** - 说明脚本功能和用法
2. **导入部分** - 必要的库导入
3. **配置部分** - 可配置的参数
4. **主要功能** - 核心逻辑实现
5. **测试部分** - 基本的功能验证
6. **主函数** - `if __name__ == "__main__":` 入口

### 📊 输出格式
- 使用统一的日志格式
- 提供进度指示
- 输出清晰的结果摘要
- 包含错误处理和异常信息

### 🔍 错误处理
- 捕获并处理常见异常
- 提供有意义的错误信息
- 支持调试模式输出
- 优雅地处理中断信号

## 🚀 快速开始

### 验证当前系统状态
```bash
# 快速验证所有功能
python scripts/testing/test_optimization.py
python scripts/testing/test_redis_monitoring.py
```

### 性能基准测试
```bash
# 运行综合性能测试
python scripts/testing/test_comprehensive_performance.py
```

### 部署验证
```bash
# 验证部署配置
python scripts/testing/verify_deployment.py
```

## 📋 脚本清单

| 脚本名称 | 功能 | 状态 | 用途 |
|----------|------|------|------|
| `test_optimization.py` | 优化效果测试 | ✅ 完成 | 验证轻量级优化效果 |
| `test_redis_monitoring.py` | Redis监控测试 | ✅ 完成 | 验证缓存和监控功能 |
| `test_comprehensive_performance.py` | 综合性能测试 | ✅ 完成 | 全面性能评估 |
| `verify_deployment.py` | 部署验证 | ✅ 完成 | 验证部署状态 |
| `verify_fixes.py` | 修复验证 | ✅ 完成 | 验证问题修复 |
| `optimize_css.py` | CSS优化 | 📋 计划 | 前端CSS压缩 |
| `optimize_js.py` | JS优化 | 📋 计划 | JavaScript压缩 |
| `migrate_data.py` | 数据迁移 | 📋 计划 | 数据库迁移 |

## 🔧 开发新脚本

### 添加测试脚本
新的测试脚本应放在 `testing/` 目录中，并遵循命名规范：
- `test_*.py` - 功能测试
- `verify_*.py` - 验证脚本
- `benchmark_*.py` - 性能基准测试

### 添加优化脚本
优化脚本应放在 `optimization/` 目录中：
- `optimize_*.py` - 优化工具
- `build_*.py` - 构建脚本
- `compress_*.py` - 压缩工具

### 添加迁移脚本
迁移脚本应放在 `migration/` 目录中：
- `migrate_*.py` - 迁移工具
- `upgrade_*.py` - 升级脚本
- `convert_*.py` - 转换工具

记住：每个新脚本都应该包含完整的文档和错误处理！
