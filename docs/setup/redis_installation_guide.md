# Redis 安装和配置指南

## Windows 系统 Redis 安装

### 方法1：使用 Chocolatey（推荐）

1. **安装 Chocolatey**（如果还没有安装）：
   ```powershell
   # 以管理员身份运行 PowerShell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **安装 Redis**：
   ```powershell
   choco install redis-64
   ```

3. **启动 Redis 服务**：
   ```powershell
   redis-server
   ```

### 方法2：手动下载安装

1. **下载 Redis for Windows**：
   - 访问：https://github.com/microsoftarchive/redis/releases
   - 下载最新版本的 Redis-x64-*.zip

2. **解压并配置**：
   ```bash
   # 解压到 C:\Redis
   # 打开命令提示符，进入 Redis 目录
   cd C:\Redis
   redis-server.exe redis.windows.conf
   ```

### 方法3：使用 Docker（推荐用于开发）

1. **安装 Docker Desktop**

2. **运行 Redis 容器**：
   ```bash
   docker run -d --name redis-cache -p 6379:6379 redis:latest
   ```

3. **验证 Redis 运行**：
   ```bash
   docker exec -it redis-cache redis-cli ping
   ```

## 验证 Redis 安装

### 测试连接：
```bash
# 打开新的命令提示符
redis-cli ping
# 应该返回：PONG
```

### 基本操作测试：
```bash
redis-cli
127.0.0.1:6379> set test "Hello Redis"
127.0.0.1:6379> get test
127.0.0.1:6379> exit
```

## 配置 Chat AI 项目

### 环境变量设置：
```bash
# 在项目根目录创建 .env 文件
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

### 或者在启动时设置：
```bash
set REDIS_ENABLED=true
set REDIS_URL=redis://localhost:6379/0
python src/app/main.py
```

## 故障排除

### 常见问题：

1. **端口被占用**：
   ```bash
   netstat -an | findstr :6379
   ```

2. **防火墙阻止**：
   - 添加 Redis 到 Windows 防火墙例外

3. **权限问题**：
   - 以管理员身份运行命令提示符

### Redis 服务管理：

**启动服务**：
```bash
redis-server
```

**后台运行**：
```bash
redis-server --daemonize yes
```

**停止服务**：
```bash
redis-cli shutdown
```

## 生产环境配置

### Redis 配置文件优化：
```conf
# redis.conf
bind 127.0.0.1
port 6379
timeout 300
tcp-keepalive 60
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 安全配置：
```conf
# 设置密码
requirepass your_secure_password

# 禁用危险命令
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

## 监控和维护

### Redis 性能监控：
```bash
# 实时监控
redis-cli monitor

# 查看信息
redis-cli info

# 查看内存使用
redis-cli info memory
```

### 定期维护：
```bash
# 手动保存数据
redis-cli bgsave

# 查看慢查询
redis-cli slowlog get 10
```

## 快速解决方案

### 方案1：临时禁用Redis（推荐）

如果您暂时不想安装Redis，可以使用内存缓存模式：

**PowerShell:**
```powershell
$env:REDIS_ENABLED="false"
python src/app/main.py
```

**命令提示符:**
```cmd
set REDIS_ENABLED=false
python src/app/main.py
```

### 方案2：快速安装Redis（Windows）

**使用Chocolatey（推荐）:**
```powershell
# 以管理员身份运行PowerShell
choco install redis-64
redis-server
```

**使用Docker:**
```bash
docker run -d --name redis-cache -p 6379:6379 redis:latest
```

### 方案3：验证Redis连接

**检查Redis是否运行:**
```bash
# 检查端口
netstat -an | findstr :6379

# 测试连接
redis-cli ping
```

## 常见错误解决

### Error 10061: 连接被拒绝

**原因**: Redis服务器未运行

**解决方案**:
1. 启动Redis服务器: `redis-server`
2. 或禁用Redis: `set REDIS_ENABLED=false`

### 智能缓存系统状态

✅ **好消息**: 即使Redis不可用，智能缓存系统仍然可以正常工作！

- **自动降级**: Redis连接失败时自动使用内存缓存
- **功能完整**: 所有智能缓存功能都可以在内存模式下运行
- **性能优秀**: 内存缓存仍然提供显著的性能提升

### 启动应用的简单方法

**方法1: 内存缓存模式（无需Redis）**
```bash
set REDIS_ENABLED=false && python src/app/main.py
```

**方法2: Redis缓存模式（需要Redis运行）**
```bash
set REDIS_ENABLED=true && python src/app/main.py
```

**方法3: 默认模式（自动检测）**
```bash
python src/app/main.py
```

应用会自动检测Redis是否可用，如果不可用会自动使用内存缓存。
