# 开发指南

本文档为开发者提供贡献指南和开发工作流。

## 开发工作流

### 1. 环境设置

```bash
# Fork 项目
git clone https://github.com/your-username/mp3downloader.git
cd mp3downloader

# 创建开发分支
git checkout -b feature/your-feature-name

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black pylint
```

### 2. 代码结构

```
src/
├── ui/              # 用户界面
│   └── screens.py   # 应用屏幕组件
├── core/            # 核心功能
│   ├── downloader.py # 下载管理
│   └── player.py    # 播放控制
├── android/         # Android集成
│   ├── permissions.py # 权限管理
│   ├── webview.py    # WebView包装
│   └── share.py      # 文件分享
└── utils/          # 工具函数
    ├── constants.py # 常量定义
    └── logger.py    # 日志系统
```

### 3. 代码编写规范

#### Python风格

遵循PEP 8标准：

```python
# ✓ 好的代码

def download_media(url: str, output_dir: str) -> str:
    """
    下载媒体文件
    
    Args:
        url: 媒体URL
        output_dir: 输出目录
        
    Returns:
        下载文件路径
        
    Raises:
        ValueError: 无效URL
        IOError: 文件写入错误
    """
    if not url:
        raise ValueError('URL cannot be empty')
    
    # 实现逻辑...
    return file_path


# ✗ 不好的代码
def download(u, o):
    if not u:
        return None
    # 缺少文档和类型注解
    return x
```

#### 导入顺序

```python
# 标准库
import os
import sys
from pathlib import Path
from typing import Optional, Dict

# 第三方库
from kivy.app import App
from kivy.logger import Logger

# 本地模块
from utils.constants import APP_NAME
from core.downloader import DownloadManager
```

#### 错误处理

```python
# ✓ 好的错误处理
try:
    result = self.downloader.download(url)
except FileNotFoundError as e:
    Logger.error('UI', f'File not found: {e}')
    self.show_error('文件不存在', str(e))
except Exception as e:
    Logger.error('UI', f'Unexpected error: {e}')
    self.show_error('错误', '发生了意外错误')

# ✗ 避免这样
except:
    pass  # 吞掉所有异常！
```

### 4. 代码质量检查

```bash
# 代码格式检查
flake8 src/ main.py --count --show-source --statistics

# 代码格式化
black src/ main.py

# 代码风格检查
pylint src/ main.py --disable=all --enable=E,W

# 类型检查
mypy src/ --ignore-missing-imports

# 代码覆盖率
pytest --cov=src tests/
```

### 5. 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_downloader.py

# 带显示输出的测试
pytest -s -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 功能开发指南

### 添加新的下载器支持

```python
# 在 src/core/downloader.py 中
class DownloadManager:
    SUPPORTED_PLATFORMS = {
        'youtube': 'YouTube',
        'bilibili': 'Bilibili',
        'tiktok': 'TikTok',
        # 添加新平台
        'newsite': 'New Site',
    }
    
    def _detect_platform(self, url: str) -> Optional[str]:
        """检测URL来自哪个平台"""
        for platform, name in self.SUPPORTED_PLATFORMS.items():
            if platform in url:
                Logger.info('Downloader', f'Detected: {name}')
                return platform
        return None
```

### 添加新的UI屏幕

```python
# 在 src/ui/screens.py 中
class NewScreen(BoxLayout):
    """新屏幕类"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # 添加UI组件...
        self.add_widget(Label(text='新屏幕'))
    
    def on_button_click(self, instance):
        """按钮点击处理"""
        Logger.info('NewScreen', 'Button clicked')

# 在 main.py 中注册
elif screen_id == 'new':
    self.current_screen = NewScreen()
```

### 添加新的权限

```python
# 在 src/android/permissions.py 中
class PermissionManager:
    REQUIRED_PERMISSIONS = [
        # ... 现有权限
        'android.permission.NEW_PERMISSION',
    ]
```

## Git工作流

### 提交规范

使用约定式提交（Conventional Commits）：

