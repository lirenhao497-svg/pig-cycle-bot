@echo off
chcp 65001 >nul
echo 🐷 猪周期量化系统 - 启动开发环境
echo ================================
echo.

echo [1/2] 启动后端 API...
start "backend" /B python "C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot\web-dashboard\backend.py"
echo    后端已启动: http://localhost:8000
echo    文档: http://localhost:8000/docs
timeout /t 2 /nobreak >nul

echo.
echo [2/2] 启动前端开发服务器...
cd /d "C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot\web-dashboard"
start "frontend" /B npm run dev
echo    前端已启动: http://localhost:5173
echo.

echo ================================
echo 监控大屏: http://localhost:5173
echo 按任意键停止所有服务...
echo ================================
pause >nul

echo.
echo 停止服务...
taskkill /fi "WINDOWTITLE eq backend" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq frontend" /f >nul 2>&1
echo 已停止.
