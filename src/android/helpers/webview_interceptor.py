"""
WebView请求拦截器

负责：
- 拦截WebView中的网络请求
- 检测音视频URL
- 通过回调通知Python层
- 处理去重和线程安全
"""

from typing import Optional, Callable
from kivy.logger import Logger
from kivy.clock import Clock

try:
    from jnius import autoclass, PythonJavaClass, java_method
    from jnius import cast

    # Android类
    WebViewClient = autoclass('android.webkit.WebViewClient')
    WebResourceRequest = autoclass('android.webkit.WebResourceRequest')
    WebResourceResponse = autoclass('android.webkit.WebResourceResponse')
    Uri = autoclass('android.net.Uri')
    
    JNIUS_AVAILABLE = True
except (ImportError, Exception):
    JNIUS_AVAILABLE = False
    Logger.warning('WebViewInterceptor', 'jnius not available')


class MediaDetectionCallback(PythonJavaClass):
    """媒体检测回调接口（Python-Java通信）"""

    __javainterfaces__ = ()
    
    def __init__(self, callback: Optional[Callable] = None):
        super().__init__()
        self.callback = callback

    def on_media_detected(self, url: str, media_type: str):
        """
        媒体检测回调
        
        Args:
            url: 多媒体资源URL
            media_type: 'video' 或 'audio'
        """
        if self.callback:
            try:
                # 在主线程执行回调
                Clock.schedule_once(
                    lambda dt: self.callback(url, media_type),
                    0
                )
            except Exception as e:
                Logger.error('MediaDetectionCallback', f'Callback error: {e}')


class CustomWebViewClient(PythonJavaClass):
    """自定义WebViewClient用于拦截请求"""

    __javainterfaces__ = ('android/webkit/WebViewClient',)

    def __init__(self, media_detector=None, callback: Optional[Callable] = None):
        """
        初始化自定义WebViewClient
        
        Args:
            media_detector: MediaDetector实例
            callback: 检测到媒体时的回调函数 callback(url: str, media_type: str)
        """
        super().__init__()
        self.media_detector = media_detector
        self.callback = callback
        self.shown_urls = set()  # 已弹过对话框的URL
        
        Logger.info('CustomWebViewClient', 'Initialized')

    @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)V')
    def onPageStarted(self, view, url):
        """页面开始加载"""
        Logger.debug('CustomWebViewClient', f'Page started: {url}')

    @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)V')
    def onPageFinished(self, view, url):
        """页面加载完成"""
        Logger.debug('CustomWebViewClient', f'Page finished: {url}')

    @java_method('(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Landroid/webkit/WebResourceResponse;')
    def shouldInterceptRequest(self, view, request):
        """
        拦截网络请求
        
        这是检测媒体资源的主要方法
        在Android 5.0+自动调用
        """
        try:
            # 获取请求URL
            uri = request.getUrl()
            if uri is None:
                return None
            
            url_str = str(uri.toString())
            
            # 检测媒体
            self._check_media_url(url_str)
            
        except Exception as e:
            Logger.error('CustomWebViewClient', f'Intercept error: {e}')
        
        # 返回None表示按正常方式处理请求
        return None

    def _check_media_url(self, url: str):
        """
        检查URL是否为媒体资源
        
        Args:
            url: 完整URL
        """
        if not url or not self.media_detector:
            return

        try:
            # 检测媒体类型
            media_type = self.media_detector.detect_url(url)
            
            if media_type.name == 'UNKNOWN':
                return
            
            # 去重检查
            base_url = url.split('?')[0].split('#')[0]
            if base_url in self.shown_urls:
                return
            
            self.shown_urls.add(base_url)
            
            Logger.info(
                'CustomWebViewClient',
                f'Media detected: {media_type.name} - {url[:80]}'
            )
            
            # 回调通知Python层
            if self.callback:
                try:
                    Clock.schedule_once(
                        lambda dt: self.callback(url, media_type.name.lower()),
                        0
                    )
                except Exception as e:
                    Logger.error('CustomWebViewClient', f'Callback error: {e}')
        
        except Exception as e:
            Logger.error('CustomWebViewClient', f'Check media error: {e}')

    def reset_shown_urls(self):
        """重置已显示的URL列表"""
        self.shown_urls.clear()
        Logger.info('CustomWebViewClient', 'Shown URLs cleared')


class WebViewInterceptor:
    """WebView拦截器管理器"""

    def __init__(self, media_detector=None):
        """
        初始化拦截器
        
        Args:
            media_detector: MediaDetector实例
        """
        self.media_detector = media_detector
        self.client = None
        self.detection_callback = None
        
        if JNIUS_AVAILABLE and media_detector:
            self._init_interceptor()
    
    def _init_interceptor(self):
        """初始化拦截器"""
        try:
            Logger.info('WebViewInterceptor', 'Initializing interceptor')
            # 客户端会在设置到WebView时创建
        except Exception as e:
            Logger.error('WebViewInterceptor', f'Init error: {e}')

    def create_webview_client(self, on_media_detected: Optional[Callable] = None):
        """
        创建自定义WebViewClient
        
        Args:
            on_media_detected: 媒体检测回调 callback(url: str, media_type: str)
            
        Returns:
            CustomWebViewClient实例
        """
        if not JNIUS_AVAILABLE:
            Logger.warning('WebViewInterceptor', 'jnius not available')
            return None
        
        try:
            self.detection_callback = on_media_detected
            self.client = CustomWebViewClient(
                media_detector=self.media_detector,
                callback=on_media_detected
            )
            Logger.info('WebViewInterceptor', 'WebViewClient created')
            return self.client
        except Exception as e:
            Logger.error('WebViewInterceptor', f'Create client error: {e}')
            return None

    def reset(self):
        """重置状态"""
        if self.client:
            self.client.reset_shown_urls()
        Logger.info('WebViewInterceptor', 'Reset')
