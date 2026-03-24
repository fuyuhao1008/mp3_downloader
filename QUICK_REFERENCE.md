# 快速参考指南

## 架构概览

```
WebView用户交互
    ↓
CustomWebViewClient 拦截请求
    ↓
MediaDetector 检测URL类型
    ↓
MediaDetectedDialog 确认下载
    ↓
DownloadManager 下载文件
    ↓
DownloadProgressDialog 显示进度
    ↓
本地存储媒体库
```

## 关键类和方法

### 1. MediaDetector (src/core/media_detector.py)

```python
from core.media_detector import MediaDetector, MediaType

detector = MediaDetector()

# 检测URL类型
media_type = detector.detect_url(url)  # → MediaType.VIDEO/AUDIO/UNKNOWN

# 判断是否为视频
if detector.is_video_url(url):
    print("这是视频")

# 判断是否为音频
if detector.is_audio_url(url):
    print("这是音频")

# 防止重复提示
if detector.should_show_dialog(url):
    show_dialog()

# 获取媒体信息
info = detector.get_media_info(url)
# → {'extension': 'mp4', 'domain': 'video.com', 'path': '/v/'}

# 添加自定义规则
detector.add_custom_pattern(r'custom\.domain\.com', MediaType.VIDEO)
```

### 2. BrowserScreen (src/ui/screens.py)

```python
from ui.screens import BrowserScreen

# 创建浏览器屏幕
browser = BrowserScreen(
    webview_manager=webview_manager,
    download_manager=download_manager,
    media_detector=media_detector,
    on_error=error_callback
)

# 处理媒体检测（自动被WebView拦截器调用）
browser.on_media_detected(url='https://...', media_type='video')

# 处理用户确认下载
browser._on_media_download(url='https://...', convert_to_mp3=True)
```

### 3. MediaDetectedDialog (src/ui/dialogs/media_detected_dialog.py)

```python
from ui.dialogs.media_detected_dialog import MediaDetectedDialog, DownloadProgressDialog

# 显示媒体检测对话框
dialog = MediaDetectedDialog(
    url='https://example.com/video.mp4',
    media_type='video',
    on_download=lambda url, convert: print(f"Download {url}")
)
dialog.open()

# 显示下载进度对话框
progress = DownloadProgressDialog(
    task_id='task_123',
    download_manager=download_manager
)
progress.open()

# 更新进度（自动更新）
progress.update_progress(42)  # 42%

# 检查下载状态（自动检查）
progress._check_download_status()
```

### 4. WebViewManager (src/android/webview.py)

```python
from android.webview import WebViewManager

# 创建WebView并启用媒体检测
webview = WebViewManager(
    media_detector=detector,
    on_media_detected=media_callback
)

# 加载URL
webview.load_url('https://example.com')

# 刷新页面
webview.reload()

# 返回
webview.go_back()
```

### 5. DownloadManager (src/core/downloader.py)

```python
from core.downloader import DownloadManager

download_manager = DownloadManager()

# 从检测结果下载（适配器方法）
task_id = download_manager.download_from_detected_url(
    url='https://example.com/video.mp4',
    media_type='video'  # 或 'audio'
)

# 取消下载
download_manager.cancel_task(task_id)

# 取消所有下载
download_manager.cancel_all()

# 获取任务状态
status = download_manager.get_task_status(task_id)
# → 'downloading'/'completed'/'failed'/'cancelled'
```

## 事件流

### 用户浏览网页
```python
# 用户在BrowserScreen中输入URL
def _on_go_pressed(self):
    url = self.url_input.text
    self.webview_manager.load_url(url)  # 加载网页
```

### 网页中有视频
```python
# WebView发起Media请求
# CustomWebViewClient.shouldInterceptRequest(view, request) 被调用

# Android线程中执行：
def _check_media_url(self, url):
    media_type = self.media_detector.detect_url(url)
    if media_type != MediaType.UNKNOWN:
        # 安全切到主线程
        Clock.schedule_once(
            lambda dt: self.callback(url, media_type),
            0
        )
```

### 回调处理
```python
# 主线程中执行
def _on_media_detected(self, url: str, media_type: str):
    """来自main.py的回调路由"""
    if isinstance(self.current_screen, BrowserScreen):
        self.current_screen.on_media_detected(url, media_type)

# BrowserScreen中处理
def on_media_detected(self, url, media_type):
    dialog = MediaDetectedDialog(
        url=url,
        media_type=media_type,
        on_download=self._on_media_download
    )
    dialog.open()
```

### 用户确认下载
```python
# 用户点击"确认下载"按钮
def _on_media_download(self, url, convert_to_mp3):
    # 创建下载任务
    task_id = self.download_manager.download_from_detected_url(
        url=url,
        media_type=self.media_type
    )
    
    # 显示进度对话框
    progress_dialog = DownloadProgressDialog(
        task_id=task_id,
        download_manager=self.download_manager
    )
    progress_dialog.open()
```

### 下载完成
```python
# DownloadProgressDialog自动检查状态
def _check_download_status(self):
    status = self.download_manager.get_task_status(self.task_id)
    
    if status == 'completed':
        # 自动关闭进度对话框
        self.dismiss()
        
        # 显示完成提示
        show_notification('下载完成')
        
    elif status == 'failed':
        show_error('下载失败')
```

## 配置和定制

### 修改检测规则

```python
# 在 MediaDetector 初始化后添加规则
detector.add_custom_pattern(
    pattern=r'mysite\.com/media/',
    media_type=MediaType.VIDEO
)
```

### 修改对话框样式

