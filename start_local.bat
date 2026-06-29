@echo off
chcp 65001 >nul
title 猪周期全栈服务

set PROJECT_DIR=C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot
set PYTHON=C:\Users\ll\AppData\Local\Programs\Python\Python313\python.exe

echo ┌─────────────────────────────────────────────┐
echo │  猪周期全栈服务                             │
echo │  Pig Cycle Local Server                     │
echo └─────────────────────────────────────────────┘
echo.

:: Step 1: 构建前端（如果 dist 不存在或源码有更新）
cd /d "%PROJECT_DIR%\web-dashboard"
if not exist "%PROJECT_DIR%\web-dashboard\dist\index.html" (
    echo [1/3] 前端构建...
    call npm run build
    if %errorlevel% neq 0 (
        echo ❌ 前端构建失败
        pause
        exit /b 1
    )
    echo ✅ 前端构建成功
) else (
    echo [1/3] 前端已构建，跳过
)
echo.

:: Step 2: 启动 FastAPI 后端
echo [2/3] 启动 FastAPI 后端 (port 8000)...
echo   数据库: data/hog_data.db
echo   前端:   http://localhost:8000
echo   接口:   http://localhost:8000/api/latest
echo.

:: 如果已有后台服务，先关掉
for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /v /fo csv ^| findstr "uvicorn"') do (
    taskkill /pid %%a /f 2>nul
)

cd /d "%PROJECT_DIR%\web-dashboard"
start "" "%PYTHON%" -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload

:: 等待服务启动
timeout /t 3 /nobreak >nul

:: 验证
curl -s http://localhost:8000/api/latest -o nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ FastAPI 后端启动成功
) else (
    echo ⚠️ 后端启动中，稍后自动检测...
)

echo.
echo [3/3] 服务已就绪
echo.
echo ┌─────────────────────────────────────────────┐
echo │  访问地址                                    │
echo ├─────────────────────────────────────────────┤
echo │  前端:     http://localhost:8000             │
echo │  后端API:  http://localhost:8000/api/latest  │
echo │  API文档:  http://localhost:8000/docs        │
echo └─────────────────────────────────────────────┘
echo.
echo 浏览器打开 http://localhost:8000 即可查看
echo.
echo 按任意键停止服务...
pause >nul

:: 停止后端
taskkill /f /fi "WINDOWTITLE eq uvicorn*" 2>nul
echo ✅ 服务已停止
