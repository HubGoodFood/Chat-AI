# Render部署验证清单

## 🎯 部署前检查

### ✅ 配置文件验证

- [ ] **render.yaml配置正确**
  - [ ] 使用正确的依赖文件：`requirements.txt`
  - [ ] 使用正确的gunicorn配置：`gunicorn.conf.py`
  - [ ] Redis已禁用：`REDIS_ENABLED: false`
  - [ ] 模型类型正确：`MODEL_TYPE: lightweight`

- [ ] **环境变量设置**
  - [ ] `FLASK_ENV=production`
  - [ ] `REDIS_ENABLED=false`
  - [ ] `MODEL_TYPE=lightweight`
  - [ ] `CACHE_ENABLED=true`
  - [ ] `MONITORING_ENABLED=true`
  - [ ] `DEEPSEEK_API_KEY`（在Render Dashboard中设置）

### ✅ 代码验证

- [ ] **依赖文件存在**
  - [ ] `requirements.txt`存在且内容正确
  - [ ] `gunicorn.conf.py`存在且配置正确

- [ ] **关键文件检查**
  - [ ] `app.py`作为WSGI入口点
  - [ ] `src/app/main.py`主应用文件
  - [ ] `src/config/settings.py`配置文件

## 🚀 部署步骤

### 1. 推送代码
```bash
git add .
git commit -m "准备Render部署"
git push
```

### 2. Render配置
1. 在Render Dashboard中创建新的Web Service
2. 连接GitHub仓库
3. 设置环境变量（特别是DEEPSEEK_API_KEY）
4. 选择starter计划（足够使用）

### 3. 部署监控
- 查看构建日志
- 确认没有Redis连接错误
- 确认没有LLM客户端错误
- 验证应用启动成功

## 🔍 部署后验证

### ✅ 功能测试

- [ ] **基础功能**
  - [ ] 应用可以正常访问
  - [ ] 聊天界面加载正常
  - [ ] 产品查询功能正常

- [ ] **缓存功能**
  - [ ] 内存缓存工作正常
  - [ ] 没有Redis连接错误

- [ ] **LLM功能**
  - [ ] LLM客户端初始化成功
  - [ ] AI回复功能正常（如果设置了API密钥）

### ✅ 性能验证

- [ ] **响应时间**
  - [ ] 首次加载 < 5秒
  - [ ] 后续请求 < 2秒

- [ ] **内存使用**
  - [ ] 内存使用 < 512MB
  - [ ] 没有内存泄漏

- [ ] **错误率**
  - [ ] 没有500错误
  - [ ] 日志中没有严重错误

## 🛠️ 常见问题解决

### Redis连接错误
```
Redis连接失败: Error 111 connecting to localhost:6379
```
**解决方案：** 确认`REDIS_ENABLED=false`已设置

### LLM客户端错误
```
Client.__init__() got an unexpected keyword argument 'proxies'
```
**解决方案：** 已在代码中修复，重新部署即可

### 依赖安装失败
```
ERROR: Could not find a version that satisfies the requirement
```
**解决方案：** 检查`requirements.txt`文件是否存在且正确

### 内存不足
```
MemoryError: Unable to allocate
```
**解决方案：** 确认使用轻量级模型配置

## 📊 性能基准

| 指标 | 目标值 | 实际值 |
|------|--------|--------|
| 启动时间 | < 30秒 | _____ |
| 内存使用 | < 512MB | _____ |
| 响应时间 | < 2秒 | _____ |
| 错误率 | < 1% | _____ |

## 🎉 部署成功标志

- ✅ 应用可以正常访问
- ✅ 没有Redis连接错误
- ✅ 没有LLM客户端错误
- ✅ 聊天功能正常工作
- ✅ 内存使用在合理范围内
- ✅ 响应时间满足要求

## 📞 获取帮助

如果遇到问题：
1. 查看 `docs/deployment/render_troubleshooting.md`
2. 运行本地诊断：`python fix_deployment_issues.py`
3. 检查Render部署日志
4. 在GitHub仓库中创建issue