```bash
# 格式
git commit -m "<type>(<scope>): <subject>"

# 类型
feat:    新功能
fix:     bug修复
docs:    文档更新
style:   代码风格（无逻辑改变）
refactor: 代码重构
perf:    性能改进
test:    测试相关
chore:   构建/依赖更新

# 示例
git commit -m "feat(downloader): support new platform"
git commit -m "fix(ui): correct screen layout"
git commit -m "docs(readme): update build instructions"
```

### 分支命名

```bash
feature/add-new-ui          # 新功能
bugfix/fix-download-issue   # 修复bug
docs/update-readme          # 文档更新
refactor/clean-code         # 代码重构
```

### 提交PR

1. 创建本地分支
2. 进行修改和提交
3. Push到fork的仓库
4. 创建Pull Request
5. 等待代码审查
6. 合并到主分支

## 调试技巧

### Kivy调试

```python
# 启用调试模式
from kivy.logger import Logger
Logger.setLevel('debug')

# 输出调试信息
Logger.debug('MyScreen', f'Variable value: {value}')

# 性能检测
from kivy.clock import Clock
Clock.create_trigger(self._update, 0.5)  # 每0.5秒调用
```

### Android调试

```bash
# 查看日志
adb logcat -s MediaDownloader

# 访问应用文件
adb shell
$ run-as org.example.mediadownloader
$ ls -la /data/data/org.example.mediadownloader

# 调试Python代码
adb forward tcp:5555 tcp:5555
# 在IDE中设置远程调试
```

### 性能分析

```python
import time
import cProfile

# 测量函数耗时
start = time.time()
do_something()
elapsed = time.time() - start
print(f'耗时: {elapsed:.2f}s')

# 性能分析
profiler = cProfile.Profile()
profiler.enable()
do_something()
profiler.disable()
profiler.print_stats()
```

## 文档更新

### 更新README

```markdown
# 按模块组织

## 下载模块
说明...

## UI模块
说明...
```

### 代码注释

```python
class MyClass:
    """
    类的简要说明
    
    详细说明（可选）
    
    Attributes:
        attr1: 属性1说明
        attr2: 属性2说明
    """
    
    def my_method(self, param1: str) -> bool:
        """
        方法说明
        
        Args:
            param1: 参数1说明
            
        Returns:
            返回值说明
            
        Raises:
            ValueError: 异常说明
        """
        pass
```

## 发布流程

### 版本控制

使用语义化版本（Semantic Versioning）：

```
X.Y.Z
│ │ └─ Patch（bug修复）
│ └─── Minor（新功能，向后兼容）
└───── Major（重大更新，可能不兼容）

示例：1.0.0 → 1.0.1（修复） → 1.1.0（新功能） → 2.0.0（大版本）
```

### 发布检查清单

- [ ] 所有测试通过
- [ ] 代码检查通过
- [ ] README和文档更新
- [ ] CHANGELOG更新
- [ ] 版本号更新
- [ ] Git标签创建
- [ ] GitHub Release发布
- [ ] APK上传

### 发布命令

```bash
# 更新版本号
# 编辑 buildozer.spec, main.py, src/utils/constants.py

# 提交版本更新
git add .
git commit -m "chore: bump version to 1.1.0"

# 创建标签
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# GitHub会自动触发Actions构建和发布
```

## 常见问题

### Q: 如何添加新的依赖？

A: 更新`requirements.txt`并在`buildozer.spec`中添加：

```ini
requirements = python3,kivy,new_package
```

### Q: 如何测试没有Android设备的代码？

A: 在Linux/Windows上运行Kivy应用进行功能测试，只有Android特定代码需要实际设备。

### Q: 如何处理兼容性问题？

A: 
- 为Android特定代码添加try/except
- 检查API级别
- 使用功能检测而不是版本检测

### Q: buildozer缓存如何清除？

A:
```bash
rm -rf .buildozer bin/
buildozer android debug  # 重新构建
```

## 许可证

本项目采用MIT许可证。所有贡献必须同意此许可证。

---

感谢您的贡献！🎉
