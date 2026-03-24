"""
常量定义模块
"""

import os
import sys
from pathlib import Path

# 应用信息
APP_NAME = 'MediaDownloader'
APP_VERSION = '1.0.0'
APP_AUTHOR = 'Your Name'
APP_DESCRIPTION = 'Android Media Downloader and Player'

# 平台检测
ANDROID_PLATFORM = True
try:
    # 尝试导入Android特定模块
    from jnius import autoclass
    ANDROID_PLATFORM = True
except (ImportError, Exception):
    ANDROID_PLATFORM = False

# 存储路径
if ANDROID_PLATFORM:
    from android.permissions import PermissionManager
    DOWNLOAD_DIR = PermissionManager.get_downloads_dir()
    CACHE_DIR = PermissionManager.get_cache_dir()
    APP_DATA_DIR = PermissionManager.get_app_files_dir()
else:
    # 桌面环境
    home_dir = Path.home()
    DOWNLOAD_DIR = str(home_dir / 'Downloads' / APP_NAME)
    CACHE_DIR = str(home_dir / '.cache' / APP_NAME)
    APP_DATA_DIR = str(home_dir / f'.{APP_NAME.lower()}')

# 确保目录存在
for directory in [DOWNLOAD_DIR, CACHE_DIR, APP_DATA_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# 支持的媒体格式
SUPPORTED_VIDEO_FORMATS = [
    'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', '3gp', 'mpg', 'mpeg'
]

SUPPORTED_AUDIO_FORMATS = [
    'mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a', 'wma', 'opus'
]

SUPPORTED_FORMATS = SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS

# 下载设置
MAX_CONCURRENT_DOWNLOADS = 2
DOWNLOAD_TIMEOUT = 300  # 秒
CHUNK_SIZE = 8192  # 字节

# 播放器设置
AUTO_PLAY_NEXT = True
REMEMBER_PLAYBACK_POSITION = True

# 文件转换设置
DEFAULT_MP3_BITRATE = '192'  # kbps
DEFAULT_VIDEO_QUALITY = 'best'

# 网络设置
SOCKET_TIMEOUT = 30  # 秒
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # 秒

# 日志设置
LOG_LEVEL = 'INFO'
LOG_DIR = CACHE_DIR
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# URL规则（支持的网站）
SUPPORTED_URLS = {
    'Bilibili': ['bilibili.com', 'b23.tv'],
    'YouTube': ['youtube.com', 'youtu.be'],
    '抖音': ['douyin.com', 'dyh.land'],
    'TikTok': ['tiktok.com'],
    'Instagram': ['instagram.com'],
    '微博': ['weibo.com'],
    '小红书': ['xiaohongshu.com'],
}

# UI设置
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 1920
FONT_SIZE_LARGE = '20sp'
FONT_SIZE_MEDIUM = '14sp'
FONT_SIZE_SMALL = '10sp'

# 颜色主题（RGB）
THEME_COLORS = {
    'primary': (0.2, 0.6, 1.0, 1.0),      # 蓝色
    'primary_dark': (0.1, 0.4, 0.8, 1.0),
    'accent': (1.0, 0.5, 0.0, 1.0),       # 橙色
    'text_primary': (0.2, 0.2, 0.2, 1.0),
    'text_secondary': (0.6, 0.6, 0.6, 1.0),
    'background': (1.0, 1.0, 1.0, 1.0),
    'surface': (0.95, 0.95, 0.95, 1.0),
}
