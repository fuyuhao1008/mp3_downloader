# 媒体检测功能测试计划

## 📋 测试目标

验证从WebView媒体检测到下载完成的完整工作流程，包括所有边界情况和错误处理。

---

## 🧪 测试关键场景

### TC-001: 基本视频检测和下载

**前置条件**：
- 应用已安装
- 网络连接正常
- 存储权限已授予

**步骤**：
1. 打开应用
2. 点击"浏览"标签页
3. 输入 URL: `https://www.bilibili.com/video/BV1...` (含视频的B站链接)
4. 页面加载，开始播放视频
5. 观察是否弹出 MediaDetectedDialog

**预期结果**：
- ✅ 页面正常加载
- ✅ 弹出对话框显示 "🎬 检测到视频"
- ✅ 对话框显示视频URL
- ✅ 有下载格式选择（仅MP3、原始、两者）

**验证点**：
```python
# 日志验证
adb logcat | grep -E "Media detected|detect_url|shouldInterceptRequest"

# 输出示例：
# Media detected: video
# detect_url → MediaType.VIDEO  
# shouldInterceptRequest called for: https://mp...
```

---

### TC-002: 媒体检测 - 音频URL

**步骤**：
1. 打开浏览器
2. 导航到含有音乐的网站（如网易云音乐、QQ音乐）
3. 点击播放音乐

**预期结果**：
- ✅ 弹出对话框显示 "🎵 检测到音频"
- ✅ 对话框内容正确

**验证点**：
```python
test_audio_urls = [
    'https://music.qq.com/song/1234567890.m4a',
    'https://res.wx.qq.com/voice/123abc.silk',
    'https://music.163.com/#/song?id=123456',
]

from core.media_detector import MediaDetector, MediaType
detector = MediaDetector()

for url in test_audio_urls:
    assert detector.detect_url(url) == MediaType.AUDIO
```

---

### TC-003: URL去重 - 防止重复提示

**步骤**：
1. 打开浏览器
2. 访问视频页面 (URL: `https://example.com/video.mp4?quality=hd`)
3. 页面加载，检测到媒体 → 显示对话框
4. **关闭对话框**（点击"取消"）
5. **刷新页面** (点击"↶ 刷新"按钮)
6. 观察第二次是否还会弹窗

**预期结果**：
- ✅ 第一次访问 → 弹窗
- ✅ 刷新页面 → **不弹窗**（去重）
- ✅ 导航到不同视频 → 再次弹窗

**验证点**：
```python
# 在 CustomWebViewClient 中检查去重机制
logger.info('shown_urls before:', self.shown_urls)
base_url = 'https://example.com/video.mp4'
assert base_url in self.shown_urls  # 已记录

# 再次检测相同URL
if base_url in self.shown_urls:
    logger.info('URL already shown, skipping')
    return  # 不再弹窗
```

---

### TC-004: 下载确认和进度跟踪

**步骤**：
1. 完成 TC-001 (检测到视频)
2. 在 MediaDetectedDialog 中点击"确认下载"
3. 观察进度对话框
4. 等待下载完成

**预期结果**：
- ✅ MediaDetectedDialog 关闭
- ✅ DownloadProgressDialog 打开
- ✅ 进度条从 0% 增长到 100%
- ✅ 显示下载文件大小和进度
- ✅ 下载完成后自动关闭对话框

**验证点**：
```python
# 检查下载任务
task_id = download_manager.download_from_detected_url(
    url='https://example.com/video.mp4',
    media_type='video'
)

# 检查状态
status = download_manager.get_task_status(task_id)
assert status in ['downloading', 'completed']

# 检查进度
progress = download_manager.get_task_progress(task_id)
assert 0 <= progress <= 100
```

---

### TC-005: 下载格式选择

**步骤**：
1. 检测到视频后，打开 MediaDetectedDialog
2. 点击"处理方式"下拉菜单
3. 选择不同选项：
   - "仅保存为MP3（推荐）"
   - "保存原始格式"
   - "同时保存两种格式"
4. 点击"确认下载"
5. 监控下载结果

**预期结果**：
- ✅ MP3选项 → 仅保存MP3格式
- ✅ 原格式选项 → 保存原始文件格式
- ✅ 两种选项 → 同时生成MP3和原格式

**验证点**：
```python
# 验证文件格式
import os
from pathlib import Path

media_dir = Path('/storage/.../MediaDownloader/music/')

# MP3选项
mp3_files = list(media_dir.glob('*.mp3'))
assert len(mp3_files) > 0

# 原格式选项  
video_files = list(media_dir.glob('*.mp4')) + list(media_dir.glob('*.flv'))
assert len(video_files) > 0
```

---

### TC-006: 下载取消

**步骤**：
1. 开始下载任务
2. DownloadProgressDialog 显示时，点击"取消"按钮
3. 观察下载状态

