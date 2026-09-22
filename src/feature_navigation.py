"""Presentation-only labels for the individual media workspaces.

Mode values are the existing engine identifiers; navigation never translates or
changes them before the original task dispatcher receives them.
"""

from ai_watermark import MODE_AI_IMAGE_WATERMARK
from clarity_enhance import MODE_IMAGE_ENHANCE, MODE_VIDEO_ENHANCE
from direct_download import MODE_DIRECT_DOWNLOAD
from engine import MODE_AUDIO, MODE_COMPRESS, MODE_EXTRACT, MODE_VIDEO
from hidden_watermark import MODE_IMAGE_HIDDEN_WATERMARK
from music_unlock import MODE_MUSIC_UNLOCK
from watermark_repair import MODE_IMAGE_WATERMARK_REPAIR


FEATURE_SECTIONS = (
    ("视频工具", (
        (MODE_VIDEO, "视频转换", "video"),
        (MODE_VIDEO_ENHANCE, "视频增强", "spark"),
        (MODE_COMPRESS, "视频压缩", "compress"),
        (MODE_EXTRACT, "提取音频", "extract"),
    )),
    ("音频工具", (
        (MODE_AUDIO, "音频转换", "audio"),
        (MODE_MUSIC_UNLOCK, "本地音乐解锁", "music"),
        (MODE_DIRECT_DOWNLOAD, "授权音频下载", "download"),
    )),
    ("图片工具", (
        (MODE_IMAGE_ENHANCE, "图片增强", "image"),
        (MODE_IMAGE_WATERMARK_REPAIR, "可见水印修复", "select"),
        (MODE_IMAGE_HIDDEN_WATERMARK, "隐藏水印处理", "shield"),
        (MODE_AI_IMAGE_WATERMARK, "AI 水印修复", "spark"),
    )),
)

FEATURE_MODES = tuple(mode for _section, entries in FEATURE_SECTIONS
                      for mode, _label, _icon in entries)

FEATURE_SUMMARIES = {
    MODE_VIDEO: "转换视频格式，按需要选择编码、画质与分辨率。",
    MODE_VIDEO_ENHANCE: "为视频降噪与锐化，按原比例提升至最高 4K。",
    MODE_COMPRESS: "按画质目标压缩视频，兼顾体积与兼容性。",
    MODE_EXTRACT: "从视频导出音频，也可直接复制原始音轨。",
    MODE_AUDIO: "转换常用音频格式，选择适合的质量方案。",
    MODE_MUSIC_UNLOCK: "批量处理你有权使用的本地音乐文件。",
    MODE_DIRECT_DOWNLOAD: "粘贴公开音频文件直链，批量保存至本机。",
    MODE_IMAGE_ENHANCE: "改善图片观感，按比例放大至最高 4K。",
    MODE_IMAGE_WATERMARK_REPAIR: "框选可见标记，由周围画面修复所选区域。",
    MODE_IMAGE_HIDDEN_WATERMARK: "处理简单像素隐藏标记，可选清理常见元数据。",
    MODE_AI_IMAGE_WATERMARK: "框选可见角标，可选处理简单像素低位标记。",
}
