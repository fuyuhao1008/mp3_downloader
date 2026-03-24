"""
Android WebView集成模块

负责：
- 使用Android原生WebView加载网页
- 与WebView进行JavaScript交互
- 支持媒体检测和URL拦截
"""

from kivy.logger import Logger
from kivy.uix.widget import Widget
from typing import Optional, Callable
from pathlib import Path
import sys

# 添加android.helpers到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from jnius import autoclass, cast
    from jnius import PythonJavaClass, java_method

    # Android WebView相关类
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    JavaScriptInterface = autoclass('android.webkit.JavaScriptInterface')
    Uri = autoclass('android.net.Uri')
    WebChromeClient = autoclass('android.webkit.WebChromeClient')
    
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    Logger.warning('WebViewManager', 'pyjnius or WebView classes not available')


class PythonWebViewInterface(PythonJavaClass):
    """Python-JavaScript交互接口"""

    __javainterfaces__ = ('android/webkit/JavaScriptInterface',)
    
    def __init__(self, callback: Optional[Callable] = None):
        super().__init__()
        self.callback = callback

    @java_method('(Ljava/lang/String;)V')
    def onJavaScriptCall(self, message: str):
        """接收来自JavaScript的消息"""
        Logger.info('WebViewManager', f'JavaScript call: {message}')
        if self.callback:
            self.callback(message)


class WebViewManager:
    """WebView管理器"""

    def __init__(self, media_detector=None, on_media_detected: Optional[Callable] = None):
        """
        初始化WebView管理器
        
        Args:
            media_detector: MediaDetector实例（用于检测媒体URL）
            on_media_detected: 媒体检测回调 callback(url: str, media_type: str)
        """
        self.webview = None
        self.js_interface = None
        self.media_detector = media_detector
        self.on_media_detected = on_media_detected
        self.webview_client = None
        self.interceptor = None
        
        if not WEBVIEW_AVAILABLE:
            Logger.warning('WebViewManager', 'WebView not available')
            return

        try:
            self._init_webview()
            Logger.info('WebViewManager', 'WebView initialized')
        except Exception as e:
            Logger.error('WebViewManager', f'Init error: {e}')

    def _init_webview(self):
        """初始化WebView"""
        if not WEBVIEW_AVAILABLE:
            return

        try:
            activity = PythonActivity.mActivity
            
            # 创建WebView
            self.webview = WebView(activity)
            
            # 配置WebView设置
            settings = self.webview.getSettings()
            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setDatabaseEnabled(True)
            settings.setMixedContentMode(0)  # MIXED_CONTENT_ALWAYS_ALLOW
            settings.setUserAgentString(
                'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36'
            )
            
            # 如果有媒体检测器，使用自定义WebViewClient进行URL拦截
            if self.media_detector:
                self._setup_media_detection()
            else:
                # 否则使用默认的WebViewClient
                self.webview.setWebViewClient(WebViewClient())
            
            Logger.info('WebViewManager', 'WebView configured')
        except Exception as e:
            Logger.error('WebViewManager', f'Init WebView error: {e}')

    def _setup_media_detection(self):
        """设置媒体检测"""
        try:
            from helpers.webview_interceptor import WebViewInterceptor
            
            self.interceptor = WebViewInterceptor(self.media_detector)
            self.webview_client = self.interceptor.create_webview_client(
                on_media_detected=self.on_media_detected
            )
            
            if self.webview_client:
                self.webview.setWebViewClient(self.webview_client)
                Logger.info('WebViewManager', 'Media detection enabled')
            else:
                self.webview.setWebViewClient(WebViewClient())
                Logger.warning('WebViewManager', 'Failed to setup media detection')
        except Exception as e:
            Logger.warning('WebViewManager', f'Media detection setup failed: {e}')
            self.webview.setWebViewClient(WebViewClient())

    def load_url(self, url: str):
        """
        加载URL
        
        Args:
            url: 网址
        """
        if not self.webview:
            Logger.error('WebViewManager', 'WebView not initialized')
            return

        try:
            Logger.info('WebViewManager', f'Loading URL: {url}')
            self.webview.loadUrl(url)
        except Exception as e:
            Logger.error('WebViewManager', f'Load URL error: {e}')

    def load_html(self, html: str, base_url: str = 'about:blank'):
        """
        加载HTML内容
        
        Args:
            html: HTML代码
            base_url: 基础URL
        """
        if not self.webview:
            Logger.error('WebViewManager', 'WebView not initialized')
            return

        try:
            Logger.info('WebViewManager', f'Loading HTML (length: {len(html)})')
            self.webview.loadData(html, 'text/html; charset=utf-8', 'utf-8')
        except Exception as e:
            Logger.error('WebViewManager', f'Load HTML error: {e}')

    def execute_javascript(self, script: str):
        """
        执行JavaScript代码
        
        Args:
            script: JavaScript代码
        """
        if not self.webview:
            Logger.error('WebViewManager', 'WebView not initialized')
            return

        try:
            Logger.debug('WebViewManager', f'Executing JS: {script[:50]}...')
            if hasattr(self.webview, 'evaluateJavascript'):
                self.webview.evaluateJavascript(script, None)
        except Exception as e:
            Logger.error('WebViewManager', f'Execute JS error: {e}')

    def add_javascript_interface(self, callback: Optional[Callable] = None):
        """
        添加JavaScript接口
        
        Args:
            callback: 接收消息的回调
        """
        if not self.webview:
            Logger.error('WebViewManager', 'WebView not initialized')
            return

        try:
            self.js_interface = PythonWebViewInterface(callback)
            self.webview.addJavascriptInterface(self.js_interface, 'PythonInterface')
            Logger.info('WebViewManager', 'JavaScript interface added')
        except Exception as e:
            Logger.error('WebViewManager', f'Add interface error: {e}')

    def clear_cache(self):
        """清除缓存"""
        if self.webview:
            try:
                self.webview.clearCache(True)
                Logger.info('WebViewManager', 'Cache cleared')
            except Exception as e:
                Logger.error('WebViewManager', f'Clear cache error: {e}')

    def go_back(self) -> bool:
        """返回"""
        if self.webview:
            try:
                if self.webview.canGoBack():
                    self.webview.goBack()
                    return True
            except Exception as e:
                Logger.error('WebViewManager', f'Go back error: {e}')
        return False

    def go_forward(self) -> bool:
        """前进"""
        if self.webview:
            try:
                if self.webview.canGoForward():
                    self.webview.goForward()
                    return True
            except Exception as e:
                Logger.error('WebViewManager', f'Go forward error: {e}')
        return False

    def reload(self):
        """重新加载"""
        if self.webview:
            try:
                self.webview.reload()
                Logger.info('WebViewManager', 'Page reloaded')
            except Exception as e:
                Logger.error('WebViewManager', f'Reload error: {e}')