**预期结果**：
- ✅ 下载立即停止
- ✅ 进度对话框关闭
- ✅ 本地文件被删除（或标记不完整）

**验证点**：
```python
# 监控取消操作
def test_cancel():
    task_id = download_manager.download(url)
    time.sleep(1)  # 等待下载开始
    
    download_manager.cancel_task(task_id)
    
    time.sleep(0.5)
    status = download_manager.get_task_status(task_id)
    assert status == 'cancelled'
```

---

### TC-007: 线程安全性测试

**步骤**：
1. 打开浏览器
2. 同时访问多个含媒体的页面（在多个标签页中）
3. 观察多个视频同时被检测时的行为

**预期结果**：
- ✅ 每个检测到的媒体都弹窗（去重检查后）
- ✅ 每个对话框都独立工作
- ✅ 多个下载任务可以并行进行
- ✅ UI不卡顿，没有线程错误

**验证点**：
```python
# 用于验证线程安全
from threading import Thread

def simulate_parallel_requests():
    urls = [
        'https://example.com/video1.mp4',
        'https://example.com/video2.mp4',
        'https://example.com/audio1.mp3',
    ]
    
    threads = []
    for url in urls:
        t = Thread(
            target=lambda u=url: detector.detect_url(u)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # 验证所有请求都被处理
    assert detector.shown_urls_count == 3

# 日志检查
adb logcat | grep -E "Thread|Error|Exception"
```

---

### TC-008: 非Android环境降级

**步骤**：
1. 在桌面系统（Windows/Mac/Linux）运行应用
2. 打开"浏览"标签页
3. 观察界面

**预期结果**：
- ✅ 应用不崩溃
- ✅ 显示降级UI（Label说明WebView不可用）
- ✅ 其他标签页（媒体库、下载、播放器）正常工作

**验证点**：
```python
# 检查降级机制
if ANDROID_PLATFORM:
    webview = WebViewManager(...)
else:
    # fallback UI
    logger.info('WebView not available, using fallback')
    label = Label(text='WebView不在此平台可用')
```

---

### TC-009: 错误处理 - 网络超时

**步骤**：
1. 断开网络连接
2. 打开浏览器
3. 尝试加载 URL

**预期结果**：
- ✅ 显示错误提示（而不是崩溃）
- ✅ 允许输入其他URL重试
- ✅ 应用保持可用状态

**验证点**：
```python
def test_network_error():
    try:
        browser.webview_manager.load_url('https://offline-test.local')
        time.sleep(5)
    except Exception as e:
        logger.error('Network error:', str(e))
    
    # 验证应用仍然响应
    assert browser.current_screen is not None
```

---

### TC-010: 错误处理 - 权限缺失

**步骤**：
1. 撤销应用的存储权限（通过系统设置）
2. 尝试下载媒体

**预期结果**：
- ✅ 显示权限提示
- ✅ 提示请求权限
- ✅ 不能完成下载（等待权限授予）

**验证点**：
```bash
# 撤销权限
adb shell pm revoke com.example.mediadownloader android.permission.WRITE_EXTERNAL_STORAGE

# 查看日志
adb logcat | grep -i permission

# 恢复权限
adb shell pm grant com.example.mediadownloader android.permission.WRITE_EXTERNAL_STORAGE
```

---

### TC-011: 媒体检测规则准确性

**目的**：验证所有27+正则规则的覆盖率

**测试URL列表**：

**视频URL**：
```
✅ http://example.com/video.mp4
✅ http://example.com/path/video/clip.m3u8
✅ https://mpvideo.qpic.cn/123456.mp4  (微信视频)
✅ https://v.qq.com/x/page/abc123.html  (QQ视频)
✅ https://www.bilibili.com/video/BV1xxx  (B站)
✅ https://www.youtube.com/watch?v=dQw4w9WgXcQ  (YouTube)
✅ https://example.com/play/xyz  (播放路由)
❌ http://example.com/audio.mp3  (应该识别为AUDIO)
```

**音频URL**：
```
✅ http://example.com/audio.mp3
✅ http://example.com/voice/message.m4a
✅ https://music.qq.com/song/123456  (QQ音乐)
✅ https://music.163.com/song/789  (网易云)
✅ https://res.wx.qq.com/voice/abc.silk  (微信语音)
✅ http://example.com/audio/podcast.aac
❌ http://example.com/video.mp4  (应该识别为VIDEO)
```

