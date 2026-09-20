"""One-pass image export combining selected visible-area repair with optional
low-bit pixel treatment. It cannot identify a generator or verify provenance.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable, Iterable

from clarity_enhance import IMAGE_EXTENSIONS
from engine import (
    ConversionCancelled, ConversionError, ConversionOptions, MediaInfo,
    _run_ffmpeg, ffmpeg_path, probe_media,
)
from hidden_watermark import build_hidden_pixel_filter
from i18n import translate
from watermark_repair import (
    WATERMARK_REPAIR_STRENGTHS, WATERMARK_REPAIR_TARGETS,
    WatermarkRegion, display_dimensions, normalize_regions,
    padding_pixels, write_region_mask,
)


MODE_AI_IMAGE_WATERMARK = "AI 图片水印修复"
AI_WATERMARK_TARGETS = WATERMARK_REPAIR_TARGETS
AI_WATERMARK_STRENGTHS = WATERMARK_REPAIR_STRENGTHS

_TARGETS = {
    "PNG（无损）": (".png", "png"),
    "JPG（高质量）": (".jpg", "mjpeg"),
    "WebP（高质量）": (".webp", "libwebp"),
}


@dataclass(frozen=True)
class AIWatermarkResult:
    output_path: Path
    width: int
    height: int
    region_count: int
    locale: str = "zh_CN"

    @property
    def size_message(self) -> str:
        return translate(
            "AI 图片处理完成 · {width}×{height} · 请核验结果",
            self.locale, width=self.width, height=self.height,
        )


def make_ai_output_path(source: Path, options: ConversionOptions) -> Path:
    try:
        extension = _TARGETS[options.target][0]
    except KeyError as exc:
        raise ConversionError(translate(
            "不支持的图片输出格式：{target}",
            options.locale, target=options.target,
        )) from exc
    candidate = options.output_dir / f"{source.stem}_ai_repaired{extension}"
    if options.overwrite or not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = options.output_dir / f"{source.stem}_ai_repaired_{index}{extension}"
        if not candidate.exists():
            return candidate
        index += 1


def _graph_filter_path(path: Path) -> str:
    """Escape the option value, then the enclosing FFmpeg filtergraph.

    FFmpeg consumes two parsing layers for -filter_complex. Quoting a path at
    only one layer breaks on apostrophes, semicolons and graph label brackets.
    Arguments are passed directly to the process, without a shell layer.
    """
    value = str(path.resolve()).replace("\\", "/")
    option = "".join(("\\" if char in "\\':" else "") + char for char in value)
    return "".join(("\\" if char in "\\'[],;" else "") + char
                   for char in option)


def build_ai_watermark_command(
    source: Path,
    output: Path,
    options: ConversionOptions,
    mask: Path | None,
    process_hidden: bool,
) -> list[str]:
    try:
        _extension, encoder = _TARGETS[options.target]
    except KeyError as exc:
        raise ConversionError(translate(
            "不支持的图片输出格式：{target}",
            options.locale, target=options.target,
        )) from exc
    if options.quality not in AI_WATERMARK_STRENGTHS:
        raise ConversionError(translate(
            "不支持的修复边缘强度：{strength}",
            options.locale, strength=options.quality,
        ))
    if mask is None and not process_hidden:
        raise ConversionError(translate(
            "请先框选可见角标或勾选隐藏像素处理。", options.locale))

    filters = []
    if mask is not None:
        filters.append(f"removelogo=filename={_graph_filter_path(mask)}")
    if process_hidden:
        filters.append(build_hidden_pixel_filter("标准处理", options.locale))
    # removelogo discards alpha on its own. Restore the original alpha plane
    # after image repair, before handing the output to PNG/WebP encoders.
    graph = (
        "format=rgba,split[work][original_alpha];"
        f"[work]{','.join(filters)}[repaired];"
        "[original_alpha]alphaextract[alpha];"
        "[repaired][alpha]alphamerge,format=rgba[out]"
    )

    command = [
        str(ffmpeg_path(options.locale)),
        "-hide_banner", "-y", "-nostdin", "-stats_period", "0.5",
        "-i", str(source),
        "-filter_complex", graph,
        "-map", "[out]", "-map_metadata", "0",
        "-frames:v", "1", "-c:v", encoder,
    ]
    if options.target == "PNG（无损）":
        command += ["-compression_level", "6"]
    elif options.target == "JPG（高质量）":
        command += ["-q:v", "2"]
    else:
        command += ["-quality", "92", "-compression_level", "4"]
    command += ["-update", "1", "-progress", "pipe:1", "-nostats", str(output)]
    return command


def repair_ai_watermark(
    source: Path,
    options: ConversionOptions,
    regions: Iterable[WatermarkRegion],
    process_hidden: bool = False,
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
) -> AIWatermarkResult:
    """Publish one new image after either or both selected repair operations."""
    source = source.resolve()
    if not source.is_file():
        raise ConversionError(translate("输入文件不存在。", options.locale))
    if source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ConversionError(translate("请选择受支持的图片文件。", options.locale))
    selected = tuple(regions)
    checked = normalize_regions(selected) if selected else ()
    if not checked and not process_hidden:
        raise ConversionError(translate(
            "请先框选可见角标或勾选隐藏像素处理。", options.locale))
    if options.target not in _TARGETS or options.quality not in AI_WATERMARK_STRENGTHS:
        build_ai_watermark_command(source, source, options, None, True)

    cancel_event = cancel_event or Event()
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")
    if progress_callback:
        progress_callback(4, translate("正在分析画面…", options.locale))
    info: MediaInfo = probe_media(source, options.locale)
    if not info.video_codec or info.width <= 0 or info.height <= 0:
        raise ConversionError(translate("该文件没有可修复的画面。", options.locale))

    width, height = display_dimensions(source, info, options.locale)
    options.output_dir.mkdir(parents=True, exist_ok=True)
    output = make_ai_output_path(source, options)
    token = uuid.uuid4().hex
    temporary = output.with_name(f".{output.stem}.{token}.partial{output.suffix}")
    mask = (options.output_dir / f".{source.stem}.{token}.ai-mask.pgm"
            if checked else None)
    try:
        if mask is not None:
            padding = padding_pixels(width, height, options.quality)
            write_region_mask(mask, width, height, checked, padding)
        command = build_ai_watermark_command(
            source, temporary, options, mask, process_hidden)
        if progress_callback:
            progress_callback(12, translate("正在处理 AI 图片水印…", options.locale))
        _run_ffmpeg(command, info, progress_callback, cancel_event, options.locale)
        if cancel_event.is_set():
            raise ConversionCancelled("任务已取消")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ConversionError(translate(
                "修复结束，但没有生成有效的输出文件。", options.locale))
        if not options.overwrite and output.exists():
            output = make_ai_output_path(source, options)
        try:
            temporary.replace(output)
        except OSError as exc:
            raise ConversionError(translate(
                "无法保存输出文件：{error}", options.locale, error=exc)) from exc
    finally:
        if temporary.exists():
            temporary.unlink()
        if mask is not None and mask.exists():
            mask.unlink()

    if progress_callback:
        progress_callback(100, translate("AI 图片水印处理完成", options.locale))
    return AIWatermarkResult(output, width, height, len(checked), options.locale)
