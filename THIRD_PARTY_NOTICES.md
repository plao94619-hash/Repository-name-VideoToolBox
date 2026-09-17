# Third-party notices

“万能音视频工具箱”在本机调用 FFmpeg 和 FFprobe 独立程序完成媒体处理。

## FFmpeg

- Project: https://ffmpeg.org/
- Windows builds: https://github.com/BtbN/FFmpeg-Builds
- Source code: https://github.com/FFmpeg/FFmpeg
- License: the bundled GPL build is distributed under GNU GPL v3 or later.

Windows 安装包内附相应的 GNU GPL v3 许可文本。软件菜单“帮助 → 第三方许可”可以打开本文件。

## Qt for Python / PySide6

- Project: https://doc.qt.io/qtforpython-6/
- License: LGPLv3/GPLv3 or commercial.
- This application uses the LGPLv3 option and does not modify Qt.

## Unlock Music CLI

- Project: https://git.unlock-music.dev/um/cli
- Web project referenced by the feature request: https://git.unlock-music.dev/um/web
- Package documentation: https://pkg.go.dev/unlock-music.dev/cli
- Bundled version: v0.2.12
- License: MIT License

Windows 构建使用 Go 1.23.3 从固定版本 `unlock-music.dev/cli/cmd/um@v0.2.12` 构建独立的 `um.exe`。应用仅以离线参数调用它来处理用户选择的本地文件，不启用联网元数据更新，也不会删除源文件。安装包内附 `licenses/Unlock-Music-MIT.txt`。

## Other components

Python, PyInstaller, Inno Setup, Pillow 及其依赖项保留各自的许可证和版权声明。

安装向导的简体中文语言文件保留了原文件的贡献者标注，来源：
https://github.com/jrsoftware/issrc/blob/main/Files/Languages/ChineseSimplified.isl

安装向导的繁体中文语言文件同样保留贡献者标注，来源：
https://github.com/jrsoftware/issrc/blob/main/Files/Languages/ChineseTraditional.isl
