"""
媒体检测对话框

显示检测到的媒体资源，询问用户是否下载为MP3
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.logger import Logger


class MediaDetectedDialog(Popup):
    """媒体检测对话框"""

    def __init__(self, url: str, media_type: str, 
                 on_download: callable = None,
                 on_cancel: callable = None, **kwargs):
        """
        初始化对话框
        
        Args:
            url: 媒体资源URL
            media_type: 'video' 或 'audio'
            on_download: 确认下载时的回调 callback(url: str, convert_to_mp3: bool)
            on_cancel: 取消时的回调 callback()
        """
        super().__init__(**kwargs)
        
        self.url = url
        self.media_type = media_type
        self.on_download = on_download or (lambda u, c: None)
        self.on_cancel = on_cancel or (lambda: None)
        
        self.title = '检测到媒体资源'
        self.size_hint = (0.85, 0.55)
        
        # 构建UI
        self._build_ui()
        
        Logger.info('MediaDetectedDialog', f'Dialog created for: {media_type}')

    def _build_ui(self):
        """构建用户界面"""
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # 标题和图标
        header_layout = BoxLayout(size_hint_y=0.25, spacing=10)
        icon = '🎬' if self.media_type == 'video' else '🎵'
        header_layout.add_widget(Label(
            text=icon,
            font_size='32sp',
            size_hint_x=0.2
        ))
        
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.8, spacing=5)
        info_layout.add_widget(Label(
            text=f'检测到{self._get_media_name()}',
            font_size='16sp',
            bold=True,
            size_hint_y=0.5
        ))
        info_layout.add_widget(Label(
            text='是否下载为MP3文件？',
            font_size='12sp',
            size_hint_y=0.5
        ))
        header_layout.add_widget(info_layout)
        main_layout.add_widget(header_layout)
        
        # URL显示（可选，如需要可显示）
        url_preview = self.url[:60] + '...' if len(self.url) > 60 else self.url
        main_layout.add_widget(Label(
            text=f'[size=10sp]{url_preview}[/size]',
            markup=True,
            size_hint_y=0.15,
            font_size='10sp'
        ))
        
        # 转换选项
        option_layout = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=10)
        
        # 如果是视频，提供MP3转换选项
        if self.media_type == 'video':
            option_label = Label(
                text='处理方式：',
                size_hint_y=0.4,
                font_size='12sp'
            )
            option_layout.add_widget(option_label)
            
            self.format_spinner = Spinner(
                text='仅保存为MP3（推荐）',
                values=(
                    '仅保存为MP3（推荐）',
                    '保存原格式',
                    '同时保存MP3和原格式'
                ),
                size_hint_y=0.6
            )
            option_layout.add_widget(self.format_spinner)
        else:
            # 音频直接输出为MP3
            option_layout.add_widget(Label(
                text='音频将被转换为MP3格式保存',
                size_hint_y=1.0,
                font_size='12sp'
            ))
            self.format_spinner = None
        
        main_layout.add_widget(option_layout)
        
        # 按钮
        btn_layout = BoxLayout(size_hint_y=0.20, spacing=10)
        
        download_btn = Button(
            text='确认下载',
            background_color=(0.2, 0.6, 1.0, 1.0),
            size_hint_x=0.6
        )
        download_btn.bind(on_press=self._on_download)
        btn_layout.add_widget(download_btn)
        
        cancel_btn = Button(
            text='取消',
            background_color=(0.8, 0.8, 0.8, 1.0),
            size_hint_x=0.4
        )
        cancel_btn.bind(on_press=self._on_cancel)
        btn_layout.add_widget(cancel_btn)
        
        main_layout.add_widget(btn_layout)
        
        self.content = main_layout

    def _get_media_name(self) -> str:
        """获取媒体类型显示名称"""
        if self.media_type == 'video':
            return '视频'
        elif self.media_type == 'audio':
            return '音频'
        else:
            return '媒体'

    def _on_download(self, instance):
        """下载按钮点击"""
        try:
            # 判断是否转换为MP3
            convert_to_mp3 = True
            
            if self.format_spinner:
                selected = self.format_spinner.text
                if '原格式' in selected and 'MP3' not in selected:
                    convert_to_mp3 = False
            
            Logger.info('MediaDetectedDialog', 
                       f'Download confirmed: convert_to_mp3={convert_to_mp3}')
            
            self.on_download(self.url, convert_to_mp3)
            self.dismiss()
        except Exception as e:
            Logger.error('MediaDetectedDialog', f'Download error: {e}')

    def _on_cancel(self, instance):
        """取消按钮点击"""
        Logger.info('MediaDetectedDialog', 'Download cancelled')
        self.on_cancel()
        self.dismiss()


class DownloadProgressDialog(Popup):
    """下载进度对话框"""

    def __init__(self, task_id: str, url: str, **kwargs):
        """
        初始化下载进度对话框
        
        Args:
            task_id: 下载任务ID
            url: 下载URL
        """
        super().__init__(**kwargs)
        
        self.task_id = task_id
        self.url = url
        
        self.title = '下载中...'
        self.size_hint = (0.9, 0.4)
        self.auto_dismiss = False
        
        # 构建UI
        self._build_ui()

    def _build_ui(self):
        """构建进度UI"""
        from kivy.uix.progressbar import ProgressBar
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # 标题
        main_layout.add_widget(Label(
            text='正在下载并处理媒体文件...',
            size_hint_y=0.2,
            font_size='12sp'
        ))
        
        # 进度条
        self.progress_bar = ProgressBar(size_hint_y=0.3, value=0, max=100)
        main_layout.add_widget(self.progress_bar)
        
        # 进度百分比
        self.progress_label = Label(
            text='0%',
            size_hint_y=0.2,
            font_size='12sp'
        )
        main_layout.add_widget(self.progress_label)
        
        # 取消按钮
        cancel_btn = Button(text='取消下载', size_hint_y=0.2)
        cancel_btn.bind(on_press=self._on_cancel)
        main_layout.add_widget(cancel_btn)
        
        self.content = main_layout

    def update_progress(self, progress: int, status: str = None):
        """
        更新下载进度
        
        Args:
            progress: 进度百分比 (0-100)
            status: 状态文本（可选）
        """
        self.progress_bar.value = min(100, max(0, progress))
        self.progress_label.text = f'{progress}%'

    def _on_cancel(self, instance):
        """取消下载"""
        Logger.info('DownloadProgressDialog', f'Download cancelled: {self.task_id}')
        # 需要在调用方处理取消逻辑

    def on_complete(self, success: bool, file_path: str = None):
        """
        下载完成
        
        Args:
            success: 是否成功
            file_path: 完成后的文件路径
        """
        if success:
            self.title = '下载成功！'
            self.progress_label.text = '✓ 完成'
            self.progress_bar.value = 100
        else:
            self.title = '下载失败'
            self.progress_label.text = '✗ 出错'
        
        # 3秒后自动关闭
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.dismiss(), 3)
