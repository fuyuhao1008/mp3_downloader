# MediaDownloader - Android媒体下载和播放应用

完整的Android APK应用，支持从Bilibili、YouTube等平台下载视频和音频，并本地播放。

## 功能特性

- ✅ 支持多个平台的媒体下载（Bilibili、YouTube、抖音等）
- ✅ 自动检测可下载的媒体资源
- ✅ 视频下载和MP3转换
- ✅ 本地媒体播放（视频/音频）
- ✅ 文件分享到微信等应用
- ✅ 华为鸿蒙系统支持
- ✅ 现代化UI（Kivy框架）
- ✅ 完整的错误处理和日志记录
- ✅ 后台下载服务

## 技术栈

| 组件 | 技术 | 备注 |
|------|------|------|
| **框架** | Kivy 2.3.0 | 唯一能打包APK的Python框架 |
| **下载** | yt-dlp | 支持多平台的媒体下载 |
| **转换** | FFmpeg | 视频/音频格式转换 |
| **播放** | ffpyplayer | 基于FFmpeg的播放器 |
| **Android集成** | pyjnius | 调用Android原生功能 |
| **权限管理** | androidx.core | 现代权限管理 |
| **构建** | Buildozer | 自动化APK构建 |

## 项目结构

```
mp3downloader/
├── main.py                      # 应用入口
├── requirements.txt             # Python依赖
├── buildozer.spec              # Buildozer配置（用于APK构建）
├── .github/
│   └── workflows/
│       └── build.yml           # GitHub Actions CI/CD配置
├── src/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   └── screens.py          # UI屏幕（下载、媒体库、播放器）
│   ├── core/
│   │   ├── __init__.py
│   │   ├── downloader.py       # yt-dlp下载管理
│   │   └── player.py           # ffpyplayer播放控制
│   ├── android/
│   │   ├── __init__.py
│   │   ├── permissions.py      # Android权限和存储管理
│   │   ├── webview.py          # 原生WebView集成（可选）
│   │   └── share.py            # 文件分享功能
│   └── utils/
│       ├── __init__.py
│       ├── constants.py        # 常量定义
│       └── logger.py           # 日志系统
└── buildozer/
    └── ...                      # Buildozer生成的文件
```

## 安装和构建

### 前置条件

- **系统要求**：Linux（Ubuntu 20.04+）或WSL2
- **Python**：3.10+
- **Java**：JDK 11+
- **Android SDK**：Level 31+
- **Android NDK**：25.2.9519653 或更新版本

### 方式1：使用GUI（Buildozer推荐）

#### 1. 环境配置

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装必要的依赖
sudo apt install -y \
    build-essential \
    git \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    openjdk-11-jdk \
    gradle \
    wget \
    curl

# 创建Python虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Linux/WSL2
# 或 venv\Scripts\activate  # Windows cmd
# 或 venv\Scripts\Activate.ps1  # Windows PowerShell

# 安装构建工具
pip install buildozer cython
```

#### 2. Android SDK 和 NDK 配置

```bash
# 使用Buildozer自动下载（推荐）
# Buildozer会在首次构建时自动下载相关工具

# 或手动配置环境变量
export ANDROID_SDK_ROOT=~/.buildozer/android/sdk
export ANDROID_NDK=~/.buildozer/android/ndk/25.2.9519653
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

#### 3. 构建APK

```bash
cd /path/to/mp3downloader

# 构建debug版本
buildozer android debug

# 或构建release版本（需要签名密钥）
buildozer android release
```

**输出文件**：`bin/mediadownloader-1.0.0-debug.apk`

### 方式2：使用GitHub Actions（云构建）

#### 配置

1. 将代码推送到GitHub
2. 进入 GitHub 仓库的 Actions 页面
3. 选择 Build Android APK 工作流
4. 点击 Run workflow，选择 build_type 为 release（或 debug）
5. 构建完成后在 Artifacts 中下载 APK

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

手动触发后，产物名称为：

- mediadownloader-release-apk
- mediadownloader-debug-apk

### 方式3：WSL2 + Docker（完全隔离环境）

```bash
# 使用Docker进行构建（避免本地环境污染）
docker run -it -v $(pwd):/src kivy/kivy:latest bash

cd /src
buildozer android debug
```

## 使用指南

### 安装APK到设备

```bash
# 列出连接的设备
adb devices

# 安装APK
adb install -r bin/mediadownloader-1.0.0-debug.apk

# 或直接在手机上点击APK文件安装
```

### 主要功能使用

#### 1. 下载媒体

1. 打开应用，进入"下载"标签页
2. 输入支持平台的媒体链接（B站、YouTube等）
3. 选择下载格式和质量
4. 点击"开始下载"

支持的平台：
- Bilibili (bilibili.com, b23.tv)
- YouTube (youtube.com, youtu.be)
- 抖音 (douyin.com, dyh.land)
- TikTok, Instagram, 微博等

