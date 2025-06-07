@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo    Chat AI 应用启动脚本
echo ==========================================
echo.

if "%1"=="--help" (
    echo 用法:
    echo   start_app.bat           # 使用内存缓存启动（默认）
    echo   start_app.bat --redis   # 使用 Redis 缓存启动
    echo   start_app.bat --help    # 显示帮助信息
    echo.
    echo 注意:
    echo   - 使用 --redis 参数前，请确保 Redis 服务器正在运行
    echo   - 默认模式使用内存缓存，无需额外配置
    goto :eof
)

if "%1"=="--redis" (
    echo [INFO] 检查 Redis 连接...
    
    REM 检查 Redis 是否可用
    netstat -an | findstr ":6379" >nul
    if errorlevel 1 (
        echo [ERROR] Redis 服务器连接失败
        echo [HINT] 请先启动 Redis 服务器，或使用内存缓存模式
        echo        启动 Redis: redis-server
        echo        或使用内存模式: start_app.bat
        pause
        exit /b 1
    ) else (
        echo [OK] Redis 服务器连接正常
        set REDIS_ENABLED=true
        set REDIS_URL=redis://localhost:6379/0
    )
) else (
    echo [INFO] 使用内存缓存模式
    set REDIS_ENABLED=false
)

echo.
echo [INFO] 配置环境变量...
echo        REDIS_ENABLED = %REDIS_ENABLED%
if "%REDIS_ENABLED%"=="true" (
    echo        REDIS_URL = %REDIS_URL%
)

echo.
echo [INFO] 启动应用服务器...
echo        访问地址: http://localhost:5000
echo        管理接口: http://localhost:5000/admin/cache-stats
echo.
echo 按 Ctrl+C 停止应用
echo ==========================================

REM 启动应用
python src/app/main.py

if errorlevel 1 (
    echo.
    echo [ERROR] 应用启动失败
    echo.
    echo 故障排除建议:
    echo 1. 检查 Python 是否已安装: python --version
    echo 2. 检查依赖是否已安装: pip install -r requirements.txt
    echo 3. 检查当前目录是否正确
    echo 4. 查看详细错误日志
    pause
    exit /b 1
)
