"""
MediaDownloader - Android媒体下载和播放应用
使用Kivy框架构建，支持HarmonyOS/Android

新逻辑：
- WebView浏览网页
- 自动检测音视频播放
- 询问用户是否下载为MP3
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger

from ui.screens import HomeScreen, BrowserScreen, LibraryScreen, SettingsScreen, DownloadScreen
from core.downloader import DownloadManager
from core.player import MediaPlayer
from core.media_detector import MediaDetector
from android.permissions import PermissionManager
from android.webview import WebViewManager
from utils.constants import APP_NAME, APP_VERSION, ANDROID_PLATFORM
from utils.logger import setup_logger

# 配置窗口大小（Android会自动忽略）
Window.size = (1080, 1920)

# 设置日志
Logger.setLevel('debug')
setup_logger()


class MediaDownloaderApp(App):
    """主应用类"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = f"{APP_NAME} v{APP_VERSION}"
        self.download_manager = None
        self.player = None
        self.permission_manager = None
        self.media_detector = None
        self.webview_manager = None
        self.current_screen = None

    def build(self):
        """构建应用UI"""
        Logger.info('MediaDownloader', 'Starting application build')
        
        # 初始化权限管理（仅Android）
        if ANDROID_PLATFORM:
            try:
                self.permission_manager = PermissionManager()
                self.permission_manager.request_permissions()
                Logger.info('MediaDownloader', 'Android permissions initialized')
            except Exception as e:
                Logger.error('MediaDownloader', f'Failed to init permissions: {e}')

        # 初始化管理器和检测器
        try:
            self.download_manager = DownloadManager()
            self.player = MediaPlayer()
            self.media_detector = MediaDetector()
            
            # 创建WebViewManager并传入媒体检测器和回调
            self.webview_manager = WebViewManager(
                media_detector=self.media_detector,
                on_media_detected=self._on_media_detected
            )
            
            Logger.info('MediaDownloader', 'All managers initialized successfully')
        except Exception as e:
            Logger.error('MediaDownloader', f'Failed to init managers: {e}')
            self.show_error('初始化失败', str(e))

        # 创建主UI
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题栏
        title_layout = BoxLayout(size_hint_y=0.08, spacing=10)
        title_label = Label(
            text=self.title,
            font_size='20sp',
            bold=True,
            size_hint_x=0.7
        )
        title_layout.add_widget(title_label)
        
        # 菜单按钮
        menu_layout = BoxLayout(size_hint_x=0.3, spacing=5)
        for btn_text in ['设置', '帮助']:
            btn = Button(text=btn_text, size_hint_x=0.5)
            btn.bind(on_press=self.on_menu_button)
            menu_layout.add_widget(btn)
        title_layout.add_widget(menu_layout)
        main_layout.add_widget(title_layout)

        # 标签页容器
        self.screen_box = BoxLayout(orientation='vertical')
        main_layout.add_widget(self.screen_box)

        # 底部标签页按钮
        tab_layout = BoxLayout(size_hint_y=0.1, spacing=5)
        tabs = [
            ('浏览', 'browser'),      # 新的浏览器标签页（主功能）
            ('媒体库', 'library'),
            ('下载', 'download'),     # 备选方案
            ('播放器', 'player'),
        ]
        
        for tab_name, tab_id in tabs:
            btn = Button(text=tab_name)
            btn.bind(on_press=lambda instance, tid=tab_id: self.switch_screen(tid))
            tab_layout.add_widget(btn)
        main_layout.add_widget(tab_layout)

        # 默认显示浏览界面（新的主界面）
        self.switch_screen('browser')

        return main_layout

    def _on_media_detected(self, url: str, media_type: str):
        """
        媒体检测回调（由WebViewInterceptor调用）
        
        Args:
            url: 媒体资源URL
            media_type: 'video' 或 'audio'
        """
        Logger.info('MediaDownloaderApp', f'Media detected: {media_type}')
        
        # 在当前屏幕处理检测到的媒体
        if isinstance(self.current_screen, BrowserScreen):
            self.current_screen.on_media_detected(url, media_type)

    def switch_screen(self, screen_id):
        """切换屏幕"""
        Logger.info('MediaDownloader', f'Switching to screen: {screen_id}')
        self.screen_box.clear_widgets()

        try:
            if screen_id == 'browser':
                # 新的浏览器界面（主要功能）
                self.current_screen = BrowserScreen(
                    webview_manager=self.webview_manager,
                    download_manager=self.download_manager,
                    media_detector=self.media_detector,
                    on_error=self.show_error
                )
            elif screen_id == 'download':
                # 备选的直接下载界面
                self.current_screen = DownloadScreen(
                    download_manager=self.download_manager,
                    on_error=self.show_error
                )
            elif screen_id == 'library':
                self.current_screen = LibraryScreen(
                    player=self.player,
                    on_error=self.show_error
                )
            elif screen_id == 'player':
                self.current_screen = HomeScreen(
                    player=self.player,
                    on_error=self.show_error
                )
            
            if self.current_screen:
                self.screen_box.add_widget(self.current_screen)
        except Exception as e:
            Logger.error('MediaDownloader', f'Failed to switch screen: {e}')
            self.show_error('切换界面失败', str(e))

    def on_menu_button(self, instance):
        """菜单按钮处理"""
        if instance.text == '设置':
            self.show_settings()
        elif instance.text == '帮助':
            self.show_help()

    def show_settings(self):
        """显示设置界面"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 设置选项
        settings_scrollview = ScrollView()
        settings_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        settings_grid.bind(minimum_height=settings_grid.setter('height'))

        # 下载位置设置
        location_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        location_layout.add_widget(Label(text='下载位置:', size_hint_x=0.4))
        location_spinner = Spinner(
            text='内部存储',
            values=('内部存储', '外部存储'),
            size_hint_x=0.6
        )
        location_layout.add_widget(location_spinner)
        settings_grid.add_widget(location_layout)

        # 自动转换MP3设置
        convert_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        convert_layout.add_widget(Label(text='自动转换MP3:', size_hint_x=0.4))
        convert_spinner = Spinner(
            text='否',
            values=('是', '否'),
            size_hint_x=0.6
        )
        convert_layout.add_widget(convert_spinner)
        settings_grid.add_widget(convert_layout)

        settings_scrollview.add_widget(settings_grid)
        content.add_widget(settings_scrollview)

        # 按钮
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=10)
        btn_layout.add_widget(Button(text='保存'))
        btn_layout.add_widget(Button(text='取消'))
        content.add_widget(btn_layout)

        popup = Popup(title='设置', content=content, size_hint=(0.9, 0.8))
        popup.open()

    def show_help(self):
        """显示帮助信息"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        help_text = """
        媒体下载器 - 使用说明

        1. 下载功能：
           - 在"下载"标签页输入媒体URL
           - 支持Bilibili、YouTube等平台
           - 可选择下载格式和质量

        2. 媒体库：
           - 查看和管理已下载的文件
           - 支持分享到微信等应用
           - 删除本地文件

        3. 播放器：
           - 播放已下载的媒体文件
           - 支持音视频播放
           - 显示播放进度

        4. 需要的权限：
           - 存储读写权限
           - 网络访问权限
           - 媒体播放权限
        """
        
        scroll = ScrollView()
        label = Label(text=help_text, markup=True, size_hint_y=None)
        label.bind(texture_size=label.setter('size'))
        scroll.add_widget(label)
        content.add_widget(scroll)

        close_btn = Button(text='关闭', size_hint_y=0.15)
        content.add_widget(close_btn)

        popup = Popup(title='帮助', content=content, size_hint=(0.9, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_error(self, title, message):
        """显示错误对话框"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        content.add_widget(Label(text=message, size_hint_y=0.8))
        
        btn = Button(text='确定', size_hint_y=0.2)
        content.add_widget(btn)

        popup = Popup(title=title, content=content, size_hint=(0.9, 0.6))
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def on_stop(self):
        """应用停止时清理资源"""
        Logger.info('MediaDownloader', 'Stopping application')
        
        if self.player:
            try:
                self.player.stop()
            except Exception as e:
                Logger.error('MediaDownloader', f'Error stopping player: {e}')
        
        if self.download_manager:
            try:
                self.download_manager.cancel_all()
            except Exception as e:
                Logger.error('MediaDownloader', f'Error canceling downloads: {e}')
        
        return True


if __name__ == '__main__':
    app = MediaDownloaderApp()
    app.run()