#### 2. 媒体库

1. 进入"媒体库"标签页查看已下载文件
2. 点击"播放"播放媒体
3. 点击"分享"通过微信等应用分享
4. 点击"删除"删除本地文件

#### 3. 播放器

1. 进入"播放器"标签页
2. 点击"⏯"播放/暂停
3. 使用"⏪/⏩"快退/快进（各10秒）
4. 查看播放进度和剩余时间

## 配置说明

### buildozer.spec 关键配置

```ini
[app]
title = MediaDownloader              # 应用名称
package.name = mediadownloader       # 包名
package.domain = org.example         # 包域名
version = 1.0.0                      # 版本

[app:buildozer]
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 31                      # 目标API级别
android.minapi = 21                   # 最低API级别
android.ndk = 25b                     # NDK版本
android.archs = arm64-v8a,armeabi-v7a # 支持的架构
```

### 权限清单

| 权限 | 用途 |
|------|------|
| INTERNET | 下载媒体 |
| READ_EXTERNAL_STORAGE | 读取下载文件 |
| WRITE_EXTERNAL_STORAGE | 保存下载文件 |
| ACCESS_NETWORK_STATE | 检查网络状态 |
| FOREGROUND_SERVICE | 后台下载服务 |
| MANAGE_EXTERNAL_STORAGE | Android 11+文件访问 |

## 故障排查

### 常见问题

#### 1. "yt-dlp not installed"错误

```bash
# 确保requirements.txt包含yt-dlp
pip install yt-dlp

# 在buildozer.spec中添加依赖
requirements = python3,kivy,yt-dlp,ffmpeg,ffpyplayer,pyjnius
```

#### 2. NDK版本不匹配

```bash
# 清除缓存并重新构建
rm -rf .buildozer

# 或在buildozer.spec中指定正确的NDK版本
android.ndk = 25.2.9519653
```

#### 3. Java内存不足

```bash
# 增加Gradle堆内存
export GRADLE_OPTS="-Xmx4096m"
buildozer android debug
```

#### 4. 文件权限错误（只读分区）

自动处理：应用会首先尝试外部存储，失败时降级到应用私有目录

```python
# src/android/permissions.py 中的 get_downloads_dir()
# 优先级：外部存储 > 应用目录 > 缓存目录
```

### 调试技巧

```bash
# 查看实时日志
adb logcat | grep MediaDownloader

# 导出完整日志
adb logcat > app.log

# 连接调试器
adb shell am start -D -N org.example.mediadownloader/.MainActivity

# 访问应用文件（Android 11+）
adb shell "run-as org.example.mediadownloader ls /data/data/org.example.mediadownloader"
```

## 性能优化

### 内存管理

```python
# 下载管理器限制并发数
MAX_CONCURRENT_DOWNLOADS = 2

# 播放器自动资源清理
def __del__(self):
    self.stop()  # 确保释放资源
```

### 网络优化

```python
# 超时设置
SOCKET_TIMEOUT = 30
RETRY_ATTEMPTS = 3

# 分块下载
CHUNK_SIZE = 8192
```

### UI优化

- 使用线程进行耗时操作
- 定期更新进度（0.5秒间隔）
- 使用ScrollView处理长列表

## 安全性

### 权限安全

- 运行时权限请求（Android 6.0+）
- 最小权限原则
- 权限检查和降级方案

### 网络安全

- HTTPS支持
- SSL证书验证
- 超时和重试机制

### 文件安全

- FileProvider用于文件分享（避免直接路径暴露）
- 沙箱存储（应用专属目录）
- 文件加密（可选）

## 构建和发布

### 签名生成

```bash
# 生成签名密钥（一次性）
keytool -genkey -v -keystore my-key.keystore \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias my-app

# 在buildozer.spec中配置
android.keystore = /path/to/my-key.keystore
android.keystore_alias = my-app
android.keystore_alias_passwd = password
```

### Release版本构建

```bash
buildozer android release
# 输出：bin/mediadownloader-1.0.0-release-unsigned.apk

# 对齐和签名
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore my-key.keystore \
  bin/mediadownloader-1.0.0-release-unsigned.apk my-app

zipalign -v 4 \
  bin/mediadownloader-1.0.0-release-unsigned.apk \
  mediadownloader-1.0.0-release.apk
```

### 上传到应用市场

支持的平台：
- Google Play Store
- 华为AppGallery
- 小米应用商店
- 腾讯应用宝
- GitHub Releases

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 支持

如有问题或建议，请：
1. 查看项目Issues
2. 提交新Issue描述问题
3. Fork并提交Pull Request

---

**更新日期**：2024年
**最后验证版本**：1.0.0
**Python版本**：3.10+
**最低Android版本**：6.0（API 21）
**建议Android版本**：10.0+（API 29+）
