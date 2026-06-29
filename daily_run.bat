@echo off
chcp 65001 >nul
title 猪周期爬虫 + 服务更新

set PROJECT_DIR=C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot
set PYTHON=C:\Users\ll\AppData\Local\Programs\Python\Python313\python.exe

echo ┌─────────────────────────────────────────────┐
echo │  猪周期：每日爬虫 + 数据同步                 │
echo │  %date% %time%                              │
echo └─────────────────────────────────────────────┘
echo.

cd /d "%PROJECT_DIR%"

:: Step 1: 运行爬虫
echo [1/5] 运行数据爬虫...
"%PYTHON%" scheduler.py
if %errorlevel% neq 0 (
    echo ⚠️ 爬虫部分失败，继续执行后续步骤
)

:: Step 2: 构建前端（确保 dist 是最新版）
echo.
echo [2/5] 构建前端...
cd /d "%PROJECT_DIR%\web-dashboard"
call npm run build 2>&1
if %errorlevel% equ 0 (
    echo ✅ 前端构建成功
) else (
    echo ⚠️ 前端构建失败，使用旧版本
)

:: Step 3: 重启本地后端服务
echo.
echo [3/5] 重启本地后端服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f 2>nul
)
timeout /t 2 /nobreak >nul

cd /d "%PROJECT_DIR%\web-dashboard"
start "" "%PYTHON%" -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
timeout /t 3 /nobreak >nul

echo ✅ 本地后端已重启

:: Step 4: 上传数据库到 Railway（同步云端数据）
echo.
echo [4/5] 上传数据库到 Railway...
cd /d "%PROJECT_DIR%"
railway service files upload data/hog_data.db /app/data/hog_data.db --overwrite 2>&1
if %errorlevel% equ 0 (
    echo ✅ 数据库已上传到 Railway

    :: 重新部署使Railway加载新数据库
    echo 触发 Railway 重新部署...
    railway service redeploy 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Railway 重新部署中（约30秒后生效）
    ) else (
        echo ⚠️ 重新部署触发失败
    )
) else (
    echo ⚠️ 数据库上传失败，请手动执行 railway service redeploy
)

:: Step 5: 推送代码到 GitHub
echo.
echo [5/5] 推送代码到 GitHub...
git add -A 2>nul
git commit -m "auto: daily update %date%" 2>nul
git push origin main 2>&1
if %errorlevel% equ 0 (
    echo ✅ Git push 成功
) else (
    echo ⚠️ Git push 无变更或失败
)

:: 验证线上
echo.
echo 验证线上 API...
curl -s --connect-timeout 10 https://pig-cycle-bot-production.up.railway.app/api/latest > %TEMP%\railway_check.txt 2>nul
findstr "pig_grain_ratio" %TEMP%\railway_check.txt >nul
if %errorlevel% equ 0 (
    echo ✅ 线上 API 返回正常
) else (
    echo ⚠️ 线上 API 可能尚未部署完成（等30秒后手动刷新即可）
)

echo.
echo ┌─────────────────────────────────────────────┐
echo │  每日任务完成                                │
echo ├─────────────────────────────────────────────┤
echo │  本地:  http://localhost:8000               │
echo │  线上:  https://pig-cycle-bot-production.   │
echo │         up.railway.app/api/latest           │
echo └─────────────────────────────────────────────┘
