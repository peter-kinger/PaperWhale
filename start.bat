@echo off
chcp 65001 >nul
title AI文献阅读工具

echo.
echo 正在启动AI文献阅读工具...
echo.

cd /d "%~dp0"

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装Python，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 检查依赖
python -c "import pdfplumber, requests, json" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖...
    pip install pdfplumber requests -q
)

:: 启动主程序
python main.py

pause