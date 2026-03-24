@echo off
REM Windows批处理启动脚本

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo MediaDownloader - Windows启动脚本
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] 错误：找不到Python
    echo [i] 请从 https://www.python.org 下载Python 3.11+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [√] Python版本: %PYTHON_VERSION%

REM 创建虚拟环境
if not exist "venv" (
    echo [i] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo [i] 检查依赖...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1

python -m pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [w] 部分依赖安装失败（可能在非Android环境下）
    echo [i] 继续运行基础版本...
)

if not exist "main.py" (
    echo [X] 错误：找不到 main.py
    pause
    exit /b 1
)

echo.
echo ==========================================
echo [√] 环境准备完成
echo ==========================================
echo.
echo 运行模式选择：
echo 1. 开发模式（本地运行，不构建APK）
echo 2. 调试模式（输出详细日志）
echo 3. 构建APK（需要Buildozer）
echo 4. 清理构建文件
echo.
set /p choice="请选择 [1-4]: "

if "%choice%"=="1" (
    echo [i] 启动应用（开发模式）...
    python main.py
) else if "%choice%"=="2" (
    echo [i] 启动应用（调试模式）...
    set KIVY_LOG_MODE=MIXED
    set KIVY_LOG_LEVEL=debug
    python main.py
) else if "%choice%"=="3" (
    where buildozer >nul 2>&1
    if errorlevel 1 (
        echo [i] 安装Buildozer...
        python -m pip install buildozer cython
    )
    
    echo [i] 清理之前的构建...
    if exist "bin" rmdir /s /q bin
    if exist ".buildozer" rmdir /s /q .buildozer
    
    echo [i] 开始构建Android APK...
    buildozer android debug
    
    if exist "bin\mediadownloader-*-debug.apk" (
        echo [√] APK构建成功！
        dir /b bin\mediadownloader-*-debug.apk
    ) else (
        echo [X] APK构建失败
        pause
        exit /b 1
    )
) else if "%choice%"=="4" (
    echo [i] 清理构建文件...
    if exist "bin" (
        rmdir /s /q bin
        echo [√] 删除 bin/
    )
    if exist ".buildozer" (
        rmdir /s /q .buildozer
        echo [√] 删除 .buildozer/
    )
    if exist "__pycache__" (
        rmdir /s /q __pycache__
        echo [√] 删除 __pycache__/
    )
    echo [√] 清理完成
) else (
    echo [X] 无效选择
    pause
    exit /b 1
)

pause
