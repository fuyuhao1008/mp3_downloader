"""
项目配置和初始化脚本

如果需要运行时初始化某些模块，在此处添加
"""

import os
import sys
from pathlib import Path

# 确保能找到src模块
sys.path.insert(0, str(Path(__file__).parent))

# 初始化日志
try:
    from src.utils.logger import setup_logger
    setup_logger()
except Exception as e:
    print(f"Warning: Failed to setup logger: {e}")

# 验证必要的目录
def init_directories():
    """初始化必要的目录结构"""
    try:
        from src.utils.constants import DOWNLOAD_DIR, CACHE_DIR, APP_DATA_DIR
        for directory in [DOWNLOAD_DIR, CACHE_DIR, APP_DATA_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Warning: Failed to init directories: {e}")
        return False

# 应用启动时执行
if __name__ != '__main__':
    init_directories()
