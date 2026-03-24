"""
文件分享模块

负责：
- 分享文件到其他应用（微信、QQ等）
- 使用Android原生Intent系统
"""

import os
from kivy.logger import Logger
from typing import List, Optional

try:
    from jnius import autoclass, cast

    # Android Intent相关类
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    File = autoclass('java.io.File')
    FileProvider = autoclass('androidx.core.content.FileProvider')
    MimeTypeMap = autoclass('android.webkit.MimeTypeMap')
    
    SHARE_AVAILABLE = True
except ImportError:
    SHARE_AVAILABLE = False
    Logger.warning('ShareManager', 'pyjnius or required Android classes not available')


class ShareManager:
    """文件分享管理器"""

    # 常见MIME类型映射
    MIME_TYPES = {
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'mkv': 'video/x-matroska',
        'webm': 'video/webm',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'aac': 'audio/aac',
        'flac': 'audio/flac',
        'ogg': 'audio/ogg',
        'm4a': 'audio/mp4',
        'txt': 'text/plain',
        'pdf': 'application/pdf',
        'zip': 'application/zip',
    }

    def __init__(self):
        """初始化分享管理器"""
        self.activity = None
        
        if SHARE_AVAILABLE:
            try:
                self.activity = PythonActivity.mActivity
                Logger.info('ShareManager', 'Share manager initialized')
            except Exception as e:
                Logger.error('ShareManager', f'Init error: {e}')

    def share_file(self, file_path: str, title: str = '分享文件'):
        """
        分享单个文件
        
        Args:
            file_path: 文件路径
            title: 分享对话框标题
        """
        if not self.activity:
            Logger.error('ShareManager', 'Share not available')
            return

        if not os.path.exists(file_path):
            Logger.error('ShareManager', f'File not found: {file_path}')
            return

        try:
            Logger.info('ShareManager', f'Sharing file: {file_path}')
            
            # 获取MIME类型
            mime_type = self._get_mime_type(file_path)
            
            # 创建File和Uri
            file_obj = File(file_path)
            
            # Android 7.0+ 需要使用FileProvider
            authority = f"{self.activity.getPackageName()}.fileprovider"
            file_uri = FileProvider.getUriForFile(
                self.activity,
                authority,
                file_obj
            )
            
            # 创建分享Intent
            intent = Intent()
            intent.setAction(Intent.ACTION_SEND)
            intent.putExtra(Intent.EXTRA_STREAM, file_uri)
            intent.setType(mime_type)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            
            # 使用系统分享选择器
            chooser = Intent.createChooser(intent, title)
            self.activity.startActivity(chooser)
            
            Logger.info('ShareManager', 'Share intent started')
        except Exception as e:
            Logger.error('ShareManager', f'Share error: {e}')

    def share_multiple_files(self, file_paths: List[str], title: str = '分享文件'):
        """
        分享多个文件
        
        Args:
            file_paths: 文件路径列表
            title: 分享对话框标题
        """
        if not self.activity:
            Logger.error('ShareManager', 'Share not available')
            return

        try:
            Logger.info('ShareManager', f'Sharing {len(file_paths)} files')
            
            # 创建Uri列表
            uri_list = []
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    Logger.warning('ShareManager', f'File not found: {file_path}')
                    continue
                
                file_obj = File(file_path)
                authority = f"{self.activity.getPackageName()}.fileprovider"
                file_uri = FileProvider.getUriForFile(
                    self.activity,
                    authority,
                    file_obj
                )
                uri_list.append(file_uri)
            
            if not uri_list:
                Logger.error('ShareManager', 'No valid files to share')
                return
            
            # 创建ArrayList
            ArrayList = autoclass('java.util.ArrayList')
            uri_array_list = ArrayList()
            for uri in uri_list:
                uri_array_list.add(uri)
            
            # 创建分享Intent
            intent = Intent()
            intent.setAction(Intent.ACTION_SEND_MULTIPLE)
            intent.putParcelableArrayListExtra(Intent.EXTRA_STREAM, uri_array_list)
            intent.setType('*/*')
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            
            # 使用系统分享选择器
            chooser = Intent.createChooser(intent, title)
            self.activity.startActivity(chooser)
            
            Logger.info('ShareManager', 'Multiple share intent started')
        except Exception as e:
            Logger.error('ShareManager', f'Share error: {e}')

    def share_text(self, text: str, title: str = '分享'):
        """
        分享文本
        
        Args:
            text: 文本内容
            title: 分享对话框标题
        """
        if not self.activity:
            Logger.error('ShareManager', 'Share not available')
            return

        try:
            Logger.info('ShareManager', 'Sharing text')
            
            intent = Intent()
            intent.setAction(Intent.ACTION_SEND)
            intent.putExtra(Intent.EXTRA_TEXT, text)
            intent.setType('text/plain')
            
            chooser = Intent.createChooser(intent, title)
            self.activity.startActivity(chooser)
        except Exception as e:
            Logger.error('ShareManager', f'Share text error: {e}')

    def open_with(self, file_path: str):
        """
        用其他应用打开文件
        
        Args:
            file_path: 文件路径
        """
        if not self.activity:
            Logger.error('ShareManager', 'Not available')
            return

        if not os.path.exists(file_path):
            Logger.error('ShareManager', f'File not found: {file_path}')
            return

        try:
            Logger.info('ShareManager', f'Opening file with other apps: {file_path}')
            
            file_obj = File(file_path)
            mime_type = self._get_mime_type(file_path)
            
            authority = f"{self.activity.getPackageName()}.fileprovider"
            file_uri = FileProvider.getUriForFile(
                self.activity,
                authority,
                file_obj
            )
            
            intent = Intent()
            intent.setAction(Intent.ACTION_VIEW)
            intent.setDataAndType(file_uri, mime_type)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            
            chooser = Intent.createChooser(intent, '打开方式')
            self.activity.startActivity(chooser)
        except Exception as e:
            Logger.error('ShareManager', f'Open with error: {e}')

    def _get_mime_type(self, file_path: str) -> str:
        """
        获取文件MIME类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            MIME类型
        """
        # 先检查扩展名映射
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        if ext in self.MIME_TYPES:
            return self.MIME_TYPES[ext]
        
        # 使用Android系统MIME类型查询
        if SHARE_AVAILABLE:
            try:
                mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext)
                if mime:
                    return mime
            except Exception as e:
                Logger.debug('ShareManager', f'Get MIME error: {e}')
        
        # 默认为二进制
        return 'application/octet-stream'
