[app]

# 应用信息
title = MediaDownloader
package.name = mediadownloader
package.domain = org.example

# 源代码
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json,md,yaml,yml,sh

# 版本
version = 1.0.0

# 需求
requirements = python3,kivy,yt-dlp,ffmpeg,ffpyplayer,pyjnius,requests,urllib3,python-dateutil,colorama,six

# 权限（Android）
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,MANAGE_EXTERNAL_STORAGE

# 功能
android.features = android.hardware.camera,android.hardware.microphone

# NDK/API级别
android.api = 31
android.minapi = 21
android.ndk = 25b
android.build_tools = 33.0.2
android.accept_sdk_license = True

# 支持的架构
android.archs = arm64-v8a,armeabi-v7a

# Gradle和构建设置
android.gradle_dependencies = androidx.core:core:1.10.1,androidx.appcompat:appcompat:1.6.1,androidx.constraintlayout:constraintlayout:2.1.4

# 后台服务（用于下载）
android.services = org.kivy.android.DownloadService:foreground

# 应用图标
# icon.filename = %(source.dir)s/assets/icon.png

# 应用预览图
# presplash.filename = %(source.dir)s/assets/presplash.png

# 主Activity
android.entrypoint = org.kivy.android.PythonActivity

# 应用theme
android.theme = @android:style/Theme.NoTitleBar.Fullscreen

# 支持的方向
android.orientation = portrait,sensorportrait

# Android特定配置
android.presplash_inside_package = 1
android.logcat_filters = *:S python:D

# 清单额外配置（FileProvider用于文件分享）
android.manifest_additions = 
	<provider
	    android:name="androidx.core.content.FileProvider"
	    android:authorities="${applicationId}.fileprovider"
	    android:exported="false">
	    <meta-data
	        android:name="android.support.FILE_PROVIDER_PATHS"
	        android:resource="@xml/file_paths" />
	</provider>

# 资源文件
android.add_src = buildozer/

[buildozer]

# 日志级别
log_level = 2

# 警告
warn_on_root = 1

# 使用缓存
use_local_toolchain = 1

# 构建目录
build_dir = .buildozer
bin_dir = ./bin

[app:buildozer]

# 打包信息
android.package = org.example.mediadownloader
android.name = MediaDownloader

# 应用签名
# 开发环境使用默认密钥，生产环境需配置真实keystore
# android.keystore = path/to/keystore.jks
# android.keystore_alias = alias_name
# android.keystore_alias_passwd = password

# 应用权限级别
android.permission_level = normal

# gradle包装器
android.gradle_wrapper = true

# 其他配置
android.gradle_options = 
	org.gradle.java.home=${JAVA_HOME}
	android.ndkVersion=25.2.9519653
	android.sdkVersion=33
