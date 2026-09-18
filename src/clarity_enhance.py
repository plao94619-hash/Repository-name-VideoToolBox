from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from threading import Event
from typing import Callable

from engine import (
    VIDEO_EXTENSIONS,
    ConversionCancelled,
    ConversionError,
    ConversionOptions,
    MediaInfo,
    MODE_VIDEO,
    _run_ffmpeg,
    _video_quality_args,
    choose_video_encoder,
    ffmpeg_path,
    probe_media,
)
from i18n import translate


MODE_VIDEO_ENHANCE = "视频清晰度增强"
MODE_IMAGE_ENHANCE = "图片清晰度增强"

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff",
}

ENHANCE_STRENGTHS = ["自然增强", "标准增强", "强力增强"]
ENHANCE_RESOLUTIONS = [
    "保持原尺寸（最高 4K）",
    "提升至 1080p",
    "提升至 2K",
    "提升至 4K",
]
VIDEO_ENHANCE_TARGETS = ["MP4"]
IMAGE_ENHANCE_TARGETS = ["PNG（无损）", "JPG（高质量）", "WebP（高质量）"]

_TARGET_BOUNDS = {
    "提升至 1080p": (1920, 1080),
    "提升至 2K": (2560, 1440),
    "提升至 4K": (3840, 2160),
}
_IMAGE_TARGETS = {
    "PNG（无损）": (".png", "png"),
    "JPG（高质量）": (".jpg", "mjpeg"),
    "WebP（高质量）": (".webp", "libwebp"),
}
_STRENGTH_FILTERS = {
    "自然增强": (
        "hqdn3d=0.8:0.8:3.0:3.0",
        "unsharp=5:5:0.35:3:3:0.0",
    ),
    "标准增强": (
        "hqdn3d=1.4:1.4:5.0:5.0",
        "unsharp=5:5:0.55:3:3:0.10",
    ),
    "强力增强": (
        "hqdn3d=2.2:2.2:8.0:8.0",
        "unsharp=7:7:0.75:5:5:0.15",
    ),
}


@dataclass(frozen=True)
class EnhancementResult:
    output_path: Path
    width: int
    height: int
    locale: str = "zh_CN"

    @property
    def size_message(self) -> str:
        return translate(
            "增强完成 · {width}×{height}",
            self.locale,
            width=self.width,
            height=self.height,
        )


