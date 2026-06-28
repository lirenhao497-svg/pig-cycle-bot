@echo off
chcp 65001 >nul
title 配置自动运行任务

echo ========================================
echo    猪周期数据系统 - 配置自动运行
echo ========================================
echo.

cd /d "%~dp0"

echo 正在创建Windows任务计划...
echo 任务名称：猪周期数据系统-每日抓取
echo 运行时间：每天上午10:00
echo.

:: 获取Python路径
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
if "%PYTHON_PATH%"=="" (
    echo ❌ 找不到Python，请先安装Python
    pause
    exit /b 1
)

echo Python路径：%PYTHON_PATH%
echo 项目路径：%~dp0
echo.

:: 创建任务计划
schtasks /create /tn "猪周期数据系统-每日抓取" /tr "\"%PYTHON_PATH%\" \"%~dp0main.py\"" /sc daily /st 10:00 /f

if %errorlevel% equ 0 (
    echo.
    echo ✅ 任务计划创建成功！
    echo.
    echo 📅 运行时间：每天上午10:00
    echo 💾 数据文件：data\hog_data.db
    echo 📋 日志文件：logs\app.log
    echo.
    echo 💡 提示：
    echo    - 电脑开着就会自动运行
    echo    - 可以在「任务计划程序」里查看和修改
    echo    - 如果当天10点前电脑没开，当天就不会跑
) else (
    echo.
    echo ❌ 创建失败，可能需要管理员权限
    echo.
    echo 💡 请右键点击此文件，选择「以管理员身份运行」
)

echo.
echo ========================================
pause >nul
