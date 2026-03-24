"""
UI屏幕组件

包含：
- HomeScreen: 主播放器界面
- BrowserScreen: WebView网页浏览界面（支持媒体检测）
- DownloadScreen: 下载界面（备选方案）
- LibraryScreen: 媒体库界面
- SettingsScreen: 设置界面
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListView
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import os


class HomeScreen(BoxLayout):
    """主播放器屏幕"""

    def __init__(self, player=None, on_error=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.player = player
        self.on_error = on_error or (lambda t, m: None)
        self.current_file = None

        # 封面/标题显示
        cover_layout = BoxLayout(size_hint_y=0.4, padding=10)
        
        # 对于测试环境，显示占位符
        self.cover_image = Image(source='atlas://data/images/defaulttheme/checkbox_off')
        cover_layout.add_widget(self.cover_image)
        self.add_widget(cover_layout)

        # 文件信息
        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=5)
        self.title_label = Label(text='未选择文件', font_size='18sp', bold=True)
        self.duration_label = Label(text='时长: 00:00', font_size='12sp')
        info_layout.add_widget(self.title_label)
        info_layout.add_widget(self.duration_label)
        self.add_widget(info_layout)

        # 进度条
        progress_layout = BoxLayout(orientation='vertical', size_hint_y=0.1, spacing=5)
        self.progress_bar = ProgressBar(value=0, max=100)
        self.time_label = Label(text='00:00 / 00:00', size_hint_y=0.3, font_size='10sp')
        progress_layout.add_widget(self.progress_bar)
        progress_layout.add_widget(self.time_label)
        self.add_widget(progress_layout)

        # 播放控制按钮
        control_layout = BoxLayout(size_hint_y=0.15, spacing=10, padding=5)
        
        buttons_config = [
            ('⏮', self.on_previous, 0.15),
            ('⏪', self.on_rewind, 0.15),
            ('⏯', self.on_play_pause, 0.3),
            ('⏩', self.on_forward, 0.15),
            ('⏹', self.on_stop, 0.15),
        ]
        
        for text, callback, width in buttons_config:
            btn = Button(text=text, size_hint_x=width, font_size='20sp')
            btn.bind(on_press=callback)
            control_layout.add_widget(btn)
        
        self.add_widget(control_layout)

        # 播放列表
        playlist_layout = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        playlist_label = Label(text='播放列表', size_hint_y=0.1, font_size='14sp', bold=True)
        playlist_layout.add_widget(playlist_label)
        
        self.playlist_view = ListView(adapter=ListAdapter(
            data=[],
            cls=ListItemButton
        ))
        playlist_layout.add_widget(self.playlist_view)
        self.add_widget(playlist_layout)

        Logger.info('HomeScreen', 'HomeScreen initialized')

    def on_play_pause(self, instance):
        """暂停/播放"""
        if self.player:
            try:
                if self.player.is_playing:
                    self.player.pause()
                    instance.text = '▶'
                else:
                    self.player.resume()
                    instance.text = '⏸'
            except Exception as e:
                Logger.error('HomeScreen', f'Play/pause error: {e}')
                self.on_error('播放错误', str(e))

    def on_stop(self, instance):
        """停止播放"""
        if self.player:
            try:
                self.player.stop()
            except Exception as e:
                Logger.error('HomeScreen', f'Stop error: {e}')
                self.on_error('停止错误', str(e))

    def on_previous(self, instance):
        """上一曲"""
        Logger.info('HomeScreen', 'Previous track')

    def on_next(self, instance):
        """下一曲"""
        Logger.info('HomeScreen', 'Next track')

    def on_rewind(self, instance):
        """快退"""
        if self.player:
            try:
                current_pos = self.player.get_position()
                self.player.seek(max(0, current_pos - 10))
            except Exception as e:
                Logger.error('HomeScreen', f'Rewind error: {e}')

    def on_forward(self, instance):
        """快进"""
        if self.player:
            try:
                current_pos = self.player.get_position()
                duration = self.player.get_duration()
                self.player.seek(min(duration, current_pos + 10))
            except Exception as e:
                Logger.error('HomeScreen', f'Forward error: {e}')

    def update_progress(self):
        """更新播放进度"""
        if self.player and self.player.is_playing:
            try:
                current = self.player.get_position()
                duration = self.player.get_duration()
                
                if duration > 0:
                    self.progress_bar.value = (current / duration) * 100
                    self.time_label.text = f'{self._format_time(current)} / {self._format_time(duration)}'
            except Exception as e:
                Logger.error('HomeScreen', f'Update progress error: {e}')

    @staticmethod
    def _format_time(seconds):
        """格式化时间"""
        if seconds < 0:
            return '00:00'
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f'{h:02d}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'


class DownloadScreen(BoxLayout):
    """下载屏幕"""

    def __init__(self, download_manager=None, on_error=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.download_manager = download_manager
        self.on_error = on_error or (lambda t, m: None)
        self.download_tasks = {}

        # URL输入区域
        input_layout = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=5)
        input_layout.add_widget(Label(text='输入媒体URL:', size_hint_y=0.3))
        
        self.url_input = TextInput(
            hint_text='粘贴视频链接（支持B站、YouTube、抖音等）',
            multiline=False,
            size_hint_y=0.7
        )
        input_layout.add_widget(self.url_input)
        self.add_widget(input_layout)

        # 下载选项
        options_layout = BoxLayout(size_hint_y=0.15, spacing=10)
        
        # 格式选择
        format_layout = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=3)
        format_layout.add_widget(Label(text='格式:', size_hint_y=0.3, font_size='11sp'))
        self.format_spinner = Button(text='视频', size_hint_y=0.7)
        format_layout.add_widget(self.format_spinner)
        options_layout.add_widget(format_layout)

        # 质量选择
        quality_layout = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=3)
        quality_layout.add_widget(Label(text='质量:', size_hint_y=0.3, font_size='11sp'))
        self.quality_spinner = Button(text='最高', size_hint_y=0.7)
        quality_layout.add_widget(self.quality_spinner)
        options_layout.add_widget(quality_layout)

        self.add_widget(options_layout)

        # 下载按钮
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        
        download_btn = Button(text='开始下载')
        download_btn.bind(on_press=self.on_download)
        btn_layout.add_widget(download_btn)

        info_btn = Button(text='获取信息')
        info_btn.bind(on_press=self.on_get_info)
        btn_layout.add_widget(info_btn)

        self.add_widget(btn_layout)

        # 下载任务列表
        task_label = Label(text='下载任务:', size_hint_y=0.08, font_size='14sp', bold=True)
        self.add_widget(task_label)

        # 任务列表
        scroll = ScrollView()
        self.task_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.task_grid.bind(minimum_height=self.task_grid.setter('height'))
        scroll.add_widget(self.task_grid)
        self.add_widget(scroll)

        Clock.schedule_interval(self.update_downloads, 0.5)
        Logger.info('DownloadScreen', 'DownloadScreen initialized')

    def on_download(self, instance):
        """开始下载"""
        url = self.url_input.text.strip()
        
        if not url:
            self.on_error('输入错误', '请输入有效的URL')
            return

        Logger.info('DownloadScreen', f'Starting download: {url}')

        try:
            if self.download_manager:
                # 转换为MP3标志
                convert_mp3 = self.format_spinner.text == '音频(MP3)'
                
                task_id = self.download_manager.download(
                    url=url,
                    convert_to_mp3=convert_mp3
                )
                
                self.download_tasks[task_id] = {
                    'url': url,
                    'status': '下载中',
                    'progress': 0
                }
                
                Logger.info('DownloadScreen', f'Download task created: {task_id}')
        except Exception as e:
            Logger.error('DownloadScreen', f'Download error: {e}')
            self.on_error('下载失败', str(e))

    def on_get_info(self, instance):
        """获取媒体信息"""
        url = self.url_input.text.strip()
        
        if not url:
            self.on_error('输入错误', '请输入有效的URL')
            return

        Logger.info('DownloadScreen', f'Getting info for: {url}')

        try:
            if self.download_manager:
                info = self.download_manager.get_info(url)
                
                content = BoxLayout(orientation='vertical', padding=10, spacing=10)
                scroll = ScrollView()
                
                info_text = f"标题: {info.get('title', 'N/A')}\n"
                info_text += f"上传者: {info.get('uploader', 'N/A')}\n"
                info_text += f"时长: {info.get('duration', 'N/A')}秒\n"
                info_text += f"格式: {', '.join(info.get('formats', []))}\n"
                
                label = Label(text=info_text, size_hint_y=None, markup=True)
                label.bind(texture_size=label.setter('size'))
                scroll.add_widget(label)
                content.add_widget(scroll)
                
                close_btn = Button(text='关闭', size_hint_y=0.15)
                content.add_widget(close_btn)
                
                popup = Popup(title='媒体信息', content=content, size_hint=(0.9, 0.7))
                close_btn.bind(on_press=popup.dismiss)
                popup.open()
        except Exception as e:
            Logger.error('DownloadScreen', f'Get info error: {e}')
            self.on_error('获取信息失败', str(e))

    def update_downloads(self, dt):
        """更新下载进度"""
        if not self.download_manager:
            return

        try:
            # 更新现有任务
            tasks_to_remove = []
            for task_id in list(self.download_tasks.keys()):
                info = self.download_manager.get_task_info(task_id)
                
                if info is None:
                    tasks_to_remove.append(task_id)
                else:
                    self.download_tasks[task_id]['status'] = info.get('status', '未知')
                    self.download_tasks[task_id]['progress'] = info.get('progress', 0)
            
            # 移除已完成任务
            for task_id in tasks_to_remove:
                del self.download_tasks[task_id]
            
            # 重新绘制列表
            self.task_grid.clear_widgets()
            for task_id, task_data in self.download_tasks.items():
                task_widget = self._create_task_widget(task_id, task_data)
                self.task_grid.add_widget(task_widget)
        except Exception as e:
            Logger.error('DownloadScreen', f'Update downloads error: {e}')

    def _create_task_widget(self, task_id, task_data):
        """创建下载任务小部件"""
        task_box = BoxLayout(orientation='vertical', size_hint_y=None, height=80, spacing=3)
        
        # 标题和URL
        title_layout = BoxLayout(size_hint_y=0.4, spacing=5)
        title_layout.add_widget(Label(
            text=task_data['url'][:40] + '...',
            size_hint_x=0.7,
            font_size='11sp'
        ))
        title_layout.add_widget(Label(
            text=task_data['status'],
            size_hint_x=0.3,
            font_size='10sp',
            bold=True
        ))
        task_box.add_widget(title_layout)

        # 进度条
        progress_layout = BoxLayout(size_hint_y=0.4, spacing=5)
        progress_bar = ProgressBar(
            value=task_data['progress'],
            max=100,
            size_hint_x=0.7
        )
        progress_layout.add_widget(progress_bar)
        progress_layout.add_widget(Label(
            text=f"{task_data['progress']:.0f}%",
            size_hint_x=0.3,
            font_size='10sp'
        ))
        task_box.add_widget(progress_layout)

        # 取消按钮
        cancel_btn = Button(text='取消', size_hint_y=0.2)
        cancel_btn.bind(on_press=lambda x: self.on_cancel_task(task_id))
        task_box.add_widget(cancel_btn)

        return task_box

    def on_cancel_task(self, task_id):
        """取消下载任务"""
        if self.download_manager:
            try:
                self.download_manager.cancel_task(task_id)
                if task_id in self.download_tasks:
                    del self.download_tasks[task_id]
                Logger.info('DownloadScreen', f'Task canceled: {task_id}')
            except Exception as e:
                Logger.error('DownloadScreen', f'Cancel task error: {e}')


class LibraryScreen(BoxLayout):
    """媒体库屏幕"""

    def __init__(self, player=None, on_error=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.player = player
        self.on_error = on_error or (lambda t, m: None)
        self.media_files = []

        # 搜索栏
        search_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        search_input = TextInput(hint_text='搜索媒体文件...', multiline=False)
        search_btn = Button(text='搜索', size_hint_x=0.2)
        search_layout.add_widget(search_input)
        search_layout.add_widget(search_btn)
        self.add_widget(search_layout)

        # 过滤按钮
        filter_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        for filter_text in ['全部', '视频', '音频', '最近']:
            btn = Button(text=filter_text, size_hint_x=0.25)
            btn.bind(on_press=self.on_filter)
            filter_layout.add_widget(btn)
        self.add_widget(filter_layout)

        # 媒体文件列表
        scroll = ScrollView()
        self.file_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.file_grid.bind(minimum_height=self.file_grid.setter('height'))
        scroll.add_widget(self.file_grid)
        self.add_widget(scroll)

        self.refresh_library()
        Logger.info('LibraryScreen', 'LibraryScreen initialized')

    def refresh_library(self):
        """刷新媒体库"""
        try:
            # 扫描媒体目录（实现见后）
            self.media_files = self._scan_media_files()
            self.update_display()
        except Exception as e:
            Logger.error('LibraryScreen', f'Refresh error: {e}')
            self.on_error('刷新失败', str(e))

    def _scan_media_files(self):
        """扫描媒体文件"""
        # TODO: 实现实际的文件扫描逻辑
        return [
            {'name': '示例视频.mp4', 'type': 'video', 'size': '100MB'},
            {'name': '示例音乐.mp3', 'type': 'audio', 'size': '5MB'},
        ]

    def update_display(self):
        """更新显示"""
        self.file_grid.clear_widgets()
        
        for media in self.media_files:
            file_widget = self._create_file_widget(media)
            self.file_grid.add_widget(file_widget)

    def _create_file_widget(self, media):
        """创建文件小部件"""
        media_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=5)
        
        # 文件信息
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6, spacing=3)
        info_layout.add_widget(Label(text=media['name'], font_size='12sp', bold=True))
        info_layout.add_widget(Label(text=f"{media['type'].upper()} | {media['size']}", font_size='10sp'))
        media_box.add_widget(info_layout)

        # 操作按钮
        action_layout = BoxLayout(size_hint_x=0.4, spacing=5)
        
        play_btn = Button(text='播放')
        play_btn.bind(on_press=lambda x: self.on_play_file(media))
        action_layout.add_widget(play_btn)

        share_btn = Button(text='分享')
        action_layout.add_widget(share_btn)

        delete_btn = Button(text='删除')
        action_layout.add_widget(delete_btn)

        media_box.add_widget(action_layout)
        return media_box

    def on_play_file(self, media):
        """播放文件"""
        Logger.info('LibraryScreen', f'Playing: {media["name"]}')
        if self.player:
            try:
                self.player.play(media['name'])
            except Exception as e:
                Logger.error('LibraryScreen', f'Play error: {e}')
                self.on_error('播放失败', str(e))

    def on_filter(self, instance):
        """过滤文件"""
        Logger.info('LibraryScreen', f'Filter: {instance.text}')


class BrowserScreen(BoxLayout):
    """WebView网页浏览屏幕（支持媒体检测和下载）"""

    def __init__(self, webview_manager=None, download_manager=None, 
                 media_detector=None, on_error=None, **kwargs):
        """
        初始化浏览屏幕
        
        Args:
            webview_manager: WebViewManager实例
            download_manager: DownloadManager实例
            media_detector: MediaDetector实例
            on_error: 错误回调
        """
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 5
        self.spacing = 5

        self.webview_manager = webview_manager
        self.download_manager = download_manager
        self.media_detector = media_detector
        self.on_error = on_error or (lambda t, m: None)
        
        # URL输入栏
        url_layout = BoxLayout(size_hint_y=0.08, spacing=5, padding=5)
        
        self.url_input = TextInput(
            hint_text='输入网址或搜索（如: bilibili.com）',
            multiline=False,
            size_hint_x=0.7
        )
        url_layout.add_widget(self.url_input)
        
        go_btn = Button(text='前往', size_hint_x=0.15)
        go_btn.bind(on_press=self._on_go_pressed)
        url_layout.add_widget(go_btn)
        
        # 返回和刷新按钮
        nav_btn = Button(text='↶', size_hint_x=0.15)
        nav_btn.bind(on_press=self._on_refresh_pressed)
        url_layout.add_widget(nav_btn)
        
        self.add_widget(url_layout)
        
        # WebView容器（模拟WebView）
        webview_layout = BoxLayout(size_hint_y=0.92)
        
        if self.webview_manager and self.webview_manager.webview:
            try:
                # 添加真实的WebView（Android）
                webview_layout.add_widget(self.webview_manager.webview)
                Logger.info('BrowserScreen', 'Real WebView added')
            except Exception as e:
                Logger.warning('BrowserScreen', f'Cannot add real WebView: {e}')
                # 降级到模拟界面
                webview_layout.add_widget(self._create_fallback_webview())
        else:
            # 非Android环境，显示模拟界面
            webview_layout.add_widget(self._create_fallback_webview())
        
        self.add_widget(webview_layout)
        
        Logger.info('BrowserScreen', 'BrowserScreen initialized')

    def _create_fallback_webview(self):
        """创建WebView的降级方案（用于非Android环境）"""
        fallback_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        fallback_layout.add_widget(Label(
            text='[b]浏览器（模拟）[/b]\n\n',
            markup=True,
            font_size='14sp'
        ))
        fallback_layout.add_widget(Label(
            text='当媒体资源被检测到时，会在这里显示下载提示。\n\n'
                 '在Android真机上运行时，将显示完整的网页浏览器。',
            font_size='11sp',
            markup=True
        ))
        return fallback_layout

    def _on_go_pressed(self, instance):
        """前往按钮点击"""
        url = self.url_input.text.strip()
        
        if not url:
            self.on_error('输入错误', '请输入URL或搜索词')
            return
        
        # 补全URL
        if not url.startswith(('http://', 'https://')):
            # 如果看起来像域名，添加https://
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                # 否则作为搜索词
                url = 'https://www.baidu.com/s?wd=' + url
        
        Logger.info('BrowserScreen', f'Loading URL: {url}')
        
        if self.webview_manager:
            try:
                self.webview_manager.load_url(url)
            except Exception as e:
                Logger.error('BrowserScreen', f'Load error: {e}')
                self.on_error('加载失败', str(e))

    def _on_refresh_pressed(self, instance):
        """刷新按钮点击"""
        if self.webview_manager:
            try:
                self.webview_manager.reload()
                Logger.info('BrowserScreen', 'Page refreshed')
            except Exception as e:
                Logger.error('BrowserScreen', f'Refresh error: {e}')

    def on_media_detected(self, url: str, media_type: str):
        """
        媒体检测回调（由WebViewInterceptor调用）
        
        Args:
            url: 媒体资源URL
            media_type: 'video' 或 'audio'
        """
        Logger.info('BrowserScreen', f'Media detected: {media_type} - {url[:80]}')
        
        try:
            from dialogs.media_detected_dialog import MediaDetectedDialog
            
            # 创建检测到媒体的对话框
            dialog = MediaDetectedDialog(
                url=url,
                media_type=media_type,
                on_download=self._on_media_download,
                on_cancel=lambda: Logger.info('BrowserScreen', 'Download cancelled')
            )
            dialog.open()
        except Exception as e:
            Logger.error('BrowserScreen', f'Dialog error: {e}')
            self.on_error('错误', f'无法显示对话框: {e}')

    def _on_media_download(self, url: str, convert_to_mp3: bool):
        """
        媒体下载确认回调
        
        Args:
            url: 媒体URL
            convert_to_mp3: 是否转换为MP3
        """
        Logger.info('BrowserScreen', 
                   f'Download media: {url[:80]}, convert_to_mp3={convert_to_mp3}')
        
        if not self.download_manager:
            self.on_error('下载失败', '下载管理器未初始化')
            return
        
        try:
            # 检测媒体类型
            media_type = 'audio' if self.media_detector.is_audio_url(url) else 'video'
            
            # 创建下载任务
            task_id = self.download_manager.download(url, convert_to_mp3)
            
            Logger.info('BrowserScreen', f'Download started: {task_id}')
            
            # 创建进度对话框
            from dialogs.media_detected_dialog import DownloadProgressDialog
            progress_dialog = DownloadProgressDialog(task_id, url)
            progress_dialog.open()
            
            # 定期更新进度
            def update_progress(dt):
                task_info = self.download_manager.get_task_info(task_id)
                if task_info:
                    progress = task_info.get('progress', 0)
                    status = task_info.get('status', 'unknown')
                    progress_dialog.update_progress(progress, status)
                    
                    if status in ('completed', 'failed', 'cancelled'):
                        on_complete = getattr(progress_dialog, 'on_complete', None)
                        if on_complete:
                            on_complete(status == 'completed', task_info.get('file_path'))
                        return False
                return True
            
            Clock.schedule_interval(update_progress, 0.5)
        except Exception as e:
            Logger.error('BrowserScreen', f'Download error: {e}')
            self.on_error('下载失败', str(e))


class SettingsScreen(BoxLayout):
    """设置屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # 添加设置项
        # TODO: 实现详细的设置选项
        self.add_widget(Label(text='设置功能开发中...'))
