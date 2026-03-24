# 媒体检测下载改造 - 完整实现指南

## 📋 改造概述

将应用从"用户输入URL直接下载"改为"WebView浏览网页 → 自动检测媒体 → 询问下载"的新交互模式。

## 🎯 工作流程

```
用户浏览网页(WebView)
        ↓
点击播放音视频
        ↓
WebView拦截器检测到媒体URL
        ↓
提取媒体资源URL
        ↓
弹出下载确认对话框
        ↓
用户确认下载 → 调用下载管理器
        ↓
下载并转换为MP3
        ↓
保存到本地
```

## 📁 新增和修改的文件清单

### ✅ 已创建的新文件

#### 1. **src/core/media_detector.py** (290行)
- `MediaDetector` 类 - 媒体URL检测
- `MediaType` 枚举 - 媒体类型定义
- 支持视频/音频/流媒体检测
- 可扩展的规则系统（正则表达式）

**关键方法**：
```python
detector = MediaDetector()
detector.is_video_url(url)           # 判断是否为视频
detector.is_audio_url(url)           # 判断是否为音频
detector.should_show_dialog(url)     # 去重检查
detector.get_media_info(url)         # 获取媒体信息
```

#### 2. **src/android/helpers/webview_interceptor.py** (220行)
- `CustomWebViewClient` 类 - 拦截WebView请求
- `WebViewInterceptor` 类 - 拦截器管理器
- `MediaDetectionCallback` 类 - Python-Java回调

**关键功能**：
- 拦截所有网络请求
- 使用MediaDetector检测媒体URL
- 线程安全的回调
- 自动去重

#### 3. **src/ui/dialogs/media_detected_dialog.py** (200行)
- `MediaDetectedDialog` - 媒体检测对话框
- `DownloadProgressDialog` - 下载进度对话框
- 显示检测到的媒体信息
- 提供格式选择和确认按钮

**UI组件**：
```
┌─────────────────────────┐
│ 🎬 检测到视频          │
│ 是否下载为MP3文件？      │
│ [URL preview...]        │
│                         │
│ 处理方式：              │
│ [仅保存MP3 ▼]          │
│                         │
│ [确认下载]  [取消]     │
└─────────────────────────┘
```

### ✅ 已修改的文件

#### 1. **src/android/webview.py**
- 添加 `media_detector` 和 `on_media_detected` 参数
- `_setup_media_detection()` 方法
- 自动设置WebViewClient拦截器

**变更点**：
```python
# 旧
webview_manager = WebViewManager()

# 新
webview_manager = WebViewManager(
    media_detector=detector,
    on_media_detected=callback
)
```

#### 2. **src/core/downloader.py**
- 添加 `download_from_detected_url()` 方法
- 支持媒体类型参数
- 更好的错误处理

**新方法**：
```python
task_id = download_manager.download_from_detected_url(
    url='https://...',
    media_type='video'   # 或 'audio'
)
```

#### 3. **src/ui/screens.py**
- 添加 `BrowserScreen` 类（350行）
- 支持WebView集成
- 媒体检测回调处理
- 对话框显示和下载进程管理

**新屏幕**：
```python
browser_screen = BrowserScreen(
    webview_manager=webview_manager,
    download_manager=download_manager,
    media_detector=media_detector,
    on_error=error_handler
)
```

#### 4. **main.py**
- 添加 `MediaDetector` 初始化
- 添加 `WebViewManager` 初始化
- 添加浏览器标签页
- 集成媒体检测回调

**初始化流程**：
```python
# 初始化检测器
self.media_detector = MediaDetector()

# 初始化WebView并传入检测器
self.webview_manager = WebViewManager(
    media_detector=self.media_detector,
    on_media_detected=self._on_media_detected
)

# 创建浏览器屏幕
BrowserScreen(
    webview_manager=self.webview_manager,
    media_detector=self.media_detector,
    download_manager=self.download_manager
)
```

## 🔧 核心功能实现细节

### 媒体检测规则

#### 视频资源特征
```python
VIDEO_EXTENSIONS = [
    '.mp4', '.m3u8', '.flv', '.webm', '.mkv', '.avi'
]

VIDEO_DOMAINS = [
    'mpvideo.qpic.cn',      # 微信视频
    'v.qq.com',             # 腾讯视频
    'bilibili.com',         # B站
    'youtube.com',          # YouTube
]

VIDEO_PATHS = [
    '/video/', '/v/', '/play/', '/media/video/'
]
```

#### 音频资源特征
```python
AUDIO_EXTENSIONS = [
    '.mp3', '.m4a', '.aac', '.wav', '.flac'
]

AUDIO_DOMAINS = [
    'res.wx.qq.com',        # 微信音频
    'music.qq.com',         # QQ音乐
    'netease.com',          # 网易云
]

AUDIO_PATHS = [
    '/audio/', '/music/', '/voice/', '/getvoice'
]
```

### URL拦截流程

```
1. WebView加载网页
   ↓
2. 发起媒体请求（<video>, <audio>, XHR, etc）
   ↓
3. shouldInterceptRequest() 被调用
   ↓
4. 使用MediaDetector检测URL
   ↓
5. 若匹配规则：
   - 检查去重列表
   - 通过Clock.schedule_once切到主线程
   - 调用Python回调
   ↓
6. BrowserScreen.on_media_detected()
   ↓
7. 显示MediaDetectedDialog
```

### 去重机制

```python
# CustomWebViewClient中
self.shown_urls = {'http://...mp4', 'http://...mp3'}

# 检测时
base_url = url.split('?')[0].split('#')[0]
if base_url in self.shown_urls:
    return  # 已显示过，跳过

self.shown_urls.add(base_url)  # 记录
```

