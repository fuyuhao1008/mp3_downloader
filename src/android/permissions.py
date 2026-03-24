"""
Android权限和系统集成模块

负责：
- 请求系统权限
- 获取存储目录
- 调用Android原生功能
"""

from kivy.logger import Logger
from kivy.app import App
import os
from pathlib import Path

try:
    from jnius import autoclass, cast
    from jnius import PythonJavaClass, java_method

    # Android类
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    Build = autoclass('android.os.Build')
    Environment = autoclass('android.os.Environment')
    File = autoclass('java.io.File')
    
    # 权限相关
    Activity = autoclass('android.app.Activity')
    VERSION = autoclass('android.os.Build$VERSION')
    PermissionChecker = autoclass('androidx.core.content.PermissionChecker')
    ActivityCompat = autoclass('androidx.core.app.ActivityCompat')
    ContextCompat = autoclass('androidx.core.content.ContextCompat')
    
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False
    Logger.warning('PermissionManager', 'pyjnius not available, running in non-Android mode')


class PermissionManager:
    """Android权限管理器"""

    # 所需权限列表
    REQUIRED_PERMISSIONS = [
        'android.permission.INTERNET',
        'android.permission.READ_EXTERNAL_STORAGE',
        'android.permission.WRITE_EXTERNAL_STORAGE',
        'android.permission.ACCESS_NETWORK_STATE',
        'android.permission.FOREGROUND_SERVICE',
    ]

    REQUEST_CODE_PERMISSIONS = 100

    def __init__(self):
        """初始化权限管理器"""
        self.app = None
        self.activity = None
        self.granted_permissions = set()
        
        if ANDROID_AVAILABLE:
            try:
                self.app = App.get_running_app()
                self.activity = PythonActivity.mActivity
                Logger.info('PermissionManager', 'Android permission manager initialized')
            except Exception as e:
                Logger.error('PermissionManager', f'Init error: {e}')

    def request_permissions(self):
        """请求所需权限"""
        if not ANDROID_AVAILABLE:
            Logger.info('PermissionManager', 'Not running on Android, skipping permission request')
            return

        try:
            Logger.info('PermissionManager', 'Requesting permissions...')
            
            # Android 6.0+ 需要运行时权限请求
            if VERSION.SDK_INT >= 23:
                # 检查未授予的权限
                permissions_to_request = []
                for perm in self.REQUIRED_PERMISSIONS:
                    if self._check_permission(perm) != PermissionChecker.PERMISSION_GRANTED:
                        permissions_to_request.append(perm)
                
                if permissions_to_request:
                    Logger.info('PermissionManager', f'Requesting {len(permissions_to_request)} permissions')
                    ActivityCompat.requestPermissions(
                        self.activity,
                        permissions_to_request,
                        self.REQUEST_CODE_PERMISSIONS
                    )
                else:
                    Logger.info('PermissionManager', 'All permissions already granted')
                    self.granted_permissions = set(self.REQUIRED_PERMISSIONS)
        except Exception as e:
            Logger.error('PermissionManager', f'Request error: {e}')

    def _check_permission(self, permission: str) -> int:
        """检查权限状态"""
        try:
            return ContextCompat.checkSelfPermission(self.activity, permission)
        except Exception as e:
            Logger.error('PermissionManager', f'Check permission error: {e}')
            return -1

    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        if not ANDROID_AVAILABLE:
            return True  # 非Android环境假设有所有权限
        
        return self._check_permission(permission) == PermissionChecker.PERMISSION_GRANTED

    @staticmethod
    def get_downloads_dir() -> str:
        """
        获取下载目录
        
        Returns:
            下载目录路径
        """
        if not ANDROID_AVAILABLE:
            return str(Path.home() / 'Downloads' / 'MediaDownloader')

        try:
            # 优先使用外部存储的下载目录
            if VERSION.SDK_INT >= 30:  # Android 11+
                # 使用应用专属目录
                files_dir = Environment.getExternalFilesDir(
                    Environment.DIRECTORY_DOWNLOADS
                )
            else:
                # 使用公共下载目录
                files_dir = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS
                )
            
            if files_dir:
                download_dir = os.path.join(files_dir.getAbsolutePath(), 'MediaDownloader')
                Path(download_dir).mkdir(parents=True, exist_ok=True)
                Logger.info('PermissionManager', f'Downloads directory: {download_dir}')
                return download_dir
        except Exception as e:
            Logger.error('PermissionManager', f'Get downloads dir error: {e}')

        # 降级方案：使用缓存目录
        try:
            files_dir = Environment.getDataDirectory()
            download_dir = os.path.join(files_dir.getAbsolutePath(), 'MediaDownloader')
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            return download_dir
        except Exception as e:
            Logger.error('PermissionManager', f'Fallback error: {e}')
            return str(Path.home() / 'Downloads' / 'MediaDownloader')

    @staticmethod
    def get_cache_dir() -> str:
        """获取缓存目录"""
        if not ANDROID_AVAILABLE:
            return str(Path.home() / '.cache' / 'MediaDownloader')

        try:
            context = PythonActivity.mActivity
            cache_dir = context.getCacheDir()
            return cache_dir.getAbsolutePath()
        except Exception as e:
            Logger.error('PermissionManager', f'Get cache dir error: {e}')
            return str(Path.home() / '.cache' / 'MediaDownloader')

    @staticmethod
    def get_app_files_dir() -> str:
        """获取应用私有文件目录"""
        if not ANDROID_AVAILABLE:
            return str(Path.home() / '.mediadownloader')

        try:
            context = PythonActivity.mActivity
            files_dir = context.getFilesDir()
            return files_dir.getAbsolutePath()
        except Exception as e:
            Logger.error('PermissionManager', f'Get files dir error: {e}')
            return str(Path.home() / '.mediadownloader')

    @staticmethod
    def is_storage_available() -> bool:
        """检查外部存储是否可用"""
        if not ANDROID_AVAILABLE:
            return True

        try:
            state = Environment.getExternalStorageState()
            return state == Environment.MEDIA_MOUNTED
        except Exception as e:
            Logger.error('PermissionManager', f'Storage check error: {e}')
            return False
