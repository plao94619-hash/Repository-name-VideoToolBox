# 万能音视频工具箱

一款面向 Windows 10/11 的本地音视频转换工具。图形界面使用 Qt for Python，转换核心使用 FFmpeg。

## 功能

- 视频格式转换：MP4、MKV、MOV、WebM、AVI
- 音频格式转换：MP3、M4A、AAC、FLAC、WAV、OGG、OPUS
- 视频提取音频：支持“原始音轨（无损提取）”，直接复制音频码流，不重新编码
- 视频压缩：画质优先、均衡压缩、极限压缩
- 编码器：H.264、H.265/HEVC、AV1
- 硬件加速：自动检测 NVIDIA NVENC、Intel QSV、AMD AMF；编码中途失败时自动用 CPU 重试一次
- 分辨率限制：保持原尺寸，或限制到 4K、1080p、720p、480p
- 批量处理、拖放添加、实时进度、安全取消、自动避免覆盖同名文件
- 使用临时输出文件，只有转换成功后才生成最终文件；失败和取消时清理临时文件
- 跳过媒体中的封面图片，选择真正的视频流进行转换
- 软件界面支持简体中文、繁体中文和英语，即时切换并记住上次选择
- Fluent 风格的响应式工作台、现代化明暗主题（可跟随系统）与窗口位置记忆
- 支持选择本地图片作为自定义背景，可随时更换或恢复默认背景
- 空列表拖放引导、统一线性图标、语义状态徽章与更清晰的任务层级
- 在完成行双击或右键复制输出路径；失败行可查看完整错误详情
- 安装向导支持英语、简体中文和繁体中文，按照 Windows 界面语言自动匹配
- 全程本地处理，不上传用户媒体文件

## 下载 Windows 安装包

打开仓库的 [Releases 页面](https://github.com/plao94619-hash/Repository-name-VideoToolBox/releases/latest)，下载最新正式版：

- Universal-Media-Toolbox-Setup-1.5.0.exe：安装版
- Universal-Media-Toolbox-Portable-1.5.0.zip：免安装便携版
- SHA256SUMS.txt：校验值

每次成功构建后也可在 Actions 下载近期构建产物。新版安装版可直接安装到旧版的位置，原有设置会保留。

> 本项目暂未购买代码签名证书。Windows SmartScreen 可能显示“未知发布者”，这是未签名个人软件的常见提示，并不等于检测到病毒。建议从本仓库下载并核对 SHA-256。

## 使用方法

1. 点击“添加文件”或直接把文件拖入窗口。
2. 选择任务类型、输出格式和质量方案。
3. 选择输出目录。
4. 点击“开始处理”。

首次启动会按 Windows 界面语言选择最接近的界面语言。窗口右上角的语言下拉菜单可在简体中文、繁体中文和英语之间切换。切换不会改变正在选择的任务类型、格式或输出目录；之前版本保存的设置仍然可用。转换期间语言菜单暂时锁定，任务完成后即可切换。

外观菜单可选择跟随系统、浅色或深色；窗口会记住上次的大小与位置。宽窗口使用“文件队列＋处理设置”双栏工作台，较窄窗口会自动回流为单栏，底部开始与取消按钮始终可见。任务完成后，双击输出文件列或右键选择“复制输出路径”；失败行可双击状态或右键选择“查看错误详情”。

“背景”菜单可选择 PNG、JPG、JPEG、WebP 或 BMP 图片作为软件背景。图片仅从本机读取，按窗口比例居中裁切，并自动叠加明暗遮罩以保持文字清晰；可从同一菜单随时更换图片或恢复默认背景。软件会记住图片路径，如果原图片被移动或删除，下次启动会安全恢复默认背景。

### 质量方案

| 方案 | 适用场景 | 特点 |
|---|---|---|
| 画质优先 | 收藏、剪辑前处理 | 接近视觉无损，文件相对较大 |
| 均衡压缩 | 日常分享与存储 | 兼顾画质、体积和速度 |
| 极限压缩 | 空间非常有限 | 优先 AV1/HEVC，体积更小但耗时明显增加 |

“无损提取”指复制视频文件中原有的音频码流，输出音质与源音轨一致。把有损音频转换成 FLAC/WAV 不会恢复已经丢失的细节。

## 本地开发

要求 Python 3.12 和系统可用的 FFmpeg/FFprobe：

~~~powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-build.txt
python src\main.py
~~~

运行测试：

~~~powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
~~~

构建 Windows 版本：

~~~powershell
python scripts\make_icon.py
pyinstaller build.spec --noconfirm --clean
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\videotoolbox.iss
~~~

GitHub Actions 会自动下载 FFmpeg Windows GPL 静态构建、运行单元测试与真实音频转换测试、打包程序、自检内置 FFmpeg，并生成安装包和便携包。

## 技术与许可

- 应用源码：MIT License
- FFmpeg：安装包内附 GNU GPL v3 文本；来源及源代码地址见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Qt for Python / PySide6：LGPLv3/GPLv3 或商业许可

界面翻译集中存放于 [src/i18n.py](src/i18n.py)，新增或更新界面提示时请同时更新英文和繁体中文翻译；自动测试会检查翻译表的键及模板占位符是否一致。安装向导的简繁体译文来自 Inno Setup 官方源码。

FFmpeg、Qt 及各编解码器商标属于各自权利人。