def _even_floor(value: float) -> int:
    return max(2, int(value) // 2 * 2)


def output_dimensions(
    width: int,
    height: int,
    resolution: str,
) -> tuple[int, int]:
    """Return an aspect-safe, encoder-safe size capped at UHD 4K."""
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if resolution not in ENHANCE_RESOLUTIONS:
        raise ValueError(f"unsupported enhancement resolution: {resolution}")

    landscape = width >= height
    max_width, max_height = ((3840, 2160) if landscape else (2160, 3840))
    if resolution == "保持原尺寸（最高 4K）":
        scale = min(1.0, max_width / width, max_height / height)
    else:
        target_width, target_height = _TARGET_BOUNDS[resolution]
        if not landscape:
            target_width, target_height = target_height, target_width
        scale = min(target_width / width, target_height / height)

    output_width = min(max_width, _even_floor(width * scale))
    output_height = min(max_height, _even_floor(height * scale))
    return output_width, output_height


def enhance_filter(width: int, height: int, strength: str) -> str:
    if strength not in _STRENGTH_FILTERS:
        raise ValueError(f"unsupported enhancement strength: {strength}")
    denoise, sharpen = _STRENGTH_FILTERS[strength]
    scale = (
        f"scale={width}:{height}:"
        "flags=lanczos+accurate_rnd+full_chroma_int"
    )
    return ",".join((denoise, scale, sharpen, "setsar=1"))


def _resolution_suffix(resolution: str) -> str:
    return {
        "保持原尺寸（最高 4K）": "",
        "提升至 1080p": "_1080p",
        "提升至 2K": "_2k",
        "提升至 4K": "_4k",
    }[resolution]


def make_enhance_output_path(
    source: Path,
    options: ConversionOptions,
) -> Path:
    if options.mode == MODE_VIDEO_ENHANCE:
        extension = ".mp4"
    elif options.mode == MODE_IMAGE_ENHANCE:
        try:
            extension = _IMAGE_TARGETS[options.target][0]
        except KeyError as exc:
            raise ConversionError(translate(
                "不支持的图片输出格式：{target}",
                options.locale,
                target=options.target,
            )) from exc
    else:
        raise ConversionError(translate(
            "未知任务类型：{mode}", options.locale, mode=options.mode))

    stem = f"{source.stem}_enhanced{_resolution_suffix(options.resolution)}"
    candidate = options.output_dir / f"{stem}{extension}"
    if options.overwrite or not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = options.output_dir / f"{stem}_{index}{extension}"
        if not candidate.exists():
            return candidate
        index += 1


def _video_encoder(options: ConversionOptions) -> str:
    encoder_options = replace(options, mode=MODE_VIDEO, quality="画质优先")
    return choose_video_encoder(encoder_options, "MP4")


def build_enhance_command(
    source: Path,
    output: Path,
    options: ConversionOptions,
    info: MediaInfo,
    encoder_override: str | None = None,
) -> tuple[list[str], tuple[int, int], str]:
    width, height = output_dimensions(info.width, info.height, options.resolution)
    filters = enhance_filter(width, height, options.quality)
    command = [
        str(ffmpeg_path(options.locale)),
        "-hide_banner", "-y", "-nostdin", "-stats_period", "0.5",
        "-i", str(source),
    ]

    encoder = ""
    if options.mode == MODE_VIDEO_ENHANCE:
        encoder = encoder_override or _video_encoder(options)
        video_map = (
            f"0:{info.video_stream_index}"
            if info.video_stream_index is not None else "0:v:0"
        )
        command += [
            "-map", video_map, "-map", "0:a?", "-map_metadata", "0",
            "-map_chapters", "0", "-vf", filters, "-c:v", encoder,
        ]
        command += _video_quality_args(encoder, "画质优先")
        command += [
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
        ]
    elif options.mode == MODE_IMAGE_ENHANCE:
        try:
            _extension, encoder = _IMAGE_TARGETS[options.target]
        except KeyError as exc:
            raise ConversionError(translate(
                "不支持的图片输出格式：{target}",
                options.locale,
                target=options.target,
            )) from exc
        command += ["-map", "0:v:0", "-vf", filters, "-frames:v", "1", "-c:v", encoder]
        if options.target == "PNG（无损）":
            command += ["-compression_level", "6"]
        elif options.target == "JPG（高质量）":
            command += ["-q:v", "2", "-pix_fmt", "yuvj444p"]
        else:
            command += ["-quality", "95", "-compression_level", "6"]
        command += ["-update", "1"]
    else:
        raise ConversionError(translate(
            "未知任务类型：{mode}", options.locale, mode=options.mode))

    command += ["-progress", "pipe:1", "-nostats", str(output)]
    return command, (width, height), encoder


def enhance_media_file(
    source: Path,
    options: ConversionOptions,
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
) -> EnhancementResult:
    source = source.resolve()
    if not source.is_file():
        raise ConversionError(translate("输入文件不存在。", options.locale))
    if options.mode == MODE_VIDEO_ENHANCE and source.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ConversionError(translate("请选择受支持的视频文件。", options.locale))
    if options.mode == MODE_IMAGE_ENHANCE and source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ConversionError(translate("请选择受支持的图片文件。", options.locale))

    cancel_event = cancel_event or Event()
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")
    options.output_dir.mkdir(parents=True, exist_ok=True)
    if progress_callback:
        progress_callback(4, translate("正在分析画面…", options.locale))

    info = probe_media(source, options.locale)
    if not info.video_codec or not info.width or not info.height:
        raise ConversionError(translate("该文件没有可增强的画面。", options.locale))
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")

    output = make_enhance_output_path(source, options)
    temporary = output.with_name(
        f".{output.stem}.{uuid.uuid4().hex}.partial{output.suffix}")
    command, dimensions, encoder = build_enhance_command(
        source, temporary, options, info)

    def forward_progress(percent: int, message: str) -> None:
        if not progress_callback:
            return
        if percent >= 0:
            progress_callback(percent, translate(
                "正在增强 {percent}%", options.locale, percent=percent))
        else:
            progress_callback(percent, message)

    try:
        if progress_callback:
            progress_callback(8, translate("正在增强清晰度…", options.locale))
        try:
            _run_ffmpeg(
                command, info, forward_progress, cancel_event, options.locale)
        except ConversionError:
            hardware = encoder.endswith(("_nvenc", "_qsv", "_amf"))
            if options.mode != MODE_VIDEO_ENHANCE or options.encoder != "自动选择" or not hardware:
                raise
            if temporary.exists():
                temporary.unlink()
            if progress_callback:
                progress_callback(8, translate(
                    "硬件编码失败，已切换 CPU 重试", options.locale))
            cpu_command, dimensions, _encoder = build_enhance_command(
                source, temporary, options, info, encoder_override="libx264")
            _run_ffmpeg(
                cpu_command, info, forward_progress, cancel_event, options.locale)

        if cancel_event.is_set():
            raise ConversionCancelled("任务已取消")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ConversionError(translate(
                "增强结束，但没有生成有效的输出文件。", options.locale))
        if not options.overwrite and output.exists():
            output = make_enhance_output_path(source, options)
        try:
            temporary.replace(output)
        except OSError as exc:
            raise ConversionError(translate(
                "无法保存输出文件：{error}",
                options.locale,
                error=exc,
            )) from exc
    finally:
        if temporary.exists():
            temporary.unlink()

    if progress_callback:
        progress_callback(100, translate("增强完成", options.locale))
    return EnhancementResult(
        output_path=output,
        width=dimensions[0],
        height=dimensions[1],
        locale=options.locale,
    )
