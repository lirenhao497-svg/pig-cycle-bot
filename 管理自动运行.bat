@echo off
chcp 65001 >nul
title 自动运行任务管理

echo ========================================
echo    猪周期数据系统 - 自动运行管理
echo ========================================
echo.

echo 请选择操作：
echo.
echo   [1] 查看任务状态
echo   [2] 立即运行一次
echo   [3] 删除自动运行任务
echo   [4] 退出
echo.

set /p choice=请输入编号：

if "%choice%"=="1" goto query
if "%choice%"=="2" goto run
if "%choice%"=="3" goto delete
if "%choice%"=="4" goto end

echo 无效输入
pause
goto end

:query
echo.
echo ========================================
echo   查看任务状态
echo ========================================
echo.
schtasks /query /tn "猪周期数据系统-每日抓取" /v /fo list
echo.
pause
goto end

:run
echo.
echo ========================================
echo   立即运行一次
echo ========================================
echo.
schtasks /run /tn "猪周期数据系统-每日抓取"
if %errorlevel% equ 0 (
    echo ✅ 已触发运行
) else (
    echo ❌ 运行失败
)
echo.
pause
goto end

:delete
echo.
echo ========================================
echo   删除自动运行任务
echo ========================================
echo.
echo ⚠️  确定要删除吗？删除后不会再自动运行
echo.
set /p confirm=输入 Y 确认删除：

if /i "%confirm%"=="Y" (
    schtasks /delete /tn "猪周期数据系统-每日抓取" /f
    if %errorlevel% equ 0 (
        echo ✅ 已删除
    ) else (
        echo ❌ 删除失败
    )
) else (
    echo 已取消
)
echo.
pause
goto end

:end