```python
# 在 MediaDetectedDialog._build_ui() 中修改
icon = '🎬 视频'  # 修改图标
title = '发现媒体资源'  # 修改标题
formats = ['MP3', '原始格式', '两者都要']  # 修改选项
colors = {
    'button': (0.2, 0.6, 1.0, 1),  # RGB + Alpha
    'background': (1, 1, 1, 1)
}
```

### 修改下载格式

```python
# 在 BrowserScreen._on_media_download() 中
format_choice = self.dialog.spinner.text

if '原始格式' in format_choice:
    convert_to_mp3 = False
elif '两者都要' in format_choice:
    # 需要修改 DownloadManager 支持此选项
    pass
else:
    convert_to_mp3 = True
```

## 调试技巧

### 查看日志

```bash
# 实时查看所有日志
adb logcat

# 过滤特定组件
adb logcat | grep MediaDetector
adb logcat | grep CustomWebViewClient
adb logcat | grep BrowserScreen
adb logcat | grep DownloadManager

# 保存日志到文件
adb logcat > logfile.txt
```

### 添加调试日志

```python
from kivy.logger import Logger

# 在你的代码中添加
Logger.info('YourComponent', 'Debug message')
Logger.warning('YourComponent', 'Warning message')
Logger.error('YourComponent', 'Error message')
```

### 测试MediaDetector规则

```python
# 创建测试脚本 test_detector.py
from core.media_detector import MediaDetector, MediaType

detector = MediaDetector()

test_urls = [
    'https://v.qq.com/x/page/abc123.html',
    'https://example.com/path/video.mp4',
    'https://music.qq.com/song/456.mp3',
]

for url in test_urls:
    result = detector.detect_url(url)
    expected = 'VIDEO' if 'v.qq' in url else ('AUDIO' if 'music' in url else 'UNKNOWN')
    status = '✓' if result.name == expected else '✗'
    print(f"{status} {url} → {result.name}")
```

### 模拟MediaDetection（不用真正的WebView）

```python
# 在 BrowserScreen 中添加测试方法
def test_media_detected(self, url, media_type):
    """模拟媒体检测，用于测试"""
    self.on_media_detected(url, media_type)

# 测试调用
browser.test_media_detected(
    'https://example.com/video.mp4',
    'video'
)
```

## 常见任务

### 1. 添加新的媒体检测规则

```python
# 在 MediaDetector 初始化时
detector.add_custom_pattern(
    r'yourdomain\.com/stream',  # 正则表达式
    MediaType.VIDEO
)
detector.add_custom_pattern(
    r'yourdomain\.com/audio',
    MediaType.AUDIO
)
```

### 2. 自定义下载格式选择

```python
# 修改 MediaDetectedDialog._build_ui()
self.format_spinner = Spinner(
    text='仅保存为MP3（推荐）',
    values=(
        '仅保存为MP3（推荐）',
        '保存原始格式',
        '同时保存两种格式',
        '仅保存音频'
    ),
    size_hint_x=1
)
self.format_spinner.bind(text=self._on_format_changed)
```

### 3. 处理特定网站的特殊格式

```python
def get_media_info(self, url):
    """获取媒体详细信息"""
    info = {'extension': '', 'domain': '', 'path': ''}
    
    # 特殊处理某些网站
    if 'bilibili.com' in url:
        # Bilibili使用特殊的流媒体格式
        info['format'] = 'dash'  # 动态自适应流媒体
    elif 'youtube.com' in url:
        # YouTube使用HLS格式
        info['format'] = 'hls'
    
    return info
```

### 4. 集成本地数据库记录下载历史

```python
# 在 DownloadManager 中添加
def log_download(self, url, media_type, filename, success):
    """记录下载历史到本地数据库"""
    import sqlite3
    import datetime
    
    conn = sqlite3.connect('downloads.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO download_history (url, media_type, filename, timestamp, success)
        VALUES (?, ?, ?, ?, ?)
    ''', (url, media_type, filename, datetime.datetime.now(), int(success)))
    
    conn.commit()
    conn.close()
```

## 设置和初始化顺序

```python
def build(self):
    # 1️⃣ 权限（Android only）
    self.permission_manager = PermissionManager()
    
    # 2️⃣ 下载管理
    self.download_manager = DownloadManager()
    
    # 3️⃣ 播放器
    self.player = MediaPlayer()
    
    # 4️⃣ 媒体检测（需要初始化正则表达式）
    self.media_detector = MediaDetector()
    
    # 5️⃣ WebView（最后，需要检测器）
    self.webview_manager = WebViewManager(
        media_detector=self.media_detector,
        on_media_detected=self._on_media_detected
    )
    
    # 6️⃣ 屏幕（需要所有管理器）
    self.switch_screen('browser')
```

## 故障排查决策树

```
问题：媒体无法检测
├─ 是否为已知网站？
│  ├─ 是 → 添加域名规则
│  └─ 否 → 通过JavaScript监听或pattern匹配
├─ URL是否被拦截？
│  ├─ 检查日志：shouldInterceptRequest被调用？
│  └─ 不是 → WebView配置问题
└─ 回调是否到达？
   └─ 检查日志：on_media_detected被调用？

问题：对话框未显示
├─ 媒体检测是否工作？（见上）
├─ BrowserScreen是否为当前屏幕？
│  └─ 检查：isinstance(self.current_screen, BrowserScreen)
└─ 对话框open()是否被调用？
   └─ 添加日志验证

问题：下载失败
├─ 网络连接？
├─ yt-dlp安装？
├─ ffmpeg可用？
└─ 存储权限？
```

---

**更多详细信息见：[MEDIA_DETECTION_GUIDE.md](./MEDIA_DETECTION_GUIDE.md)**  
**完整实现细节见：[IMPLEMENTATION_COMPLETE.md](./IMPLEMENTATION_COMPLETE.md)**
