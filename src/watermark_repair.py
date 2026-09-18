"""Visible watermark-region repair powered by FFmpeg's removelogo filter.

The user explicitly supplies one or more normalized rectangles.  This module
does not detect, inspect, or target invisible provenance or fingerprint marks.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable, Iterable

from clarity_enhance import IMAGE_EXTENSIONS
from engine import (
    ConversionCancelled,
    ConversionError,
    ConversionOptions,
    MediaInfo,
    _run_ffmpeg,
    _run_capture,
    ffmpeg_path,
    ffprobe_path,
    probe_media,
)
from i18n import translate


MODE_IMAGE_WATERMARK_REPAIR = "图片水印区域修复"
WATERMARK_REPAIR_TARGETS = ["PNG（无损）", "JPG（高质量）", "WebP（高质量）"]
WATERMARK_REPAIR_STRENGTHS = ["精细修复", "标准修复", "扩展修复"]

_IMAGE_TARGETS = {
    "PNG（无损）": (".png", "png"),
    "JPG（高质量）": (".jpg", "mjpeg"),
    "WebP（高质量）": (".webp", "libwebp"),
}
_PADDING_RATIOS = {
    "精细修复": 0.0,
    "标准修复": 0.0025,
    "扩展修复": 0.005,
}
MAX_REGIONS = 12
MAX_SELECTED_AREA = 0.55


@dataclass(frozen=True)
class WatermarkRegion:
    """Rectangle coordinates normalized to the displayed image."""

    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class WatermarkRepairResult:
    output_path: Path
    width: int
    height: int
    region_count: int
    locale: str = "zh_CN"

    @property
    def size_message(self) -> str:
        return translate(
            "修复完成 · {count} 个区域 · {width}×{height}",
            self.locale,
            count=self.region_count,
            width=self.width,
            height=self.height,
        )


def normalize_regions(regions: Iterable[WatermarkRegion]) -> tuple[WatermarkRegion, ...]:
    """Validate and clip user selections to the normalized image bounds."""

    normalized: list[WatermarkRegion] = []
    for region in regions:
        values = (region.x, region.y, region.width, region.height)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("region coordinates must be finite")
        left = min(1.0, max(0.0, region.x))
        top = min(1.0, max(0.0, region.y))
        right = min(1.0, max(0.0, region.x + region.width))
        bottom = min(1.0, max(0.0, region.y + region.height))
        if right - left < 0.001 or bottom - top < 0.001:
            raise ValueError("watermark region is too small")
        normalized.append(WatermarkRegion(left, top, right - left, bottom - top))

    if not normalized:
        raise ValueError("at least one watermark region is required")
    if len(normalized) > MAX_REGIONS:
        raise ValueError(f"no more than {MAX_REGIONS} regions are supported")
    if sum(region.area for region in normalized) > MAX_SELECTED_AREA:
        raise ValueError("selected regions cover too much of the image")
    return tuple(normalized)


def padding_pixels(width: int, height: int, strength: str) -> int:
    if strength not in _PADDING_RATIOS:
        raise ValueError(f"unsupported repair strength: {strength}")
    return min(16, max(0, round(min(width, height) * _PADDING_RATIOS[strength])))


def display_dimensions(
    source: Path,
    info: MediaInfo,
    language: str = "zh_CN",
) -> tuple[int, int]:
    """Return dimensions after FFmpeg's automatic EXIF/display rotation."""

    try:
        command = [
            str(ffprobe_path(language)),
            "-v", "error", "-select_streams", "v:0",
            "-read_intervals", "%+#1",
            "-show_entries", "frame_side_data=rotation",
            "-of", "json", str(source),
        ]
        data = json.loads(_run_capture(command, language=language))
    except (ConversionError, json.JSONDecodeError, ValueError):
        return info.width, info.height

    frames = data.get("frames") or []
    side_data = (frames[0].get("side_data_list") or []) if frames else []
    rotation = 0.0
    for item in side_data:
        if "rotation" in item:
            try:
                rotation = float(item["rotation"])
            except (TypeError, ValueError):
                rotation = 0.0
            break
    quarter_turn = int(round(rotation / 90.0)) % 2 != 0
    return ((info.height, info.width) if quarter_turn
            else (info.width, info.height))


