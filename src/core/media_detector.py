"""
媒体URL检测模块

负责：
- 识别视频/音频资源URL
- 支持扩展的规则匹配
- 去重和过滤
"""

import re
from typing import Optional, Tuple, Set
from enum import Enum
from kivy.logger import Logger


class MediaType(Enum):
    """媒体类型枚举"""
    VIDEO = 'video'
    AUDIO = 'audio'
    UNKNOWN = 'unknown'


class MediaDetector:
    """媒体URL检测器"""

    # 视频文件后缀模式
    VIDEO_EXTENSIONS = [
        r'\.mp4(\?|#|$)',
        r'\.m3u8(\?|#|$)',
        r'\.flv(\?|#|$)',
        r'\.webm(\?|#|$)',
        r'\.mkv(\?|#|$)',
        r'\.avi(\?|#|$)',
        r'\.mov(\?|#|$)',
        r'\.m4v(\?|#|$)',
    ]

    # 视频域名模式
    VIDEO_DOMAINS = [
        r'mpvideo\.qpic\.cn',           # 微信视频
        r'v\.qq\.com',                  # 腾讯视频
        r'v\.douyin\.com',              # 抖音
        r'bilibili\.com',               # B站
        r'youtube\.com',
        r'youtu\.be',
        r'vimeo\.com',
        r'dailymotion\.com',
        r'twitch\.tv',
        r'netflix\.com',
        r'hls\.livestream',             # HLS流媒体
    ]

    # 视频路径模式
    VIDEO_PATHS = [
        r'/video/',
        r'/v/',
        r'/play/',
        r'/media/video',
        r'/stream/video',
    ]

    # 音频文件后缀模式
    AUDIO_EXTENSIONS = [
        r'\.mp3(\?|#|$)',
        r'\.m4a(\?|#|$)',
        r'\.aac(\?|#|$)',
        r'\.wav(\?|#|$)',
        r'\.flac(\?|#|$)',
        r'\.ogg(\?|#|$)',
        r'\.opus(\?|#|$)',
        r'\.wma(\?|#|$)',
    ]

    # 音频域名模式
    AUDIO_DOMAINS = [
        r'res\.wx\.qq\.com',            # 微信音频
        r'music\.qq\.com',              # QQ音乐
        r'netease\.com',                # 网易云音乐
        r'kugou\.com',                  # 酷狗音乐
        r'kuwo\.cn',                    # 酷我音乐
        r'xiami\.com',                  # 虾米音乐
        r'spotify\.com',
        r'soundcloud\.com',
    ]

    # 音频路径模式
    AUDIO_PATHS = [
        r'/audio/',
        r'/sound/',
        r'/music/',
        r'/media/audio',
        r'/stream/audio',
        r'/voice/',
        r'/getvoice',
    ]

    def __init__(self):
        """初始化检测器"""
        # 编译正则表达式以提高性能
        self.video_ext_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.VIDEO_EXTENSIONS]
        self.video_domain_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.VIDEO_DOMAINS]
        self.video_path_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.VIDEO_PATHS]

        self.audio_ext_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.AUDIO_EXTENSIONS]
        self.audio_domain_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.AUDIO_DOMAINS]
        self.audio_path_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.AUDIO_PATHS]

        # 已弹过窗的URL集合（去重）
        self.shown_urls: Set[str] = set()
        
        Logger.info('MediaDetector', 'Media detector initialized')

    def detect_url(self, url: str) -> MediaType:
        """
        检测URL类型
        
        Args:
            url: 完整URL
            
        Returns:
            MediaType.VIDEO / MediaType.AUDIO / MediaType.UNKNOWN
        """
        if not url:
            return MediaType.UNKNOWN

        try:
            # 转换为小写便于匹配
            url_lower = url.lower()

            # 检测视频
            if self._match_patterns(url_lower, self.video_ext_patterns) or \
               self._match_patterns(url_lower, self.video_domain_patterns) or \
               self._match_patterns(url_lower, self.video_path_patterns):
                return MediaType.VIDEO

            # 检测音频
            if self._match_patterns(url_lower, self.audio_ext_patterns) or \
               self._match_patterns(url_lower, self.audio_domain_patterns) or \
               self._match_patterns(url_lower, self.audio_path_patterns):
                return MediaType.AUDIO

            return MediaType.UNKNOWN
        except Exception as e:
            Logger.error('MediaDetector', f'Detect error: {e}')
            return MediaType.UNKNOWN

    def is_video_url(self, url: str) -> bool:
        """
        判断是否为视频URL
        
        Args:
            url: 网址
            
        Returns:
            True/False
        """
        return self.detect_url(url) == MediaType.VIDEO

    def is_audio_url(self, url: str) -> bool:
        """
        判断是否为音频URL
        
        Args:
            url: 网址
            
        Returns:
            True/False
        """
        return self.detect_url(url) == MediaType.AUDIO

    def is_media_url(self, url: str) -> bool:
        """
        判断是否为音视频URL
        
        Args:
            url: 网址
            
        Returns:
            True/False
        """
        media_type = self.detect_url(url)
        return media_type in (MediaType.VIDEO, MediaType.AUDIO)

    def should_show_dialog(self, url: str) -> bool:
        """
        检查是否应该弹窗（去重）
        
        Args:
            url: 网址
            
        Returns:
            True表示应该弹窗，False表示已显示过
        """
        # 去除URL中的查询参数进行去重
        base_url = url.split('?')[0].split('#')[0]
        
        if base_url in self.shown_urls:
            return False
        
        self.shown_urls.add(base_url)
        return True

    def reset_shown_urls(self):
        """重置已显示的URL列表"""
        self.shown_urls.clear()
        Logger.info('MediaDetector', 'Shown URLs cleared')

    def add_custom_pattern(self, pattern: str, media_type: MediaType):
        """
        添加自定义规则（用于扩展）
        
        Args:
            pattern: 正则表达式
            media_type: 媒体类型
        """
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            
            if media_type == MediaType.VIDEO:
                self.video_ext_patterns.append(compiled_pattern)
            elif media_type == MediaType.AUDIO:
                self.audio_ext_patterns.append(compiled_pattern)
            
            Logger.info('MediaDetector', f'Custom pattern added: {pattern}')
        except Exception as e:
            Logger.error('MediaDetector', f'Add pattern error: {e}')

    @staticmethod
    def _match_patterns(text: str, patterns: list) -> bool:
        """
        匹配任意模式
        
        Args:
            text: 文本
            patterns: 正则表达式列表
            
        Returns:
            True如果匹配任意模式
        """
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False

    def get_media_info(self, url: str) -> dict:
        """
        获取媒体信息（用于显示）
        
        Args:
            url: 网址
            
        Returns:
            包含媒体类型和提示的字典
        """
        media_type = self.detect_url(url)
        
        if media_type == MediaType.VIDEO:
            return {
                'type': 'video',
                'display_name': '视频',
                'icon': '🎬',
                'description': '检测到视频资源',
            }
        elif media_type == MediaType.AUDIO:
            return {
                'type': 'audio',
                'display_name': '音频',
                'icon': '🎵',
                'description': '检测到音频资源',
            }
        else:
            return {
                'type': 'unknown',
                'display_name': '未知',
                'icon': '📦',
                'description': '检测到媒体资源',
            }
