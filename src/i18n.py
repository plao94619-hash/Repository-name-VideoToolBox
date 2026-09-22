"""Presentation translations. Engine option identifiers remain unchanged."""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("zh_CN", "zh_TW", "en_US")
LANGUAGE_LABELS = {
    "zh_CN": "简体中文",
    "zh_TW": "繁體中文",
    "en_US": "English",
}

EN_US = {
    "万能音视频工具箱": "Universal Media Toolbox",
    "视频格式转换": "Convert video",
    "音频格式转换": "Convert audio",
    "视频提取音频": "Extract audio from video",
    "视频压缩": "Compress video",
    "音乐文件解锁": "Unlock local music files",
    "自动识别原始音频格式": "Detect original audio format",
    "原始音轨（无损提取）": "Original audio track (lossless copy)",
    "画质优先": "Best quality",
    "均衡压缩": "Balanced compression",
    "极限压缩": "Maximum compression",
    "保持原分辨率": "Keep original resolution",
    "最高 4K": "Up to 4K",
    "最高 1080p": "Up to 1080p",
    "最高 720p": "Up to 720p",
    "最高 480p": "Up to 480p",
    "自动选择": "Auto-select",
    "H.264（兼容优先）": "H.264 (best compatibility)",
    "H.265 / HEVC（高压缩）": "H.265 / HEVC (smaller files)",
    "AV1（压缩率最高，速度慢）": "AV1 (smallest files, slower)",
    "就绪：可直接拖入音频或视频文件": "Ready: drag audio or video files here",
    "就绪：可拖入待解锁的本地音乐文件":
        "Ready: drop local music files to unlock",
    "添加文件": "Add files",
    "添加文件夹": "Add folder",
    "退出": "Exit",
    "第三方许可": "Third-party licenses",
    "关于": "About",
    "文件": "File",
    "帮助": "Help",
    "格式转换 · 无损提取音轨 · 画质优先压缩 · 极限压缩":
        "Format conversion · Lossless audio extraction · Video compression",
    "格式转换 · 音乐解锁 · 无损提取 · 智能压缩":
        "Convert · Unlock music · Extract losslessly · Compress",
    "本地处理 · 文件不会上传": "Local processing · Files never leave your PC",
    "把媒体文件拖到这里": "Drop media files here",
    "支持常见音频和视频格式，也可以直接拖入整个文件夹":
        "Supports common audio and video formats. You can also drop a whole folder.",
    "选择文件": "Choose files",
    "＋ 添加文件": "＋ Add files",
    "移除选中": "Remove selected",
    "清空列表": "Clear list",
    "{count} 个文件": "{count} file(s)",
    "文件名": "File name",
    "类型": "Type",
    "大小": "Size",
    "状态 / 进度": "Status / progress",
    "输出文件": "Output file",
    "任务类型": "Task",
    "输出格式": "Output format",
    "质量方案": "Quality preset",
    "视频编码": "Video codec",
    "分辨率限制": "Resolution limit",
    "输出文件夹": "Output folder",
    "选择输出目录": "Choose an output folder",
    "浏览…": "Browse…",
    "打开目录": "Open folder",
    "等待任务": "Idle",
    "取消任务": "Cancel task",
    "开始处理": "Start",
    "语言": "Language",
    "外观": "Appearance",
    "跟随系统": "System",
    "浅色": "Light",
    "深色": "Dark",
    "背景": "Background",
    "默认背景": "Default",
    "自定义图片": "Custom image",
    "选择背景图片…": "Choose background image…",
    "移除自定义背景": "Remove custom background",
    "选择背景图片": "Choose a background image",
    "图片文件": "Image files",
    "无法使用背景图片": "Background image unavailable",
    "所选文件不是可读取的图片。": "The selected file is not a readable image.",
    "自定义背景已启用": "Custom background enabled",
    "已恢复默认背景": "Default background restored",
    "待处理文件": "Files to process",
    "将文件或文件夹拖入此处，或使用下方按钮添加":
        "Drop files or folders here, or add them with the buttons below.",
    "处理设置": "Processing settings",
    "按任务需要选择输出格式与质量": "Choose the format and quality for this task.",
    "复制输出路径": "Copy output path",
    "已复制输出路径": "Output path copied",
    "查看错误详情": "View error details",
    "错误详情": "Error details",
    "此文件未能完成处理。": "This file could not be processed.",
    "选择音频或视频文件": "Choose audio or video files",
    "选择待解锁音乐文件": "Choose music files to unlock",
    "受支持的音乐文件": "Supported music files",
    "媒体文件": "Media files",
    "所有文件": "All files",
    "选择媒体文件夹": "Choose a media folder",
    "选择待解锁音乐文件夹": "Choose a music folder to unlock",
    "未知": "Unknown",
    "等待处理": "Pending",
    "已添加 {count} 个文件": "Added {count} file(s)",
    "离线解锁本地音乐，并保留原始文件":
        "Unlock local music offline while keeping the source files.",
    "把待解锁音乐拖到这里": "Drop music files to unlock here",
    "支持网易云、QQ 音乐、酷狗、酷我等本地文件，可批量添加文件夹":
        "Supports local files from NetEase, QQ Music, Kugou, Kuwo and more. Folders can be added in batches.",
    "选择音乐文件": "Choose music files",
    "开始解锁": "Start unlocking",
    "仅处理你合法拥有或获授权的本地文件；源文件不会删除。\n应用不会联网下载音乐或访问账号。":
        "Only process local files you own or are authorized to use; source files are kept.\nThe app never downloads music or accesses accounts.",
    "直接复制原音轨，不重新编码；质量选项不影响无损提取。":
        "Copies the original audio stream without re-encoding. Quality presets do not apply.",
    "FLAC/WAV 输出为无损格式，但有损源文件已丢失的音质无法恢复。":
        "FLAC/WAV are lossless output formats, but cannot restore detail lost in a lossy source.",
    "接近视觉无损，输出文件通常较大。":
        "Near visually lossless; output files are usually larger.",
    "兼顾画质、速度和文件大小，推荐日常使用。":
        "Balances quality, speed and size. Recommended for everyday use.",
    "优先减小体积，可能非常耗时并损失部分细节。":
        "Prioritizes smaller files; can be slow and lose some detail.",
    "选择输出文件夹": "Choose an output folder",
    "无法打开目录": "Cannot open folder",
    "尚未添加文件": "No files added",
    "请先添加需要处理的音频或视频文件。":
        "Add an audio or video file before starting.",
    "请先添加需要处理的文件。": "Add files before starting.",
    "文件与任务类型不匹配": "Files do not match the task",
    "当前任务不支持列表中的 {count} 个文件。请移除这些文件，或切换任务类型。":
        "This task does not support {count} file(s) in the list. Remove them or switch tasks.",
    "请选择输出目录": "Choose an output folder",
    "请先指定转换后的文件保存位置。":
        "Choose where the output files will be saved.",
    "无法创建输出目录": "Cannot create output folder",
    "正在处理…": "Processing…",
    "正在解锁…": "Unlocking…",
    "正在准备…": "Preparing…",
    "正在处理第 {current}/{total} 个文件":
        "Processing file {current} of {total}",
    "失败：{message}": "Failed: {message}",
    "任务已取消；成功 {successes} 个，失败 {failures} 个。":
        "Cancelled: {successes} succeeded, {failures} failed.",
    "任务已取消": "Cancelled",
    "已取消": "Cancelled",
    "全部完成：成功 {successes} 个，失败 {failures} 个。":
        "Finished: {successes} succeeded, {failures} failed.",
    "处理完成": "Task finished",
    "可将鼠标停在失败状态上查看 FFmpeg 错误。":
        "Hover over a failed status to see the FFmpeg error.",
    "可将鼠标停在失败状态上查看详细错误。":
        "Hover over a failed status to view the full error.",
    "是否打开输出文件夹？": "Open the output folder?",
    "打开": "Open",
    "关闭": "Close",
    "正在安全停止任务…": "Stopping safely…",
    "完整声明见项目 THIRD_PARTY_NOTICES.md。":
        "Full details are in THIRD_PARTY_NOTICES.md.",
    "版本 {version}": "Version {version}",
    "基于 FFmpeg 与 Qt for Python 构建的本地音视频转换工具。":
        "Local media conversion tool built with FFmpeg and Qt for Python.",
    "转换全程在本机完成，不上传用户文件。":
        "All processing stays on your computer; your files are not uploaded.",
    "音乐解锁功能由 Unlock Music CLI 提供，仅供处理合法拥有或获授权的本地文件。":
        "Music unlocking is provided by Unlock Music CLI and is only for local files you own or are authorized to use.",
    "项目主页": "Project home",
    "任务仍在运行": "Task still running",
    "需要先停止当前转换。是否取消任务？":
        "The current conversion must stop before closing. Cancel it?",
    "是": "Yes",
    "否": "No",
    "确定": "OK",
    "已完成": "Completed",
    "已完成，体积减少 {percent:.1f}%": "Completed: file size reduced by {percent:.1f}%",
    "已完成，输出为原文件的 {percent:.1f}%":
        "Completed: output is {percent:.1f}% of the source size",
    "没有找到 {executable}。请重新安装软件或检查程序文件是否完整。":
        "{executable} was not found. Reinstall the app or check its files.",
    "外部程序执行失败": "External program failed",
    "无法读取媒体信息：{name}": "Cannot read media information: {name}",
    "不支持的音频输出格式：{target}": "Unsupported audio output format: {target}",
    "不支持的输出格式：{target}": "Unsupported output format: {target}",
    "该文件没有可提取的音轨。": "This file has no audio track to extract.",
    "该文件没有可转换的音轨。": "This file has no audio track to convert.",
    "该文件没有视频画面。": "This file has no video stream.",
    "未知任务类型：{mode}": "Unknown task type: {mode}",
    "无法启动 FFmpeg：{error}": "Cannot start FFmpeg: {error}",
    "正在处理 {percent}%": "Processing {percent}%",
    "处理速度 {speed}": "Speed: {speed}",
    "FFmpeg 返回错误代码 {code}": "FFmpeg exited with error code {code}",
    "输入文件不存在。": "The input file does not exist.",
    "硬件编码失败，已切换 CPU 重试":
        "Hardware encoding failed; retrying on the CPU",
    "转换结束，但没有生成有效的输出文件。":
        "Conversion finished without a valid output file.",
    "无法保存输出文件：{error}": "Cannot save output file: {error}",
    "FFmpeg 或 FFprobe 版本信息异常":
        "FFmpeg or FFprobe returned invalid version information",
    "解锁完成": "Unlocked",
    "不支持的音乐文件格式：{extension}":
        "Unsupported protected music format: {extension}",
    "无法识别此音乐文件，文件可能不受支持或已经是普通音频。":
        "This music file could not be recognized. It may be unsupported or already be a normal audio file.",
    "输出文件已存在。": "The output file already exists.",
    "音乐解锁组件未返回可用的错误信息。":
        "The music unlock helper did not return a useful error.",
    "音乐解锁失败：{message}": "Music unlock failed: {message}",
    "无法启动音乐解锁组件：{error}":
        "Cannot start the music unlock helper: {error}",
    "正在解锁 {percent}%": "Unlocking {percent}%",
    "解锁结束，但没有生成有效的音频文件。":
        "Unlocking finished without a valid audio file.",
    "音乐解锁组件版本信息异常":
        "The music unlock helper returned invalid version information",
    "音乐解锁组件格式列表异常":
        "The music unlock helper returned an invalid format list",
    "授权音频下载": "Authorized audio",
    "保留原始音频格式": "Keep original audio format",
    "就绪：可粘贴公开的无 DRM 音频直链":
        "Ready: paste a public DRM-free audio file URL",
    "{count} 个链接": "{count} link(s)",
    "格式转换 · 音乐解锁 · 授权下载 · 无损提取":
        "Convert · Unlock music · Authorized download · Lossless extraction",
    "添加链接": "Add links",
    "每行粘贴一个公开音频直链，例如 https://example.com/song.mp3":
        "Paste one public audio file URL per line, e.g. https://example.com/song.mp3",
    "尚未添加链接": "No links added",
    "请粘贴公开、无 DRM 的音频文件直链。":
        "Paste a public, DRM-free audio file URL.",
    "下载时获取": "Read while downloading",
    "已添加 {count} 个链接": "Added {count} link(s)",
    "另有 {count} 个链接未显示。": "{count} more link(s) are not shown.",
    "部分链接无法添加": "Some links could not be added",
    "无法添加链接": "Cannot add link",
    "有 {count} 个链接不符合直接音频下载规则。":
        "{count} link(s) do not meet the direct-audio download rules.",
    "请先添加需要下载的音频直链。":
        "Add an audio file URL before starting.",
    "待下载音频": "Audio to download",
    "粘贴公开音频文件直链；支持一次添加多行":
        "Paste public audio file URLs; multiple lines are supported.",
    "下载无 DRM 音频直链，并保留原始格式":
        "Download DRM-free direct audio while keeping its original format.",
    "在上方粘贴音频直链": "Paste an audio file URL above",
    "仅支持公开 HTTP/HTTPS 音频文件，不支持平台页面或流媒体清单":
        "Public HTTP/HTTPS audio files only; platform pages and streaming manifests are not supported.",
    "定位到链接输入框": "Focus link input",
    "开始下载": "Start download",
    "来源 / 文件名": "Source / file name",
    "仅下载你有权保存的公开无 DRM 音频直链；不支持 Spotify、Apple Music 页面、Cookie、M3U8/DASH 或加密媒体。":
        "Only download public DRM-free audio you are authorized to save. Spotify or Apple Music pages, cookies, M3U8/DASH, and encrypted media are not supported.",
    "正在下载…": "Downloading…",
    "正在处理第 {current}/{total} 项":
        "Processing item {current} of {total}",
    "授权下载仅连接链接所在服务器，不支持订阅平台页面、Cookie、流媒体清单或加密媒体。":
        "Authorized downloads connect only to the linked server; subscription-platform pages, cookies, streaming manifests, and encrypted media are not supported.",
    "需要先停止当前任务。是否取消任务？":
        "The current task must stop before closing. Cancel it?",
    "请输入有效的音频直链。": "Enter a valid direct audio URL.",
    "仅支持 HTTP 或 HTTPS 音频直链。":
        "Only HTTP or HTTPS audio file URLs are supported.",
    "下载地址不能包含账号或密码。":
        "The download URL cannot contain a username or password.",
    "不支持 Spotify 或 Apple Music 链接；请使用官方应用离线播放。":
        "Spotify and Apple Music links are not supported; use the official app for offline playback.",
    "不支持 M3U8、DASH 或其他流媒体播放清单。":
        "M3U8, DASH, and other streaming manifests are not supported.",
    "该链接不是受支持的音频文件直链。":
        "This URL is not a supported direct audio file.",
    "无效链接": "Invalid link",
    "服务器未提供可识别的音频文件格式。":
        "The server did not provide a recognizable audio format.",
    "服务器返回 HTTP {code}。": "The server returned HTTP {code}.",
    "无法连接到下载地址：{error}":
        "Could not connect to the download URL: {error}",
    "服务器返回的内容不是音频文件。":
        "The server response is not an audio file.",
    "正在下载 {percent}%": "Downloading {percent}%",
    "已下载 {size}": "Downloaded {size}",
    "下载结束，但没有生成有效的音频文件。":
        "The download finished without a valid audio file.",
    "检测到流媒体播放清单，已停止下载。":
        "A streaming manifest was detected; the download was stopped.",
    "检测到加密或受保护的媒体，已停止下载。":
        "Encrypted or protected media was detected; the download was stopped.",
    "下载完成": "Downloaded",
    "视频清晰度增强": "Enhance video clarity",
    "图片清晰度增强": "Enhance image clarity",
    "自然增强": "Natural enhancement",
    "标准增强": "Balanced enhancement",
    "强力增强": "Strong enhancement",
    "保持原尺寸（最高 4K）": "Keep original size (max 4K)",
    "提升至 1080p": "Upscale to 1080p",
    "提升至 2K": "Upscale to 2K",
    "提升至 4K": "Upscale to 4K",
    "PNG（无损）": "PNG (lossless)",
    "JPG（高质量）": "JPG (high quality)",
    "WebP（高质量）": "WebP (high quality)",
    "就绪：可拖入要增强的视频文件":
        "Ready: drop video files to enhance",
    "就绪：可拖入要增强的图片文件":
        "Ready: drop image files to enhance",
    "格式转换 · 4K 清晰度增强 · 音乐解锁 · 授权下载":
        "Convert · 4K clarity enhancement · Unlock music · Authorized download",
    "增强强度": "Enhancement strength",
    "输出分辨率": "Output resolution",
    "选择要增强的视频文件": "Choose videos to enhance",
    "选择要增强的图片文件": "Choose images to enhance",
    "视频文件": "Video files",
    "选择视频文件夹": "Choose a video folder",
    "选择图片文件夹": "Choose an image folder",
    "待增强视频": "Videos to enhance",
    "待增强图片": "Images to enhance",
    "拖入视频或文件夹，可批量增强":
        "Drop videos or folders for batch enhancement",
    "拖入图片或文件夹，可批量增强":
        "Drop images or folders for batch enhancement",
    "降噪、锐化并按原比例输出，最高支持 4K":
        "Denoise and sharpen at the original aspect ratio, up to 4K",
    "把要增强的视频拖到这里": "Drop videos to enhance here",
    "支持常见视频格式；输出为兼容性良好的 MP4":
        "Supports common video formats and outputs compatible MP4 files",
    "选择视频文件": "Choose video files",
    "把要增强的图片拖到这里": "Drop images to enhance here",
    "支持 JPG、PNG、WebP、BMP 与 TIFF":
        "Supports JPG, PNG, WebP, BMP, and TIFF",
    "选择图片文件": "Choose image files",
    "开始增强": "Start enhancement",
    "轻度降噪与锐化，适合本身质量较好的素材。":
        "Light denoising and sharpening for already clean sources.",
    "平衡降噪与细节增强，推荐用于大多数素材。":
        "Balanced denoising and detail enhancement for most sources.",
    "更强的降噪与边缘增强，适合模糊或噪点明显的素材。":
        "Stronger denoising and edge enhancement for blurry or noisy sources.",
    "增强可改善观感并放大至 4K，但无法凭空恢复源文件中不存在的真实细节。":
        "Enhancement can improve perceived clarity and upscale to 4K, but cannot recreate real detail absent from the source.",
    "正在增强…": "Enhancing…",
    "图片与视频清晰度增强支持按原比例输出，最高可达 4K。":
        "Image and video clarity enhancement preserves aspect ratio and supports output up to 4K.",
    "增强完成 · {width}×{height}":
        "Enhanced · {width}×{height}",
    "不支持的图片输出格式：{target}":
        "Unsupported image output format: {target}",
    "请选择受支持的视频文件。": "Choose a supported video file.",
    "请选择受支持的图片文件。": "Choose a supported image file.",
    "正在分析画面…": "Analyzing image…",
    "该文件没有可增强的画面。": "This file has no image to enhance.",
    "正在增强 {percent}%": "Enhancing {percent}%",
    "正在增强清晰度…": "Enhancing clarity…",
    "增强结束，但没有生成有效的输出文件。":
        "Enhancement finished without a valid output file.",
    "增强完成": "Enhancement complete",
    "图片水印区域修复": "Repair visible image watermark areas",
    "图片隐藏水印处理": "Process hidden image watermarks",
    "AI 图片水印修复": "Repair AI image watermarks",
    "就绪：添加 AI 图片并框选可见角标":
        "Ready: add AI images and select visible overlays",
    "同时处理像素隐藏标记（可选）":
        "Also process hidden pixel marks (optional)",
    "对图片像素进行标准强度低位处理；可能损失细节，也不保证去除 SynthID 或其他鲁棒指纹。":
        "Apply balanced low-bit pixel processing. Detail may be lost; SynthID and other robust marks may remain.",
    "拖入 AI 图片或文件夹，可批量套用框选区域":
        "Drop AI images or folders to apply selected areas in a batch",
    "框选可见角标；可选在一次导出中同时处理像素隐藏标记":
        "Select visible overlays; optionally process low-bit pixel marks in the same export",
    "把 AI 图片拖到这里": "Drop AI images here",
    "在预览图框选可见角标，由周围纹理修复；可选同时处理像素低位。无自动识别，也不保证清除 SynthID、C2PA 或其他鲁棒溯源标记。请保留原图并核验。":
        "Select visible overlays to repair them using nearby texture. Optional low-bit treatment is available. No automatic detection or guaranteed removal of SynthID, C2PA, or robust provenance. Keep the original and verify the output.",
    "框选 AI 图片可见角标": "Select visible AI image overlays",
    "框选 AI 图片上的可见标记": "Select visible marks on the AI image",
    "在预览图上框选可见角标或文字，可添加多个区域；尽量贴合边缘。":
        "Drag over visible badges or text in the preview. Add multiple areas and select close to their edges.",
    "仅用于有权编辑的图片。批量图片共用相对位置；可在主界面选用像素低位处理，但不保证清除 SynthID 等鲁棒标记。保留原图并核验。":
        "Only edit images you are authorized to change. Batch images share relative positions. Optional low-bit treatment cannot guarantee removal of SynthID or other robust marks. Keep the original and verify.",
    "请先框选可见角标或勾选隐藏像素处理。":
        "Select visible overlays or enable hidden pixel processing first.",
    "不支持的修复边缘强度：{strength}":
        "Unsupported repair coverage: {strength}",
    "正在处理 AI 图片水印…": "Processing AI image watermarks…",
    "AI 图片水印处理完成": "AI image watermark processing complete",
    "AI 图片处理完成 · {width}×{height} · 请核验结果":
        "AI image processed · {width}×{height} · verify the output",
    "轻度处理": "Gentle processing",
    "标准处理": "Balanced processing",
    "强力处理": "Strong processing",
    "处理强度": "Processing strength",
    "就绪：添加图片并选择隐藏水印处理强度":
        "Ready: add images and choose a hidden watermark strength",
    "同时清理 EXIF/XMP 元数据": "Also clean EXIF/XMP metadata",
    "可选：不复制常见嵌入元数据。可能影响色彩信息和内容凭证；不保证清除全部隐藏标记。":
        "Optional: omit common embedded metadata. This may affect color information and Content Credentials; some hidden marks may remain.",
    "待处理图片": "Images to process",
    "拖入图片或文件夹，可批量处理隐藏水印":
        "Drop images or folders to process hidden watermarks in a batch",
    "处理像素低位，按强度轻度平滑；支持可选元数据清理":
        "Normalize low pixel bits, optionally smooth, and optionally clean metadata",
    "把要处理的图片拖到这里": "Drop images to process here",
    "固定 RGB 最低 1 位，主要针对简单的像素低位标记。":
        "Fix the lowest RGB bit; mainly for simple low-bit pixel marks.",
    "轻度平滑并固定 RGB 最低 2 位，推荐先试用。":
        "Gently smooth and fix the lowest 2 RGB bits. Try this first.",
    "更强平滑并固定 RGB 最低 3 位，可能损失细节。":
        "Smooth more and fix the lowest 3 RGB bits; may reduce detail.",
    "仅尽力削弱部分像素隐藏标记；无法保证去除未知指纹或 C2PA 溯源。PNG 最适合低位处理；请保留原图并自行核验。":
        "Best effort for some pixel marks; unknown fingerprints and C2PA provenance may remain. Use PNG for predictable low-bit results. Keep the original and verify the output.",
    "不支持的隐藏水印处理强度：{strength}":
        "Unsupported hidden watermark strength: {strength}",
    "该文件没有可处理的画面。": "This file has no image to process.",
    "正在处理隐藏水印…": "Processing hidden watermark…",
    "处理结束，但没有生成有效的输出文件。":
        "Processing finished without a valid output file.",
    "隐藏水印处理完成": "Hidden watermark processing complete",
    "隐藏水印处理完成 · {width}×{height} · 请自行核验":
        "Processed · {width}×{height} · verify the output",
    "精细修复": "Precise edges",
    "标准修复": "Balanced edges",
    "扩展修复": "Expanded edges",
    "就绪：添加图片并框选可见水印区域":
        "Ready: add an image and select visible watermark areas",
    "框选修复区域": "Select repair areas",
    "修复边缘": "Repair coverage",
    "待修复图片": "Images to repair",
    "拖入图片或文件夹，可批量套用所选区域":
        "Drop images or folders to apply the selected areas in a batch",
    "框选一处或多处可见水印，由本地 FFmpeg 修复周围纹理":
        "Select one or more visible watermark areas for local FFmpeg texture repair",
    "把要修复的图片拖到这里": "Drop images to repair here",
    "支持 JPG、PNG、WebP、BMP 与 TIFF；原图不会改动":
        "Supports JPG, PNG, WebP, BMP, and TIFF; source images are never changed",
    "开始修复": "Start repair",
    "严格使用框选范围，适合边界清楚且选择准确的水印。":
        "Uses the exact selection for sharply bounded, accurately selected watermarks.",
    "轻微扩展选区边缘，兼顾抗锯齿与自然过渡，推荐使用。":
        "Slightly expands the selection to cover antialiasing and blend naturally. Recommended.",
    "进一步覆盖水印阴影和描边，可能影响更多周围纹理。":
        "Covers more watermark shadow and outline, but may affect more nearby texture.",
    "仅针对手动框选的可见区域修复画面；不提供隐藏标记的检测或定向清除。导出重新编码可能使 C2PA 等内容凭证失效，请保留原图。":
        "Image repair targets manually selected visible areas. Hidden marks are not detected or selectively removed. Re-encoding may invalidate C2PA credentials; keep the original.",
    "尚未选择修复区域": "No repair areas selected",
    "已选择 {count} 个区域": "{count} area(s) selected",
    "尚未添加图片": "No images added",
    "请先添加需要修复的图片。": "Add an image to repair first.",
    "选择要修复的图片文件": "Choose images to repair",
    "框选可见水印区域": "Select visible watermark areas",
    "框选需要修复的可见水印": "Select visible watermarks to repair",
    "在预览图上拖动鼠标框选水印，可添加多个区域；框选时尽量贴合水印边缘。":
        "Drag over watermarks in the preview. You can add multiple areas; keep each selection close to its edges.",
    "撤销上一步": "Undo",
    "清空区域": "Clear areas",
    "取消": "Cancel",
    "保存区域": "Save areas",
    "仅用于你拥有或获授权编辑的图片。队列中的图片将使用相同的相对位置。此功能不检测或定向清除隐藏标记；导出重新编码可能改变元数据或使 C2PA 等内容凭证失效，请保留原图。":
        "Use only on images you own or are authorized to edit. Queued images use the same relative areas. Hidden marks are not detected or selectively removed. Re-encoding may change metadata or invalidate C2PA credentials; keep the original.",
    "无法读取图片": "Cannot read image",
    "已保存 {count} 个修复区域": "Saved {count} repair area(s)",
    "请先在图片预览中框选至少一个可见水印区域。":
        "Select at least one visible watermark area in the image preview first.",
    "正在修复…": "Repairing…",
    "正在修复选中区域…": "Repairing selected areas…",
    "该文件没有可修复的画面。": "This file has no image to repair.",
    "修复结束，但没有生成有效的输出文件。":
        "Repair finished without a valid output file.",
    "水印区域修复完成": "Watermark-area repair complete",
    "修复完成 · {count} 个区域 · {width}×{height}":
        "Repaired · {count} area(s) · {width}×{height}",
    "可见水印区域修复适用于有权编辑的图片；重新编码可能改变元数据或使内容凭证失效。":
        "Visible watermark-area repair is for images you are authorized to edit. Re-encoding may change metadata or invalidate Content Credentials.",
    "功能导航": "Workspaces",
    "功能": "Tools",
    "视频工具": "Video",
    "音频工具": "Audio",
    "图片工具": "Images",
    "视频转换": "Convert video",
    "视频增强": "Enhance video",
    "提取音频": "Extract audio",
    "音频转换": "Convert audio",
    "本地音乐解锁": "Unlock music",
    "图片增强": "Enhance images",
    "可见水印修复": "Visible marks",
    "隐藏水印处理": "Hidden marks",
    "AI 水印修复": "AI watermark",
    "切换功能会保留文件队列；开始前请确认文件类型适用于当前任务。":
        "Files stay in the queue when you switch tools. Check file types before starting.",
    "转换视频格式，按需要选择编码、画质与分辨率。":
        "Convert video formats with your choice of codec, quality and resolution.",
    "为视频降噪与锐化，按原比例提升至最高 4K。":
        "Reduce noise and sharpen video, scaling proportionally up to 4K.",
    "按画质目标压缩视频，兼顾体积与兼容性。":
        "Compress video for your quality target, size and compatibility.",
    "从视频导出音频，也可直接复制原始音轨。":
        "Export audio from video or copy the original track without re-encoding.",
    "转换常用音频格式，选择适合的质量方案。":
        "Convert common audio formats with a suitable quality preset.",
    "批量处理你有权使用的本地音乐文件。":
        "Batch process local music files you are authorized to use.",
    "粘贴公开音频文件直链，批量保存至本机。":
        "Paste direct links to public audio files and save them locally.",
    "改善图片观感，按比例放大至最高 4K。":
        "Improve image appearance and scale proportionally up to 4K.",
    "框选可见标记，由周围画面修复所选区域。":
        "Select visible marks and repair the area using nearby pixels.",
    "处理简单像素隐藏标记，可选清理常见元数据。":
        "Process simple hidden pixel marks and optionally clear common metadata.",
    "框选可见角标，可选处理简单像素低位标记。":
        "Select visible corner marks and optionally process simple low-bit pixel marks.",
}