def write_region_mask(
    path: Path,
    width: int,
    height: int,
    regions: Iterable[WatermarkRegion],
    padding: int = 0,
) -> None:
    """Write an 8-bit PGM mask accepted by FFmpeg's removelogo filter."""

    if width < 3 or height < 3:
        raise ValueError("image dimensions are too small")
    checked = normalize_regions(regions)
    pixels = bytearray(width * height)

    for region in checked:
        left = max(1, math.floor(region.x * width) - padding)
        top = max(1, math.floor(region.y * height) - padding)
        right = min(width - 1, math.ceil((region.x + region.width) * width) + padding)
        bottom = min(height - 1, math.ceil((region.y + region.height) * height) + padding)
        if right <= left or bottom <= top:
            continue
        fill = b"\xff" * (right - left)
        for row in range(top, bottom):
            start = row * width + left
            pixels[start:start + len(fill)] = fill

    path.write_bytes(f"P5\n{width} {height}\n255\n".encode("ascii") + pixels)


def _filter_path(path: Path) -> str:
    """Escape a path for a quoted FFmpeg filter option on POSIX and Windows."""

    value = str(path.resolve()).replace("\\", "/")
    for character in ("\\", "'", ":", ",", ";", "[", "]"):
        value = value.replace(character, "\\" + character)
    return value


def make_watermark_output_path(source: Path, options: ConversionOptions) -> Path:
    try:
        extension = _IMAGE_TARGETS[options.target][0]
    except KeyError as exc:
        raise ConversionError(translate(
            "不支持的图片输出格式：{target}",
            options.locale,
            target=options.target,
        )) from exc

    candidate = options.output_dir / f"{source.stem}_watermark_repaired{extension}"
    if options.overwrite or not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = options.output_dir / (
            f"{source.stem}_watermark_repaired_{index}{extension}"
        )
        if not candidate.exists():
            return candidate
        index += 1


def build_watermark_repair_command(
    source: Path,
    output: Path,
    mask: Path,
    options: ConversionOptions,
) -> list[str]:
    try:
        _extension, encoder = _IMAGE_TARGETS[options.target]
    except KeyError as exc:
        raise ConversionError(translate(
            "不支持的图片输出格式：{target}",
            options.locale,
            target=options.target,
        )) from exc

    command = [
        str(ffmpeg_path(options.locale)),
        "-hide_banner", "-y", "-nostdin", "-stats_period", "0.5",
        "-i", str(source),
        "-map", "0:v:0", "-map_metadata", "0",
        "-vf", f"removelogo=filename='{_filter_path(mask)}'",
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


def repair_visible_watermark(
    source: Path,
    options: ConversionOptions,
    regions: Iterable[WatermarkRegion],
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
) -> WatermarkRepairResult:
    """Repair user-selected visible overlay areas without modifying the source."""

    source = source.resolve()
    if not source.is_file():
        raise ConversionError(translate("输入文件不存在。", options.locale))
    if source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ConversionError(translate("请选择受支持的图片文件。", options.locale))
    checked = normalize_regions(regions)
    cancel_event = cancel_event or Event()
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")

    options.output_dir.mkdir(parents=True, exist_ok=True)
    if progress_callback:
        progress_callback(4, translate("正在分析画面…", options.locale))
    info: MediaInfo = probe_media(source, options.locale)
    if not info.video_codec or info.width <= 0 or info.height <= 0:
        raise ConversionError(translate("该文件没有可修复的画面。", options.locale))

    display_width, display_height = display_dimensions(
        source, info, options.locale)
    output = make_watermark_output_path(source, options)
    token = uuid.uuid4().hex
    temporary = output.with_name(
        f".{output.stem}.{token}.partial{output.suffix}"
    )
    mask = options.output_dir / f".{source.stem}.{token}.watermark-mask.pgm"
    padding = padding_pixels(display_width, display_height, options.quality)

    try:
        write_region_mask(mask, display_width, display_height, checked, padding)
        command = build_watermark_repair_command(
            source, temporary, mask, options,
        )
        if progress_callback:
            progress_callback(12, translate("正在修复选中区域…", options.locale))
        _run_ffmpeg(command, info, progress_callback, cancel_event, options.locale)
        if cancel_event.is_set():
            raise ConversionCancelled("任务已取消")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ConversionError(translate(
                "修复结束，但没有生成有效的输出文件。", options.locale))
        if not options.overwrite and output.exists():
            output = make_watermark_output_path(source, options)
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
        if mask.exists():
            mask.unlink()

    if progress_callback:
        progress_callback(100, translate("水印区域修复完成", options.locale))
    return WatermarkRepairResult(
        output_path=output,
        width=display_width,
        height=display_height,
        region_count=len(checked),
        locale=options.locale,
    )