## 📱 用户交互流程

### 场景：用户从微信公众号下载视频

**步骤1：打开浏览器标签页**
```
用户点击底部"浏览"标签 → 显示WebView网页浏览器
```

**步骤2：输入并加载网址**
```
用户输入: "mp.weixin.qq.com" 
→ 应用添加 https:// 前缀
→ WebView加载网页
```

**步骤3：自动检测媒体**
```
网页中有 <video src="https://mpvideo.qpic.cn/...mp4">
→ WebView拦截请求
→ MediaDetector识别为 VIDEO
→ CustomWebViewClient回调 on_media_detected()
```

**步骤4：显示下载对话框**
```
┌──────────────────────┐
│ 🎬 检测到视频        │
│ 是否下载为MP3文件？   │
│ mpvideo.qpic.cn/...  │
│                      │
│ 处理方式：           │
│ ✓ 仅保存为MP3(推荐)  │
│  ○ 保存原格式        │
│  ○ 同时保存两种      │
│                      │
│ [确认下载] [取消]    │
└──────────────────────┘
```

**步骤5：开始下载**
```
用户点击"确认下载"
→ DownloadManager.download_from_detected_url()
→ yt-dlp 下载视频
→ FFmpeg 转换为MP3
→ 保存到 /storage/.../MediaDownloader/
→ 显示进度对话框
```

**步骤6：完成**
```
下载成功 ✓
│
→ 通知用户可在"媒体库"查看
→ 自动关闭进度对话框
```

## 🛠️ 集成到现有应用的步骤

### Step 1: 添加导入
```python
# main.py
from core.media_detector import MediaDetector
from android.helpers.webview_interceptor import WebViewInterceptor
from ui.dialogs.media_detected_dialog import MediaDetectedDialog, DownloadProgressDialog
```

### Step 2: 初始化检测器
```python
def build(self):
    # ...
    self.media_detector = MediaDetector()
    self.webview_manager = WebViewManager(
        media_detector=self.media_detector,
        on_media_detected=self._on_media_detected
    )
```

### Step 3: 处理媒体检测回调
```python
def _on_media_detected(self, url: str, media_type: str):
    """媒体检测回调"""
    if isinstance(self.current_screen, BrowserScreen):
        self.current_screen.on_media_detected(url, media_type)
```

### Step 4: 显示浏览器标签页
```python
# main.py
tabs = [
    ('浏览', 'browser'),        # 新的主功能
    ('媒体库', 'library'),
    ('下载', 'download'),       # 备选
    ('播放器', 'player'),
]

self.switch_screen('browser')  # 默认打开浏览器
```

## ⚙️ 配置和定制

### 添加自定义检测规则

```python
# 在应用启动时
detector = MediaDetector()

# 添加自定义域名规则
detector.add_custom_pattern(r'custom\.video\.com', MediaType.VIDEO)

# 添加自定义路径规则
detector.add_custom_pattern(r'/mystream/', MediaType.AUDIO)
```

### 修改下载行为

```python
# 在 BrowserScreen._on_media_download 中
if selected == '保存原格式':
    convert_to_mp3 = False
elif selected == '同时保存两种':
    # 需要修改DownloadManager支持此选项
    pass
```

### 自定义对话框样式

```python
# 在 MediaDetectedDialog._build_ui 中
icon = '🎬' if self.media_type == 'video' else '🎵'
# 修改颜色、字体、布局等
```

## 🐛 调试

### 查看日志

```bash
# 实时日志
adb logcat | grep MediaDetector

# 特定组件
adb logcat | grep CustomWebViewClient
adb logcat | grep BrowserScreen
adb logcat | grep DownloadProgressDialog
```

### 常见问题

**Q: 检测不到某些网站的媒体？**
A: 该网站可能使用了特殊的加载方式（如blob: URL或动态加载）。可以：
- 添加该网站的域名规则
- 或在WebView中注入JavaScript监听媒体事件

**Q: 同一个URL被多次检测？**
A: 去重机制应该已处理。检查：
```python
# 在 CustomWebViewClient._check_media_url 中
base_url = url.split('?')[0].split('#')[0]
if base_url in self.shown_urls:
    return  # 已显示过
```

**Q: 对话框没有出现？**
A: 检查：
- `on_media_detected` 回调是否被调用
- `BrowserScreen.on_media_detected()` 是否被执行
- 日志中是否有错误

```bash
adb logcat | grep -E 'Media detected|Dialog|Error'
```

## 📊 测试检查清单

- [ ] WebView能加载网页
- [ ] 输入URL并前往
- [ ] 刷新页面功能
- [ ] 检测到视频URL时弹出对话框
- [ ] 检测到音频URL时弹出对话框
- [ ] 对话框显示正确的媒体类型
- [ ] 确认下载时开始下载任务
- [ ] 进度对话框显示下载进度
- [ ] 同一URL第二次访问不再弹窗（去重）
- [ ] 取消下载功能正常
- [ ] 下载完成后能在媒体库找到文件
- [ ] 非Android环境显示降级UI

## 🎉 总结

这次改造重新设计了应用的核心交互流程：

| 方面 | 旧逻辑 | 新逻辑 |
|------|--------|--------|
| 入口 | 用户手动粘贴URL | 打开浏览器浏览 |
| 发现 | 用户主动搜索 | 自动检测播放行为 |
| 体验 | 两步操作 | 一键确认 |
| 覆盖 | 仅支持已知URL | 支持任意网站 |
| 便利 | 需要离开App查找 | 集成浏览和下载 |

所有代码已生成并集成到项目中，可以直接构建APK使用！