ZH_TW = {
    "万能音视频工具箱": "萬能影音工具箱",
    "视频格式转换": "影片格式轉換",
    "音频格式转换": "音訊格式轉換",
    "视频提取音频": "從影片擷取音訊",
    "视频压缩": "影片壓縮",
    "音乐文件解锁": "解鎖本機音樂檔案",
    "自动识别原始音频格式": "自動辨識原始音訊格式",
    "原始音轨（无损提取）": "原始音軌（無損擷取）",
    "画质优先": "畫質優先",
    "均衡压缩": "均衡壓縮",
    "极限压缩": "極限壓縮",
    "保持原分辨率": "維持原解析度",
    "最高 4K": "最高 4K",
    "最高 1080p": "最高 1080p",
    "最高 720p": "最高 720p",
    "最高 480p": "最高 480p",
    "自动选择": "自動選擇",
    "H.264（兼容优先）": "H.264（相容性優先）",
    "H.265 / HEVC（高压缩）": "H.265 / HEVC（高壓縮）",
    "AV1（压缩率最高，速度慢）": "AV1（壓縮率最高，速度較慢）",
    "就绪：可直接拖入音频或视频文件": "就緒：可直接拖入音訊或影片檔案",
    "就绪：可拖入待解锁的本地音乐文件":
        "就緒：可拖入待解鎖的本機音樂檔案",
    "添加文件": "加入檔案",
    "添加文件夹": "加入資料夾",
    "退出": "結束",
    "第三方许可": "第三方授權",
    "关于": "關於",
    "文件": "檔案",
    "帮助": "說明",
    "格式转换 · 无损提取音轨 · 画质优先压缩 · 极限压缩":
        "格式轉換 · 無損擷取音軌 · 畫質優先壓縮 · 極限壓縮",
    "格式转换 · 音乐解锁 · 无损提取 · 智能压缩":
        "格式轉換 · 音樂解鎖 · 無損擷取 · 智慧壓縮",
    "本地处理 · 文件不会上传": "本機處理 · 檔案不會上傳",
    "把媒体文件拖到这里": "將媒體檔案拖到這裡",
    "支持常见音频和视频格式，也可以直接拖入整个文件夹":
        "支援常見音訊與影片格式，也可以直接拖入整個資料夾。",
    "选择文件": "選擇檔案",
    "＋ 添加文件": "＋ 加入檔案",
    "移除选中": "移除所選",
    "清空列表": "清空清單",
    "{count} 个文件": "{count} 個檔案",
    "文件名": "檔案名稱",
    "类型": "類型",
    "大小": "大小",
    "状态 / 进度": "狀態／進度",
    "输出文件": "輸出檔案",
    "任务类型": "工作類型",
    "输出格式": "輸出格式",
    "质量方案": "畫質方案",
    "视频编码": "影片編碼",
    "分辨率限制": "解析度限制",
    "输出文件夹": "輸出資料夾",
    "选择输出目录": "選擇輸出資料夾",
    "浏览…": "瀏覽…",
    "打开目录": "開啟資料夾",
    "等待任务": "等待工作",
    "取消任务": "取消工作",
    "开始处理": "開始處理",
    "语言": "語言",
    "外观": "外觀",
    "跟随系统": "跟隨系統",
    "浅色": "淺色",
    "深色": "深色",
    "背景": "背景",
    "默认背景": "預設背景",
    "自定义图片": "自訂圖片",
    "选择背景图片…": "選擇背景圖片…",
    "移除自定义背景": "移除自訂背景",
    "选择背景图片": "選擇背景圖片",
    "图片文件": "圖片檔案",
    "无法使用背景图片": "無法使用背景圖片",
    "所选文件不是可读取的图片。": "所選檔案不是可讀取的圖片。",
    "自定义背景已启用": "已啟用自訂背景",
    "已恢复默认背景": "已恢復預設背景",
    "待处理文件": "待處理檔案",
    "将文件或文件夹拖入此处，或使用下方按钮添加":
        "將檔案或資料夾拖入此處，或使用下方按鈕加入。",
    "处理设置": "處理設定",
    "按任务需要选择输出格式与质量": "依工作需求選擇輸出格式和畫質。",
    "复制输出路径": "複製輸出路徑",
    "已复制输出路径": "已複製輸出路徑",
    "查看错误详情": "檢視錯誤詳情",
    "错误详情": "錯誤詳情",
    "此文件未能完成处理。": "此檔案無法完成處理。",
    "选择音频或视频文件": "選擇音訊或影片檔案",
    "选择待解锁音乐文件": "選擇待解鎖音樂檔案",
    "受支持的音乐文件": "支援的音樂檔案",
    "媒体文件": "媒體檔案",
    "所有文件": "所有檔案",
    "选择媒体文件夹": "選擇媒體資料夾",
    "选择待解锁音乐文件夹": "選擇待解鎖音樂資料夾",
    "未知": "未知",
    "等待处理": "等待處理",
    "已添加 {count} 个文件": "已加入 {count} 個檔案",
    "离线解锁本地音乐，并保留原始文件":
        "離線解鎖本機音樂，並保留原始檔案。",
    "把待解锁音乐拖到这里": "將待解鎖音樂拖到這裡",
    "支持网易云、QQ 音乐、酷狗、酷我等本地文件，可批量添加文件夹":
        "支援網易雲、QQ 音樂、酷狗、酷我等本機檔案，可批次加入資料夾。",
    "选择音乐文件": "選擇音樂檔案",
    "开始解锁": "開始解鎖",
    "仅处理你合法拥有或获授权的本地文件；源文件不会删除。\n应用不会联网下载音乐或访问账号。":
        "僅處理您合法擁有或獲授權的本機檔案；不會刪除來源檔案。\n應用程式不會連網下載音樂或存取帳號。",
    "直接复制原音轨，不重新编码；质量选项不影响无损提取。":
        "直接複製原始音軌，不重新編碼；畫質選項不影響無損擷取。",
    "FLAC/WAV 输出为无损格式，但有损源文件已丢失的音质无法恢复。":
        "FLAC/WAV 輸出為無損格式，但無法恢復有損來源已失去的音質。",
    "接近视觉无损，输出文件通常较大。":
        "接近視覺無損，輸出檔案通常較大。",
    "兼顾画质、速度和文件大小，推荐日常使用。":
        "兼顧畫質、速度和檔案大小，適合日常使用。",
    "优先减小体积，可能非常耗时并损失部分细节。":
        "優先縮小檔案，可能相當耗時並損失部分細節。",
    "选择输出文件夹": "選擇輸出資料夾",
    "无法打开目录": "無法開啟資料夾",
    "尚未添加文件": "尚未加入檔案",
    "请先添加需要处理的音频或视频文件。":
        "請先加入需要處理的音訊或影片檔案。",
    "请先添加需要处理的文件。": "請先加入需要處理的檔案。",
    "文件与任务类型不匹配": "檔案與工作類型不相符",
    "当前任务不支持列表中的 {count} 个文件。请移除这些文件，或切换任务类型。":
        "目前工作不支援清單中的 {count} 個檔案。請移除這些檔案，或切換工作類型。",
    "请选择输出目录": "請選擇輸出資料夾",
    "请先指定转换后的文件保存位置。":
        "請先指定轉換後檔案的儲存位置。",
    "无法创建输出目录": "無法建立輸出資料夾",
    "正在处理…": "正在處理…",
    "正在解锁…": "正在解鎖…",
    "正在准备…": "正在準備…",
    "正在处理第 {current}/{total} 个文件":
        "正在處理第 {current}/{total} 個檔案",
    "失败：{message}": "失敗：{message}",
    "任务已取消；成功 {successes} 个，失败 {failures} 个。":
        "工作已取消；成功 {successes} 個，失敗 {failures} 個。",
    "任务已取消": "工作已取消",
    "已取消": "已取消",
    "全部完成：成功 {successes} 个，失败 {failures} 个。":
        "全部完成：成功 {successes} 個，失敗 {failures} 個。",
    "处理完成": "處理完成",
    "可将鼠标停在失败状态上查看 FFmpeg 错误。":
        "將滑鼠停在失敗狀態上可查看 FFmpeg 錯誤。",
    "可将鼠标停在失败状态上查看详细错误。":
        "將滑鼠停在失敗狀態上可查看完整錯誤。",
    "是否打开输出文件夹？": "是否開啟輸出資料夾？",
    "打开": "開啟",
    "关闭": "關閉",
    "正在安全停止任务…": "正在安全停止工作…",
    "完整声明见项目 THIRD_PARTY_NOTICES.md。":
        "完整聲明請參閱專案 THIRD_PARTY_NOTICES.md。",
    "版本 {version}": "版本 {version}",
    "基于 FFmpeg 与 Qt for Python 构建的本地音视频转换工具。":
        "以 FFmpeg 和 Qt for Python 建構的本機影音轉換工具。",
    "转换全程在本机完成，不上传用户文件。":
        "所有轉換都在本機完成，不會上傳您的檔案。",
    "音乐解锁功能由 Unlock Music CLI 提供，仅供处理合法拥有或获授权的本地文件。":
        "音樂解鎖功能由 Unlock Music CLI 提供，僅供處理合法擁有或獲授權的本機檔案。",
    "项目主页": "專案首頁",
    "任务仍在运行": "工作仍在執行",
    "需要先停止当前转换。是否取消任务？":
        "關閉前必須停止目前的轉換。要取消工作嗎？",
    "是": "是",
    "否": "否",
    "确定": "確定",
    "已完成": "已完成",
    "已完成，体积减少 {percent:.1f}%": "已完成，檔案縮小 {percent:.1f}%",
    "已完成，输出为原文件的 {percent:.1f}%":
        "已完成，輸出大小為原檔案的 {percent:.1f}%",
    "没有找到 {executable}。请重新安装软件或检查程序文件是否完整。":
        "找不到 {executable}。請重新安裝軟體或檢查程式檔案。",
    "外部程序执行失败": "外部程式執行失敗",
    "无法读取媒体信息：{name}": "無法讀取媒體資訊：{name}",
    "不支持的音频输出格式：{target}": "不支援的音訊輸出格式：{target}",
    "不支持的输出格式：{target}": "不支援的輸出格式：{target}",
    "该文件没有可提取的音轨。": "這個檔案沒有可擷取的音軌。",
    "该文件没有可转换的音轨。": "這個檔案沒有可轉換的音軌。",
    "该文件没有视频画面。": "這個檔案沒有影片畫面。",
    "未知任务类型：{mode}": "未知工作類型：{mode}",
    "无法启动 FFmpeg：{error}": "無法啟動 FFmpeg：{error}",
    "正在处理 {percent}%": "正在處理 {percent}%",
    "处理速度 {speed}": "處理速度 {speed}",
    "FFmpeg 返回错误代码 {code}": "FFmpeg 傳回錯誤碼 {code}",
    "输入文件不存在。": "輸入檔案不存在。",
    "硬件编码失败，已切换 CPU 重试":
        "硬體編碼失敗，已切換至 CPU 重試",
    "转换结束，但没有生成有效的输出文件。":
        "轉換結束，但沒有產生有效的輸出檔案。",
    "无法保存输出文件：{error}": "無法儲存輸出檔案：{error}",
    "FFmpeg 或 FFprobe 版本信息异常": "FFmpeg 或 FFprobe 版本資訊異常",
    "解锁完成": "解鎖完成",
    "不支持的音乐文件格式：{extension}":
        "不支援的受保護音樂格式：{extension}",
    "无法识别此音乐文件，文件可能不受支持或已经是普通音频。":
        "無法辨識此音樂檔案；檔案可能不受支援，或已是一般音訊。",
    "输出文件已存在。": "輸出檔案已存在。",
    "音乐解锁组件未返回可用的错误信息。":
        "音樂解鎖元件未傳回可用的錯誤資訊。",
    "音乐解锁失败：{message}": "音樂解鎖失敗：{message}",
    "无法启动音乐解锁组件：{error}":
        "無法啟動音樂解鎖元件：{error}",
    "正在解锁 {percent}%": "正在解鎖 {percent}%",
    "解锁结束，但没有生成有效的音频文件。":
        "解鎖結束，但沒有產生有效的音訊檔案。",
    "音乐解锁组件版本信息异常":
        "音樂解鎖元件版本資訊異常",
    "音乐解锁组件格式列表异常":
        "音樂解鎖元件格式清單異常",
    "授权音频下载": "下載授權音訊",
    "保留原始音频格式": "保留原始音訊格式",
    "就绪：可粘贴公开的无 DRM 音频直链":
        "就緒：可貼上公開且無 DRM 的音訊檔案直鏈",
    "{count} 个链接": "{count} 個連結",
    "格式转换 · 音乐解锁 · 授权下载 · 无损提取":
        "格式轉換 · 音樂解鎖 · 授權下載 · 無損擷取",
    "添加链接": "加入連結",
    "每行粘贴一个公开音频直链，例如 https://example.com/song.mp3":
        "每行貼上一個公開音訊直鏈，例如 https://example.com/song.mp3",
    "尚未添加链接": "尚未加入連結",
    "请粘贴公开、无 DRM 的音频文件直链。":
        "請貼上公開且無 DRM 的音訊檔案直鏈。",
    "下载时获取": "下載時取得",
    "已添加 {count} 个链接": "已加入 {count} 個連結",
    "另有 {count} 个链接未显示。": "另有 {count} 個連結未顯示。",
    "部分链接无法添加": "部分連結無法加入",
    "无法添加链接": "無法加入連結",
    "有 {count} 个链接不符合直接音频下载规则。":
        "有 {count} 個連結不符合音訊直鏈下載規則。",
    "请先添加需要下载的音频直链。":
        "請先加入要下載的音訊直鏈。",
    "待下载音频": "待下載音訊",
    "粘贴公开音频文件直链；支持一次添加多行":
        "貼上公開音訊檔案直鏈；可一次加入多行。",
    "下载无 DRM 音频直链，并保留原始格式":
        "下載無 DRM 音訊直鏈，並保留原始格式。",
    "在上方粘贴音频直链": "在上方貼上音訊直鏈",
    "仅支持公开 HTTP/HTTPS 音频文件，不支持平台页面或流媒体清单":
        "僅支援公開 HTTP/HTTPS 音訊檔案，不支援平台頁面或串流播放清單。",
    "定位到链接输入框": "移至連結輸入框",
    "开始下载": "開始下載",
    "来源 / 文件名": "來源／檔案名稱",
    "仅下载你有权保存的公开无 DRM 音频直链；不支持 Spotify、Apple Music 页面、Cookie、M3U8/DASH 或加密媒体。":
        "僅下載您有權儲存的公開無 DRM 音訊直鏈；不支援 Spotify、Apple Music 頁面、Cookie、M3U8/DASH 或加密媒體。",
    "正在下载…": "正在下載…",
    "正在处理第 {current}/{total} 项":
        "正在處理第 {current}/{total} 項",
    "授权下载仅连接链接所在服务器，不支持订阅平台页面、Cookie、流媒体清单或加密媒体。":
        "授權下載僅連線至連結所在伺服器；不支援訂閱平台頁面、Cookie、串流播放清單或加密媒體。",
    "需要先停止当前任务。是否取消任务？":
        "關閉前必須停止目前的工作。要取消工作嗎？",
    "请输入有效的音频直链。": "請輸入有效的音訊直鏈。",
    "仅支持 HTTP 或 HTTPS 音频直链。":
        "僅支援 HTTP 或 HTTPS 音訊直鏈。",
    "下载地址不能包含账号或密码。":
        "下載網址不能包含帳號或密碼。",
    "不支持 Spotify 或 Apple Music 链接；请使用官方应用离线播放。":
        "不支援 Spotify 或 Apple Music 連結；請使用官方應用程式離線播放。",
    "不支持 M3U8、DASH 或其他流媒体播放清单。":
        "不支援 M3U8、DASH 或其他串流播放清單。",
    "该链接不是受支持的音频文件直链。":
        "此連結不是支援的音訊檔案直鏈。",
    "无效链接": "無效連結",
    "服务器未提供可识别的音频文件格式。":
        "伺服器未提供可辨識的音訊檔案格式。",
    "服务器返回 HTTP {code}。": "伺服器傳回 HTTP {code}。",
    "无法连接到下载地址：{error}":
        "無法連線至下載網址：{error}",
    "服务器返回的内容不是音频文件。":
        "伺服器傳回的內容不是音訊檔案。",
    "正在下载 {percent}%": "正在下載 {percent}%",
    "已下载 {size}": "已下載 {size}",
    "下载结束，但没有生成有效的音频文件。":
        "下載結束，但沒有產生有效的音訊檔案。",
    "检测到流媒体播放清单，已停止下载。":
        "偵測到串流播放清單，已停止下載。",
    "检测到加密或受保护的媒体，已停止下载。":
        "偵測到加密或受保護的媒體，已停止下載。",
    "下载完成": "下載完成",
    "视频清晰度增强": "影片清晰度增強",
    "图片清晰度增强": "圖片清晰度增強",
    "自然增强": "自然增強",
    "标准增强": "標準增強",
    "强力增强": "強力增強",
    "保持原尺寸（最高 4K）": "維持原尺寸（最高 4K）",
    "提升至 1080p": "提升至 1080p",
    "提升至 2K": "提升至 2K",
    "提升至 4K": "提升至 4K",
    "PNG（无损）": "PNG（無損）",
    "JPG（高质量）": "JPG（高畫質）",
    "WebP（高质量）": "WebP（高畫質）",
    "就绪：可拖入要增强的视频文件":
        "就緒：可拖入要增強的影片檔案",
    "就绪：可拖入要增强的图片文件":
        "就緒：可拖入要增強的圖片檔案",
    "格式转换 · 4K 清晰度增强 · 音乐解锁 · 授权下载":
        "格式轉換 · 4K 清晰度增強 · 音樂解鎖 · 授權下載",
    "增强强度": "增強強度",
    "输出分辨率": "輸出解析度",
    "选择要增强的视频文件": "選擇要增強的影片檔案",
    "选择要增强的图片文件": "選擇要增強的圖片檔案",
    "视频文件": "影片檔案",
    "选择视频文件夹": "選擇影片資料夾",
    "选择图片文件夹": "選擇圖片資料夾",
    "待增强视频": "待增強影片",
    "待增强图片": "待增強圖片",
    "拖入视频或文件夹，可批量增强":
        "拖入影片或資料夾，可批次增強",
    "拖入图片或文件夹，可批量增强":
        "拖入圖片或資料夾，可批次增強",
    "降噪、锐化并按原比例输出，最高支持 4K":
        "降噪、銳化並依原比例輸出，最高支援 4K",
    "把要增强的视频拖到这里": "將要增強的影片拖到這裡",
    "支持常见视频格式；输出为兼容性良好的 MP4":
        "支援常見影片格式；輸出為相容性良好的 MP4",
    "选择视频文件": "選擇影片檔案",
    "把要增强的图片拖到这里": "將要增強的圖片拖到這裡",
    "支持 JPG、PNG、WebP、BMP 与 TIFF":
        "支援 JPG、PNG、WebP、BMP 與 TIFF",
    "选择图片文件": "選擇圖片檔案",
    "开始增强": "開始增強",
    "轻度降噪与锐化，适合本身质量较好的素材。":
        "輕度降噪與銳化，適合原本畫質較好的素材。",
    "平衡降噪与细节增强，推荐用于大多数素材。":
        "平衡降噪與細節增強，建議用於大多數素材。",
    "更强的降噪与边缘增强，适合模糊或噪点明显的素材。":
        "更強的降噪與邊緣增強，適合模糊或雜訊明顯的素材。",
    "增强可改善观感并放大至 4K，但无法凭空恢复源文件中不存在的真实细节。":
        "增強可改善觀感並放大至 4K，但無法憑空恢復來源檔案中不存在的真實細節。",
    "正在增强…": "正在增強…",
    "图片与视频清晰度增强支持按原比例输出，最高可达 4K。":
        "圖片與影片清晰度增強支援依原比例輸出，最高可達 4K。",
    "增强完成 · {width}×{height}":
        "增強完成 · {width}×{height}",
    "不支持的图片输出格式：{target}":
        "不支援的圖片輸出格式：{target}",
    "请选择受支持的视频文件。": "請選擇支援的影片檔案。",
    "请选择受支持的图片文件。": "請選擇支援的圖片檔案。",
    "正在分析画面…": "正在分析畫面…",
    "该文件没有可增强的画面。": "此檔案沒有可增強的畫面。",
    "正在增强 {percent}%": "正在增強 {percent}%",
    "正在增强清晰度…": "正在增強清晰度…",
    "增强结束，但没有生成有效的输出文件。":
        "增強結束，但沒有產生有效的輸出檔案。",
    "增强完成": "增強完成",
    "图片水印区域修复": "圖片可見浮水印區域修復",
    "图片隐藏水印处理": "圖片隱藏浮水印處理",
    "AI 图片水印修复": "AI 圖片浮水印修復",
    "就绪：添加 AI 图片并框选可见角标":
        "就緒：加入 AI 圖片並框選可見角標",
    "同时处理像素隐藏标记（可选）": "同時處理像素隱藏標記（選用）",
    "对图片像素进行标准强度低位处理；可能损失细节，也不保证去除 SynthID 或其他鲁棒指纹。":
        "對圖片像素進行標準強度低位處理；可能損失細節，亦不保證去除 SynthID 或其他穩健指紋。",
    "拖入 AI 图片或文件夹，可批量套用框选区域":
        "拖入 AI 圖片或資料夾，可批次套用框選區域",
    "框选可见角标；可选在一次导出中同时处理像素隐藏标记":
        "框選可見角標；可選擇在一次匯出中同時處理像素隱藏標記",
    "把 AI 图片拖到这里": "將 AI 圖片拖到這裡",
    "在预览图框选可见角标，由周围纹理修复；可选同时处理像素低位。无自动识别，也不保证清除 SynthID、C2PA 或其他鲁棒溯源标记。请保留原图并核验。":
        "在預覽圖框選可見角標，以周圍紋理修復；可選擇同時處理像素低位。無自動辨識，亦不保證清除 SynthID、C2PA 或其他穩健溯源標記。請保留原圖並查驗。",
    "框选 AI 图片可见角标": "框選 AI 圖片可見角標",
    "框选 AI 图片上的可见标记": "框選 AI 圖片上的可見標記",
    "在预览图上框选可见角标或文字，可添加多个区域；尽量贴合边缘。":
        "在預覽圖框選可見角標或文字，可加入多個區域；盡量貼合邊緣。",
    "仅用于有权编辑的图片。批量图片共用相对位置；可在主界面选用像素低位处理，但不保证清除 SynthID 等鲁棒标记。保留原图并核验。":
        "僅用於有權編輯的圖片。批次圖片共用相對位置；可在主介面選用像素低位處理，但不保證清除 SynthID 等穩健標記。請保留原圖並查驗。",
    "请先框选可见角标或勾选隐藏像素处理。":
        "請先框選可見角標或勾選隱藏像素處理。",
    "不支持的修复边缘强度：{strength}":
        "不支援的修復邊緣強度：{strength}",
    "正在处理 AI 图片水印…": "正在處理 AI 圖片浮水印…",
    "AI 图片水印处理完成": "AI 圖片浮水印處理完成",
    "AI 图片处理完成 · {width}×{height} · 请核验结果":
        "AI 圖片處理完成 · {width}×{height} · 請查驗結果",
    "轻度处理": "輕度處理",
    "标准处理": "標準處理",
    "强力处理": "強力處理",
    "处理强度": "處理強度",
    "就绪：添加图片并选择隐藏水印处理强度":
        "就緒：加入圖片並選擇隱藏浮水印處理強度",
    "同时清理 EXIF/XMP 元数据": "同時清理 EXIF/XMP 中繼資料",
    "可选：不复制常见嵌入元数据。可能影响色彩信息和内容凭证；不保证清除全部隐藏标记。":
        "選用：不複製常見內嵌中繼資料。可能影響色彩資訊和內容憑證；不保證清除所有隱藏標記。",
    "待处理图片": "待處理圖片",
    "拖入图片或文件夹，可批量处理隐藏水印":
        "拖入圖片或資料夾，可批次處理隱藏浮水印",
    "处理像素低位，按强度轻度平滑；支持可选元数据清理":
        "處理像素低位，依強度輕度平滑；可選擇清理中繼資料",
    "把要处理的图片拖到这里": "將要處理的圖片拖到這裡",
    "固定 RGB 最低 1 位，主要针对简单的像素低位标记。":
        "固定 RGB 最低 1 位，主要針對簡單的像素低位標記。",
    "轻度平滑并固定 RGB 最低 2 位，推荐先试用。":
        "輕度平滑並固定 RGB 最低 2 位，建議先試用。",
    "更强平滑并固定 RGB 最低 3 位，可能损失细节。":
        "更強的平滑並固定 RGB 最低 3 位，可能損失細節。",
    "仅尽力削弱部分像素隐藏标记；无法保证去除未知指纹或 C2PA 溯源。PNG 最适合低位处理；请保留原图并自行核验。":
        "僅盡力減弱部分像素隱藏標記；無法保證去除未知指紋或 C2PA 溯源。PNG 最適合低位處理；請保留原圖並自行查驗。",
    "不支持的隐藏水印处理强度：{strength}":
        "不支援的隱藏浮水印處理強度：{strength}",
    "该文件没有可处理的画面。": "此檔案沒有可處理的畫面。",
    "正在处理隐藏水印…": "正在處理隱藏浮水印…",
    "处理结束，但没有生成有效的输出文件。":
        "處理完成，但沒有產生有效的輸出檔案。",
    "隐藏水印处理完成": "隱藏浮水印處理完成",
    "隐藏水印处理完成 · {width}×{height} · 请自行核验":
        "已處理 · {width}×{height} · 請自行查驗",
    "精细修复": "精細修復",
    "标准修复": "標準修復",
    "扩展修复": "擴展修復",
    "就绪：添加图片并框选可见水印区域":
        "就緒：加入圖片並框選可見浮水印區域",
    "框选修复区域": "框選修復區域",
    "修复边缘": "修復邊緣",
    "待修复图片": "待修復圖片",
    "拖入图片或文件夹，可批量套用所选区域":
        "拖入圖片或資料夾，可批次套用所選區域",
    "框选一处或多处可见水印，由本地 FFmpeg 修复周围纹理":
        "框選一處或多處可見浮水印，由本機 FFmpeg 修復周圍紋理",
    "把要修复的图片拖到这里": "將要修復的圖片拖到這裡",
    "支持 JPG、PNG、WebP、BMP 与 TIFF；原图不会改动":
        "支援 JPG、PNG、WebP、BMP 與 TIFF；不會改動原圖",
    "开始修复": "開始修復",
    "严格使用框选范围，适合边界清楚且选择准确的水印。":
        "嚴格使用框選範圍，適合邊界清楚且選取準確的浮水印。",
    "轻微扩展选区边缘，兼顾抗锯齿与自然过渡，推荐使用。":
        "輕微擴展選取區域邊緣，兼顧反鋸齒與自然過渡，建議使用。",
    "进一步覆盖水印阴影和描边，可能影响更多周围纹理。":
        "進一步覆蓋浮水印陰影與描邊，可能影響更多周圍紋理。",
    "仅针对手动框选的可见区域修复画面；不提供隐藏标记的检测或定向清除。导出重新编码可能使 C2PA 等内容凭证失效，请保留原图。":
        "畫面修復僅針對手動框選的可見區域；不偵測或定向清除隱藏標記。匯出重新編碼可能使 C2PA 等內容憑證失效，請保留原圖。",
    "尚未选择修复区域": "尚未選擇修復區域",
    "已选择 {count} 个区域": "已選擇 {count} 個區域",
    "尚未添加图片": "尚未加入圖片",
    "请先添加需要修复的图片。": "請先加入需要修復的圖片。",
    "选择要修复的图片文件": "選擇要修復的圖片檔案",
    "框选可见水印区域": "框選可見浮水印區域",
    "框选需要修复的可见水印": "框選需要修復的可見浮水印",
    "在预览图上拖动鼠标框选水印，可添加多个区域；框选时尽量贴合水印边缘。":
        "在預覽圖上拖動滑鼠框選浮水印，可加入多個區域；框選時請盡量貼合浮水印邊緣。",
    "撤销上一步": "復原上一步",
    "清空区域": "清空區域",
    "取消": "取消",
    "保存区域": "儲存區域",
    "仅用于你拥有或获授权编辑的图片。队列中的图片将使用相同的相对位置。此功能不检测或定向清除隐藏标记；导出重新编码可能改变元数据或使 C2PA 等内容凭证失效，请保留原图。":
        "僅用於您擁有或獲授權編輯的圖片。佇列中的圖片會使用相同的相對位置。此功能不偵測或定向清除隱藏標記；匯出重新編碼可能改變中繼資料或使 C2PA 等內容憑證失效，請保留原圖。",
    "无法读取图片": "無法讀取圖片",
    "已保存 {count} 个修复区域": "已儲存 {count} 個修復區域",
    "请先在图片预览中框选至少一个可见水印区域。":
        "請先在圖片預覽中框選至少一個可見浮水印區域。",
    "正在修复…": "正在修復…",
    "正在修复选中区域…": "正在修復所選區域…",
    "该文件没有可修复的画面。": "此檔案沒有可修復的畫面。",
    "修复结束，但没有生成有效的输出文件。":
        "修復結束，但沒有產生有效的輸出檔案。",
    "水印区域修复完成": "浮水印區域修復完成",
    "修复完成 · {count} 个区域 · {width}×{height}":
        "修復完成 · {count} 個區域 · {width}×{height}",
    "可见水印区域修复适用于有权编辑的图片；重新编码可能改变元数据或使内容凭证失效。":
        "可見浮水印區域修復適用於有權編輯的圖片；重新編碼可能改變中繼資料或使內容憑證失效。",
    "功能导航": "功能導覽",
    "功能": "功能",
    "视频工具": "影片工具",
    "音频工具": "音訊工具",
    "图片工具": "圖片工具",
    "视频转换": "影片轉換",
    "视频增强": "影片增強",
    "提取音频": "擷取音訊",
    "音频转换": "音訊轉換",
    "本地音乐解锁": "本機音樂解鎖",
    "图片增强": "圖片增強",
    "可见水印修复": "可見浮水印修復",
    "隐藏水印处理": "隱藏浮水印處理",
    "AI 水印修复": "AI 浮水印修復",
    "切换功能会保留文件队列；开始前请确认文件类型适用于当前任务。":
        "切換功能仍會保留檔案佇列；開始前請確認檔案類型適用於目前工作。",
    "转换视频格式，按需要选择编码、画质与分辨率。":
        "轉換影片格式，按需要選擇編碼、畫質與解析度。",
    "为视频降噪与锐化，按原比例提升至最高 4K。":
        "為影片降噪與銳化，按原比例提升至最高 4K。",
    "按画质目标压缩视频，兼顾体积与兼容性。":
        "按照畫質目標壓縮影片，兼顧大小與相容性。",
    "从视频导出音频，也可直接复制原始音轨。":
        "從影片匯出音訊，也可直接複製原始音軌。",
    "转换常用音频格式，选择适合的质量方案。":
        "轉換常用音訊格式，選擇適合的品質方案。",
    "批量处理你有权使用的本地音乐文件。":
        "批次處理你有權使用的本機音樂檔案。",
    "粘贴公开音频文件直链，批量保存至本机。":
        "貼上公開音訊檔案的直接連結，批次儲存到本機。",
    "改善图片观感，按比例放大至最高 4K。":
        "改善圖片觀感，按比例放大至最高 4K。",
    "框选可见标记，由周围画面修复所选区域。":
        "框選可見標記，由周圍畫面修復選取區域。",
    "处理简单像素隐藏标记，可选清理常见元数据。":
        "處理簡單像素隱藏標記，可選擇清理常見中繼資料。",
    "框选可见角标，可选处理简单像素低位标记。":
        "框選可見角標，可選擇處理簡單像素低位標記。",
}

CATALOGS = {"en_US": EN_US, "zh_TW": ZH_TW}


def language_for_system_locale(locale_name: str) -> str:
    """Choose the closest bundled language on first launch."""
    locale = locale_name.replace("-", "_").lower()
    if locale.startswith(("zh_tw", "zh_hk", "zh_mo")) or (
        locale.startswith("zh_") and "_hant" in locale
    ):
        return "zh_TW"
    if locale.startswith("en"):
        return "en_US"
    return "zh_CN"


def translate(key: str, language: str = "zh_CN", **values: object) -> str:
    """Unknown locales fall back to Simplified Chinese."""
    template = CATALOGS.get(language, {}).get(key, key)
    return template.format(**values) if values else template
