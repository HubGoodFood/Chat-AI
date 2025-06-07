# Chat AI 应用启动脚本
# 支持 Redis 和纯内存缓存两种模式

param(
    [switch]$WithRedis,
    [switch]$Help
)

if ($Help) {
    Write-Host "Chat AI 应用启动脚本" -ForegroundColor Green
    Write-Host ""
    Write-Host "用法:"
    Write-Host "  .\start_app.ps1           # 使用内存缓存启动（默认）"
    Write-Host "  .\start_app.ps1 -WithRedis # 使用 Redis 缓存启动"
    Write-Host "  .\start_app.ps1 -Help      # 显示帮助信息"
    Write-Host ""
    Write-Host "注意："
    Write-Host "  - 使用 -WithRedis 参数前，请确保 Redis 服务器正在运行"
    Write-Host "  - 默认模式使用内存缓存，无需额外配置"
    exit
}

Write-Host "🚀 启动 Chat AI 应用..." -ForegroundColor Green

if ($WithRedis) {
    Write-Host "📡 检查 Redis 连接..." -ForegroundColor Yellow
    
    # 检查 Redis 是否可用
    try {
        $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
        if ($redisTest.TcpTestSucceeded) {
            Write-Host "✅ Redis 服务器连接正常" -ForegroundColor Green
            $env:REDIS_ENABLED = "true"
            $env:REDIS_URL = "redis://localhost:6379/0"
        } else {
            Write-Host "❌ Redis 服务器连接失败" -ForegroundColor Red
            Write-Host "💡 提示：请先启动 Redis 服务器，或使用内存缓存模式" -ForegroundColor Yellow
            Write-Host "   启动 Redis: redis-server" -ForegroundColor Cyan
            Write-Host "   或使用内存模式: .\start_app.ps1" -ForegroundColor Cyan
            exit 1
        }
    } catch {
        Write-Host "❌ 无法检查 Redis 连接: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "💡 切换到内存缓存模式..." -ForegroundColor Yellow
        $env:REDIS_ENABLED = "false"
    }
} else {
    Write-Host "💾 使用内存缓存模式" -ForegroundColor Cyan
    $env:REDIS_ENABLED = "false"
}

Write-Host "🔧 配置环境变量..." -ForegroundColor Yellow
Write-Host "   REDIS_ENABLED = $($env:REDIS_ENABLED)" -ForegroundColor Gray

if ($env:REDIS_ENABLED -eq "true") {
    Write-Host "   REDIS_URL = $($env:REDIS_URL)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🌟 启动应用服务器..." -ForegroundColor Green
Write-Host "   访问地址: http://localhost:5000" -ForegroundColor Cyan
Write-Host "   管理接口: http://localhost:5000/admin/cache-stats" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止应用" -ForegroundColor Yellow
Write-Host "=" * 50

# 启动应用
try {
    python src/app/main.py
} catch {
    Write-Host ""
    Write-Host "❌ 应用启动失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 故障排除建议:" -ForegroundColor Yellow
    Write-Host "1. 检查 Python 是否已安装: python --version" -ForegroundColor Gray
    Write-Host "2. 检查依赖是否已安装: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "3. 检查当前目录是否正确" -ForegroundColor Gray
    Write-Host "4. 查看详细错误日志" -ForegroundColor Gray
    exit 1
}
