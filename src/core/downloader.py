"""
下载管理模块

负责：
- 调用yt-dlp下载媒体
- 管理下载任务队列
- 处理下载进度
- 转换格式（MP3）
"""

import os
import sys
import json
import uuid
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Optional, Dict, List, Any
from kivy.logger import Logger

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    import ffmpeg
except ImportError:
    ffmpeg = None


class DownloadTask:
    """下载任务"""

    def __init__(self, task_id: str, url: str, convert_to_mp3: bool = False):
        self.task_id = task_id
        self.url = url
        self.convert_to_mp3 = convert_to_mp3
        self.status = 'pending'  # pending, downloading, converting, completed, failed
        self.progress = 0
        self.file_path = None
        self.error = None
        self.start_time = time.time()
        self.file_info = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'url': self.url,
            'status': self.status,
            'progress': self.progress,
            'file_path': self.file_path,
            'error': self.error,
            'file_info': self.file_info,
        }


class DownloadManager:
    """下载管理器"""

    def __init__(self, download_dir: Optional[str] = None):
        """
        初始化下载管理器
        
        Args:
            download_dir: 下载目录，如果为None则使用默认目录
        """
        self.tasks: Dict[str, DownloadTask] = {}
        self.task_queue = Queue()
        self.workers = []
        self.running = True
        
        # 设置下载目录
        if download_dir is None:
            # Android环境
            try:
                from android.permissions import PermissionManager
                download_dir = PermissionManager.get_downloads_dir()
            except (ImportError, Exception):
                # 非Android或获取失败，使用相对路径
                download_dir = str(Path.home() / 'Downloads' / 'MediaDownloader')
        
        self.download_dir = download_dir
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        
        Logger.info('DownloadManager', f'Download directory: {self.download_dir}')

        # 启动工作线程池
        self.num_workers = 2
        self._start_workers()

    def _start_workers(self):
        """启动工作线程"""
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_thread,
                daemon=True,
                name=f'DownloadWorker-{i}'
            )
            worker.start()
            self.workers.append(worker)
            Logger.info('DownloadManager', f'Started worker: {worker.name}')

    def _worker_thread(self):
        """工作线程主循环"""
        while self.running:
            try:
                task_id = self.task_queue.get(timeout=1)
                if task_id is None:  # 停止信号
                    break
                
                task = self.tasks.get(task_id)
                if task:
                    self._process_task(task)
            except Exception as e:
                Logger.error('DownloadManager', f'Worker thread error: {e}')

    def download(self, url: str, convert_to_mp3: bool = False) -> str:
        """
        创建下载任务
        
        Args:
            url: 媒体URL（可以是视频/音频资源直接URL或包含媒体的页面URL）
            convert_to_mp3: 是否转换为MP3（仅对视频有效）
            
        Returns:
            任务ID
        """
        if not url:
            raise ValueError('URL cannot be empty')
        
        task_id = str(uuid.uuid4())
        task = DownloadTask(task_id, url, convert_to_mp3)
        
        self.tasks[task_id] = task
        self.task_queue.put(task_id)
        
        Logger.info('DownloadManager', f'Created download task: {task_id} for {url}')
        return task_id

    def download_from_detected_url(self, url: str, media_type: str) -> str:
        """
        从检测到的媒体URL下载
        
        这个方法是专门为WebView媒体检测调用的
        
        Args:
            url: 媒体资源URL
            media_type: 'video' 或 'audio'
            
        Returns:
            任务ID
        """
        # 对于视频/音频，总是转换为MP3
        convert_to_mp3 = True
        
        Logger.info('DownloadManager', 
                   f'Download from detected URL: {media_type} - {url[:80]}')
        
        return self.download(url, convert_to_mp3)

    def _process_task(self, task: DownloadTask):
        """处理下载任务"""
        try:
            task.status = 'downloading'
            Logger.info('DownloadManager', f'Processing task: {task.task_id}')

            # 下载媒体
            file_path = self._download_media(task)
            
            # 如果需要转换为MP3
            if task.convert_to_mp3 and file_path:
                task.status = 'converting'
                file_path = self._convert_to_mp3(file_path)
            
            task.file_path = file_path
            task.status = 'completed'
            task.progress = 100
            
            Logger.info('DownloadManager', f'Task completed: {task.task_id}')
        except Exception as e:
            task.status = 'failed'
            task.error = str(e)
            Logger.error('DownloadManager', f'Task failed: {task.task_id} - {e}')

    def _download_media(self, task: DownloadTask) -> Optional[str]:
        """
        使用yt-dlp下载媒体
        
        Args:
            task: 下载任务
            
        Returns:
            下载文件路径
        """
        if not yt_dlp:
            raise RuntimeError('yt-dlp not installed')

        try:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [lambda d: self._update_progress(task, d)],
                'socket_timeout': 30,
                'postprocessors': [],
            }

            # 对于仅需音频，使用bestaudio格式
            if task.convert_to_mp3:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(task.url, download=True)
                task.file_info = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                }
                
                # 获取输出文件路径
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            Logger.error('DownloadManager', f'Download error for {task.url}: {e}')
            raise

    def _update_progress(self, task: DownloadTask, d: Dict):
        """更新下载进度"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            task.progress = min(100, int((downloaded / total) * 100))
        elif d['status'] == 'finished':
            task.progress = 100

    def _convert_to_mp3(self, file_path: str) -> str:
        """
        转换为MP3格式
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            转换后的文件路径
        """
        if not ffmpeg:
            Logger.warning('DownloadManager', 'ffmpeg not available, skipping conversion')
            return file_path

        try:
            output_path = os.path.splitext(file_path)[0] + '.mp3'
            
            Logger.info('DownloadManager', f'Converting to MP3: {file_path} -> {output_path}')
            
            # 使用ffmpeg-python转换
            stream = ffmpeg.input(file_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                codec='libmp3lame',
                q=4  # 质量 0-9，0最高，4为240kbps
            )
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            # 删除原始文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return output_path
        except Exception as e:
            Logger.error('DownloadManager', f'Convert error: {e}')
            raise

    def get_info(self, url: str) -> Dict[str, Any]:
        """
        获取媒体信息，不下载
        
        Args:
            url: 媒体URL
            
        Returns:
            媒体信息字典
        """
        if not yt_dlp:
            raise RuntimeError('yt-dlp not installed')

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 10,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 获取可用的格式
                formats = []
                if 'formats' in info:
                    for fmt in info['formats'][:5]:  # 只取前5个
                        if fmt.get('format_note'):
                            formats.append(fmt['format_note'])
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'views': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'formats': formats or ['Default'],
                }
        except Exception as e:
            Logger.error('DownloadManager', f'Get info error for {url}: {e}')
            raise

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息或None
        """
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None

    def cancel_task(self, task_id: str):
        """
        取消下载任务
        
        Args:
            task_id: 任务ID
        """
        task = self.tasks.get(task_id)
        if task:
            task.status = 'cancelled'
            Logger.info('DownloadManager', f'Task cancelled: {task_id}')

    def cancel_all(self):
        """取消所有任务"""
        for task in self.tasks.values():
            if task.status not in ('completed', 'failed', 'cancelled'):
                task.status = 'cancelled'
        Logger.info('DownloadManager', 'All tasks cancelled')

    def shutdown(self):
        """关闭下载管理器"""
        Logger.info('DownloadManager', 'Shutting down')
        self.running = False
        
        # 发送停止信号
        for _ in range(self.num_workers):
            self.task_queue.put(None)
        
        # 等待工作线程完成
        for worker in self.workers:
            worker.join(timeout=5)
        
        Logger.info('DownloadManager', 'Shutdown complete')
