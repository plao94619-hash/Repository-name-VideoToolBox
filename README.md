# 万能音视频工具箱

一款面向 Windows 10/11 的本地音视频转换工具。图形界面使用 Qt for Python，转换核心使用 FFmpeg。

## 功能

- 视频格式转换：MP4、MKV、MOV、WebM、AVI
- 音频格式转换：MP3、M4A、AAC、FLAC、WAV、OGG、OPUS
- 视频提取音频：支持“原始音轨（无损提取）”，直接复制音频码流，不重新编码
- 视频压缩：画质优先、均衡压缩、极限压缩
- 编码器：H.264、H.265/HEVC、AV1
- 硬件加速：自动检测 NVIDIA NVENC、Intel QSV、AMD AMF；不可用时回退 CPU
- 分辨率限制：保持原尺寸，或限制到 4K、1080p、720p、480p
- 批量处理、拖放添加、实时进度、安全取消、自动避免覆盖同名文件
- 全程本地处理，不上传用户媒体文件

## 下载 Windows 安装包

打开仓库的 **Actions** 页面，进入最新成功的 **Build Windows Installer**，下载构建产物：

- Universal-Media-Toolbox-Setup-1.0.0.exe：安装版
- Universal-Media-Toolbox-Portable-1.0.0.zip：免安装便携版
- SHA256SUMS.txt：校验值

正式版本也会发布在 Releases 页面。

> 本项目暂未购买代码签名证书。Windows SmartScreen 可能显示“未知发布者”，这是未签名个人软件的常见提示，并不等于检测到病毒。建议从本仓库下载并核对 SHA-256。

## 使用方法

1. 点击“添加文件”或直接把文件拖入窗口。
2. 选择任务类型、输出格式和质量方案。
3. 选择输出目录。
4. 点击“开始处理”。

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

GitHub Actions 会自动下载 FFmpeg Windows GPL 静态构建、运行测试、打包程序、自检内置 FFmpeg，并生成安装包和便携包。

## 技术与许可

- 应用源码：MIT License
- FFmpeg：安装包内附 GNU GPL v3 文本；来源及源代码地址见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Qt for Python / PySide6：LGPLv3/GPLv3 或商业许可

FFmpeg、Qt 及各编解码器商标属于各自权利人。
