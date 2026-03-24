#!/bin/bash
# 本地开发运行脚本

set -e

echo "=========================================="
echo "MediaDownloader - 本地开发运行脚本"
echo "=========================================="

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[✓] Python版本: $PYTHON_VERSION"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "[i] 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "[i] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "[i] 检查依赖..."
pip install --upgrade pip setuptools wheel > /dev/null
pip install -q -r requirements.txt 2>/dev/null || {
    echo "[w] 部分依赖安装失败（可能在非Android环境下）"
    echo "[i] 继续运行基础版本..."
}

# 检查主文件
if [ ! -f "main.py" ]; then
    echo "[✗] 错误：找不到 main.py"
    exit 1
fi

echo ""
echo "=========================================="
echo "[✓] 环境准备完成"
echo "=========================================="
echo ""
echo "运行模式选择："
echo "1. 开发模式（本地运行，不构建APK）"
echo "2. 调试模式（输出详细日志）"
echo "3. 构建APK（需要Buildozer）"
echo ""
read -p "请选择 [1-3]: " choice

case $choice in
    1)
        echo "[i] 启动应用（开发模式）..."
        python3 main.py
        ;;
    2)
        echo "[i] 启动应用（调试模式）..."
        export KIVY_LOG_MODE=MIXED
        export KIVY_LOG_LEVEL=debug
        python3 main.py
        ;;
    3)
        if ! command -v buildozer &> /dev/null; then
            echo "[i] 安装Buildozer..."
            pip install buildozer cython
        fi
        
        echo "[i] 清理之前的构建..."
        rm -rf bin/ .buildozer/
        
        echo "[i] 开始构建Android APK..."
        buildozer android debug
        
        if [ -f "bin/mediadownloader-*-debug.apk" ]; then
            echo "[✓] APK构建成功！"
            echo "[i] APK文件位置: $(ls -1 bin/mediadownloader-*-debug.apk | head -1)"
        else
            echo "[✗] APK构建失败"
            exit 1
        fi
        ;;
    *)
        echo "[✗] 无效选择"
        exit 1
        ;;
esac