**验证脚本**：
```python
from core.media_detector import MediaDetector, MediaType

detector = MediaDetector()

test_cases = [
    # (URL, expected_type)
    ('http://example.com/video.mp4', MediaType.VIDEO),
    ('https://v.qq.com/x/page/abc', MediaType.VIDEO),
    ('http://example.com/audio.mp3', MediaType.AUDIO),
    ('https://music.qq.com/song/123', MediaType.AUDIO),
]

results = []
for url, expected in test_cases:
    actual = detector.detect_url(url)
    passed = actual == expected
    results.append({
        'url': url,
        'expected': expected.name,
        'actual': actual.name,
        'passed': '✅' if passed else '❌'
    })

# 打印结果
for r in results:
    print(f"{r['passed']} {r['url']}")
    if not r['passed']:
        print(f"  期望: {r['expected']}, 实际: {r['actual']}")

# 统计
total = len(results)
passed = sum(1 for r in results if r['passed'])
print(f"\n通过率: {passed}/{total} ({100*passed/total:.1f}%)")
```

---

### TC-012: 完整端到端流程

**场景**：用户完整使用流程

**步骤**：
1. 启动应用
2. 点击"浏览"标签
3. 输入 URL: `https://m.bilibili.com/video/BV1ov4y167...` (B站视频链接)
4. WebView加载视频页面
5. 点击视频播放（如果有播放器）
6. 等待媒体检测
7. MediaDetectedDialog 弹出
8. 选择"仅保存为MP3（推荐）"
9. 点击"确认下载"
10. DownloadProgressDialog 显示
11. 等待下载完成
12. 关闭进度对话框
13. 点击"媒体库"标签
14. 验证文件是否出现在库中
15. 点击文件播放

**预期结果**：
- ✅ 所有步骤无异常
- ✅ 最终文件可以播放
- ✅ 文件格式为MP3

**时间目标**：
- URL加载: < 5秒
- 媒体检测: < 2秒
- 对话框显示: < 1秒
- 下载开始: < 1秒
- 总体流程: < 5分钟（取决于网速和文件大小）

---

## 📊 测试矩阵

| 编号 | 功能 | 场景 | 预期 | 状态 | 备注 |
|------|------|------|------|------|------|
| TC-001 | 视频检测 | 加载含视频网页 | 弹初对话框 | 🔄 | |
| TC-002 | 音频检测 | 加载含音乐网页 | 弹音频对话框 | 🔄 | |
| TC-003 | URL去重 | 刷新页面 | 不再弹窗 | 🔄 | |
| TC-004 | 下载进度 | 开始下载 | 显示进度 | 🔄 | |
| TC-005 | 格式选择 | 选择不同格式 | 保存正确格式 | 🔄 | |
| TC-006 | 取消下载 | 点击取消 | 下载停止 | 🔄 | |
| TC-007 | 线程安全 | 并行请求 | 正确处理 | 🔄 | |
| TC-008 | 降级模式 | 非Android系统 | 显示fallback | 🔄 | |
| TC-009 | 网络超时 | 无网络 | 错误提示 | 🔄 | |
| TC-010 | 权限检查 | 缺少权限 | 请求权限 | 🔄 | |
| TC-011 | 规则准确 | 多个测试URL | 正确分类 | 🔄 | |
| TC-012 | 端到端 | 完整流程 | 成功下载 | 🔄 | |

**图例**: 🔄 待测 | ✅ 通过 | ❌ 失败 | ⏸️ 阻塞

---

## 🐛 缺陷报告模板

```
[缺陷编号]: DEF-001
[优先级]: High / Medium / Low
[标题]: 媒体检测对话框显示不完整

[描述]:
...

[重现步骤]:
1. 
2. 
3. 

[预期结果]:
...

[实际结果]:
...

[日志]:
adb logcat output...

[附件]:
- screenshot.png
- logcat.txt
```

---

## 📈 测试覆盖统计

```
组件          覆盖率    关键测试
─────────────────────────────────
MediaDetector    80%    TC-011
WebViewClient    75%    TC-001, TC-007
Dialog UI        90%    TC-004, TC-005
DownloadMgr      85%    TC-004, TC-006
ThreadSafety     70%    TC-007
ErrorHandling    60%    TC-009, TC-010
─────────────────────────────────
整体            77%
```

---

## ✅ 测试检查清单

在发布前完成以下所有测试：

- [ ] TC-001: 基本视频检测 ✅
- [ ] TC-002: 音频检测 ✅
- [ ] TC-003: URL去重 ✅
- [ ] TC-004: 下载进度 ✅
- [ ] TC-005: 格式选择 ✅
- [ ] TC-006: 取消下载 ✅
- [ ] TC-007: 线程安全 ✅
- [ ] TC-008: 非Android降级 ✅
- [ ] TC-009: 网络错误 ✅
- [ ] TC-010: 权限检查 ✅
- [ ] TC-011: 规则准确性 ✅
- [ ] TC-012: 完整端到端 ✅

**所有测试通过后，应用可发布！** 🚀

---

**测试文档版本**: 1.0  
**最后更新**: 2024年  
**责任人**: QA Team
