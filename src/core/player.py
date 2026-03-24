"""
多媒体播放模块

负责：
- 播放本地媒体文件
- 控制播放进度
- 获取播放信息
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from kivy.logger import Logger

try:
    from ffpyplayer.player import MediaPlayer as FFMediaPlayer
    from ffpyplayer.tools import get_player_version
except ImportError:
    FFMediaPlayer = None
    get_player_version = None


class MediaPlayer:
    """媒体播放器"""

    def __init__(self):
        """初始化播放器"""
        self.current_file = None
        self.player = None
        self.is_playing = False
        self.current_position = 0
        self.duration = 0

        if FFMediaPlayer:
            Logger.info('MediaPlayer', 'ffpyplayer available')
        else:
            Logger.warning('MediaPlayer', 'ffpyplayer not available')

    def play(self, file_path: str) -> bool:
        """
        播放文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            # 停止当前播放
            if self.player:
                self.stop()

            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f'File not found: {file_path}')

            Logger.info('MediaPlayer', f'Playing: {file_path}')

            # 使用ffpyplayer播放
            if FFMediaPlayer:
                self.player = FFMediaPlayer(file_path)
                self.current_file = file_path
                self.is_playing = True
                return True
            else:
                Logger.warning('MediaPlayer', 'ffpyplayer not available, cannot play')
                return False
        except Exception as e:
            Logger.error('MediaPlayer', f'Play error: {e}')
            raise

    def pause(self):
        """暂停播放"""
        if self.player:
            try:
                self.player.toggle_pause()
                self.is_playing = False
                Logger.info('MediaPlayer', 'Paused')
            except Exception as e:
                Logger.error('MediaPlayer', f'Pause error: {e}')

    def resume(self):
        """继续播放"""
        if self.player:
            try:
                self.player.toggle_pause()
                self.is_playing = True
                Logger.info('MediaPlayer', 'Resumed')
            except Exception as e:
                Logger.error('MediaPlayer', f'Resume error: {e}')

    def stop(self):
        """停止播放"""
        if self.player:
            try:
                self.player.close_player()
                self.player = None
                self.is_playing = False
                self.current_file = None
                self.current_position = 0
                self.duration = 0
                Logger.info('MediaPlayer', 'Stopped')
            except Exception as e:
                Logger.error('MediaPlayer', f'Stop error: {e}')

    def seek(self, seconds: float):
        """
        跳转到指定位置
        
        Args:
            seconds: 位置（秒）
        """
        if self.player:
            try:
                # ffpyplayer使用seek方法
                self.player.seek(seconds)
                self.current_position = seconds
                Logger.info('MediaPlayer', f'Seeked to {seconds}s')
            except Exception as e:
                Logger.error('MediaPlayer', f'Seek error: {e}')

    def get_position(self) -> float:
        """
        获取当前播放位置
        
        Returns:
            位置（秒）
        """
        if self.player:
            try:
                # ffpyplayer的get_pts()返回当前位置
                pos = self.player.get_pts()
                if pos is not None:
                    self.current_position = pos
                    return pos
            except Exception as e:
                Logger.error('MediaPlayer', f'Get position error: {e}')
        
        return self.current_position

    def get_duration(self) -> float:
        """
        获取媒体时长
        
        Returns:
            时长（秒）
        """
        if self.player:
            try:
                # 尝试从播放器获取时长
                metadata = self.player.metadata
                if 'duration' in metadata:
                    self.duration = metadata['duration']
                    return self.duration
            except Exception as e:
                Logger.error('MediaPlayer', f'Get duration error: {e}')
        
        return self.duration

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取媒体元数据
        
        Returns:
            元数据字典
        """
        if self.player:
            try:
                return dict(self.player.metadata)
            except Exception as e:
                Logger.error('MediaPlayer', f'Get metadata error: {e}')
        
        return {}

    def set_volume(self, volume: float):
        """
        设置音量
        
        Args:
            volume: 音量（0.0-1.0）
        """
        if self.player:
            try:
                # ffpyplayer的set_volume接受0.0-1.0范围的值
                self.player.set_volume(max(0.0, min(1.0, volume)))
                Logger.info('MediaPlayer', f'Volume set to {volume}')
            except Exception as e:
                Logger.error('MediaPlayer', f'Set volume error: {e}')

    def is_valid(self) -> bool:
        """检查播放器是否有效"""
        if self.player:
            try:
                # 检查播放器是否仍然可用
                _ = self.player.get_pts()
                return True
            except Exception:
                return False
        return False

    def __del__(self):
        """析构时清理资源"""
        self.stop()
