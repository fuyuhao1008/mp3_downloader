"""
日志管理模块
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from kivy.logger import Logger as KivyLogger

try:
    from utils.constants import LOG_LEVEL, LOG_DIR, LOG_FILE, MAX_LOG_SIZE, LOG_BACKUP_COUNT
except ImportError:
    LOG_LEVEL = 'INFO'
    LOG_DIR = str(Path.home() / '.mediadownloader' / 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')
    MAX_LOG_SIZE = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5


def setup_logger():
    """设置日志系统"""
    
    # 确保日志目录存在
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    
    # 创建Python日志记录器
    logger = logging.getLogger('MediaDownloader')
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # 创建文件处理器
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        
        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.info(f'Logger initialized - Level: {LOG_LEVEL}, File: {LOG_FILE}')
    except Exception as e:
        KivyLogger.error('Logger', f'Failed to setup file logging: {e}')
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(f'MediaDownloader.{name}')


class LoggerAdapter:
    """日志适配器，兼容Kivy日志系统"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(name)
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
        KivyLogger.debug(self.name, message)
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
        KivyLogger.info(self.name, message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
        KivyLogger.warning(self.name, message)
    
    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)
        KivyLogger.error(self.name, message)
    
    def critical(self, message: str):
        """严重错误日志"""
        self.logger.critical(message)
        KivyLogger.critical(self.name, message)
