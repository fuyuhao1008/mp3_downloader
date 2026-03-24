# 快速开始指南

## 最快开始（5分钟）

### 方案A：使用现成的APK（最快）

1. 从[GitHub Releases](https://github.com/your-username/mp3downloader/releases)下载最新的`mediadownloader-*.apk`
2. 在Android手机上安装APK
3. 打开应用，开始下载媒体

### 方案B：GitHub Actions云构建（10分钟）

1. Fork本仓库到你的GitHub账户
2. Push任何commit到`main`分支
3. 在GitHub Actions中等待构建完成
4. 下载生成的APK到手机安装

### 方案C：本地WSL2构建（30分钟）

#### 第1步：环境配置

```powershell
# Windows PowerShell（管理员）
# 启用WSL2（如需要）
wsl --install -d Ubuntu-22.04

# 在WSL2中
wsl

# 更新包管理器
sudo apt update && sudo apt upgrade -y

# 安装Python和Java
sudo apt install -y python3.11 python3.11-dev python3.11-venv openjdk-11-jdk gradle

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装buildozer
pip install buildozer cython
```

#### 第2步：构建APK

```bash
# 进入项目目录
cd /mnt/f/mp3downloader  # 从Windows挂载路径

# 首次构建（下载SDK/NDK，可能需要20-30分钟）
buildozer android debug

# 后续构建（只需5分钟）
buildozer android debug
```

#### 第3步：安装到手机

```bash
# 连接手机到电脑
# 在手机上启用USB调试（设置 > 关于手机 > 开发者选项 > USB调试）

adb devices  # 应该看到你的设备

# 安装APK
adb install -r bin/mediadownloader-*-debug.apk

# 或复制到手机后直接安装
adb push bin/mediadownloader-*-debug.apk /sdcard/Download/
```

## 详细步骤指南

### 环境要求检查清单

```bash
# 检查Python版本
python3 --version  # 应该是3.10+

# 检查Java版本
java -version  # 应该是 JDK 11

# 检查Git
git --version

# 检查ADB（Android Device Bridge）
adb version
```

如有缺失，安装相应工具：

```bash
# Ubuntu/WSL2
sudo apt install python3.11-dev openjdk-11-jdk adb

# macOS
brew install python@3.11 openjdk@11

# Windows（使用Chocolatey）
choco install python openjdk11 android-sdk
```

### 项目配置

#### 1. 克隆或下载项目

```bash
# 方案A：使用Git克隆
git clone https://github.com/your-username/mp3downloader.git
cd mp3downloader

# 方案B：手动下载
# 从GitHub下载ZIP并解压
unzip mp3downloader-main.zip
cd mp3downloader
```

#### 2. 配置应用信息

编辑`buildozer.spec`中的这些行：

```ini
[app]
title = MediaDownloader
package.name = mediadownloader
package.domain = org.example  # 改为你的域名，如 com.yourname

[app:buildozer]
android.package = org.example.mediadownloader  # 一致
android.name = MediaDownloader
```

#### 3. 配置应用权限

```.ini
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,MANAGE_EXTERNAL_STORAGE
```

### 首次构建

```bash
# 激活虚拟环境
source venv/bin/activate

# 调试构建（生成可安装的APK）
buildozer android debug

# 或详细模式（查看构建过程）
buildozer android debug -v

# 或清空缓存后重新构建
rm -rf .buildozer
buildozer android debug
```

**注意**：首次构建会下载约2-3GB的工具，可能需要20-30分钟。

### 构建输出

成功构建后，APK文件位置：

```
bin/mediadownloader-1.0.0-debug.apk  # 调试版本
```

使用`ls`命令查看：

```bash
ls -lh bin/*.apk
```

### 安装到设备

#### 方法1：通过ADB安装（需要USB调试）

```bash
# 列出连接的设备
adb devices

# 安装APK
adb install -r bin/mediadownloader-1.0.0-debug.apk

# 卸载（如需要）
adb uninstall org.example.mediadownloader

# 查看实时日志
adb logcat MediaDownloader:V
```

#### 方法2：手动安装

1. 在手机上启用"未知来源"应用安装（设置 > 安全）
2. 将APK文件复制到手机（通过USB或网络）
3. 在手机文件管理器中点击APK安装

### 验证安装

```bash
# 检查包是否安装
adb shell pm list packages | grep mediadownloader

# 启动应用
adb shell am start org.example.mediadownloader/.MainActivity

# 查看应用进程
ps aux | grep mediadownloader
```

## 构建选项

### 调试版本 vs 发布版本

```bash
# 调试版本（development）
buildozer android debug
# 特点：可debuggable，更大，快速构建
# 输出：bin/mediadownloader-*-debug.apk

# 发布版本（production）
buildozer android release
# 特点：优化的，更小，需要签名
# 输出：bin/mediadownloader-*-release-unsigned.apk
```

### 自定义构建选项

编辑`buildozer.spec`中的构建参数：

```ini
[buildozer]
log_level = 2                    # 日志级别（0-3）
warn_on_root = 1                 # 警告以root运行
use_local_toolchain = 1          # 使用本地工具链

# 性能选项
android.gradle_options = 
    org.gradle.parallel=true
    org.gradle.workers.max=4
```

## 常见问题快速解决

| 问题 | 解决方案 |
|------|--------|
| `buildozer: command not found` | `pip install buildozer` 并激活虚拟环境 |
| `Java not found` | 安装JDK 11：`sudo apt install openjdk-11-jdk` |
| `SDK not found` | 首次构建会自动下载，或配置`ANDROID_SDK_ROOT` |
| `NDK too new/old` | 在buildozer.spec中设置：`android.ndk = 25.2.9519653` |
| `Out of memory` | 增加内存：`export GRADLE_OPTS="-Xmx4096m"` |
| `Permission denied` | 运行`chmod +x buildozer` 或使用`sudo` |

## 开发和调试

### 实时调试

```bash
# 在一个终端监听日志
adb logcat -s MediaDownloader

# 在另一个终端推送更新
buildozer android debug
adb install -r bin/mediadownloader-*-debug.apk
```

### 修改代码并重新构建

```bash
# 编辑Python文件（src/ui/screens.py 等）
# 然后重新构建
buildozer android debug -v

# 快速构建（跳过某些步骤）
buildozer android debug --skip-update
```

### 日志分析

```bash
# 导出所有日志
adb logcat > build.log

# 查看应用活动日志
adb logcat *:S MediaDownloader:V

# 实时搜索特定错误
adb logcat | grep -i error
```

## 性能优化

### 减少APK大小

```bash
# 移除不必要的依赖，编辑buildozer.spec
requirements = python3,kivy  # 最小化

# 启用混淆和优化
android.gradle_options = 
    android.enableR8=true
```

### 加快构建速度

```bash
# 并行构建
export GRADLE_OPTS="-Dorg.gradle.parallel=true"

# 跳过不必要的检查
buildozer android debug --skip-update

# 增量构建（修改少量文件时）
buildozer android debug --skip-update
```

## 下一步

- 📖 阅读完整[README.md](README.md)了解所有功能
- 🔧 自定义`src/ui/screens.py`修改UI
- 🐛 查看[日志文件](buildozer/log_python_app.txt)调试问题
- 🚀 发布到Google Play或华为AppGallery

## 获取帮助

- 查看buildozer官方文档：<https://buildozer.readthedocs.io/>
- Kivy文档：<https://kivy.org/doc/>
- yt-dlp项目：<https://github.com/yt-dlp/yt-dlp>
- 本项目Issues：<https://github.com/your-username/mp3downloader/issues>

---

**祝你构建顺利！** 🎉
