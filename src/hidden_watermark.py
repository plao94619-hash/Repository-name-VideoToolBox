"""Best-effort processing of low-bit image marks, separate from visible repair.

No image-only transform can detect or guarantee removal of unknown robust marks.
The original file is retained; the output is always a new image.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from clarity_enhance import IMAGE_EXTENSIONS
from engine import (
    ConversionCancelled, ConversionError, ConversionOptions, MediaInfo,
    _run_ffmpeg, ffmpeg_path, probe_media,
)
from i18n import translate
from watermark_repair import WATERMARK_REPAIR_TARGETS, display_dimensions


MODE_IMAGE_HIDDEN_WATERMARK = "图片隐藏水印处理"
HIDDEN_WATERMARK_TARGETS = WATERMARK_REPAIR_TARGETS
HIDDEN_WATERMARK_STRENGTHS = ["轻度处理", "标准处理", "强力处理"]

_TARGETS = {
    "PNG（无损）": (".png", "png"),
    "JPG（高质量）": (".jpg", "mjpeg"),
    "WebP（高质量）": (".webp", "libwebp"),
}
_STRENGTHS = {
    "轻度处理": (1, None),
    "标准处理": (2, "0.35"),
    "强力处理": (3, "0.65"),
}


@dataclass(frozen=True)
class HiddenWatermarkResult:
    output_path: Path
    width: int
    height: int
    locale: str = "zh_CN"

    @property
    def size_message(self) -> str:
        return translate(
            "隐藏水印处理完成 · {width}×{height} · 请自行核验",
            self.locale, width=self.width, height=self.height,
        )


def make_hidden_output_path(source: Path, options: ConversionOptions) -> Path:
    try:
        extension = _TARGETS[options.target][0]
    except KeyError as exc:
        raise ConversionError(translate(
            "不支持的图片输出格式：{target}",
            options.locale, target=options.target,
        )) from exc
    candidate = options.output_dir / f"{source.stem}_hidden_processed{extension}"
    if options.overwrite or not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = options.output_dir / f"{source.stem}_hidden_processed_{index}{extension}"
        if not candidate.exists():
            return candidate
        index += 1


def build_hidden_watermark_command(
    source: Path,
    output: Path,
    options: ConversionOptions,
    strip_metadata: bool = False,
) -> list[str]:
    try:
        _extension, encoder = _TARGETS[options.target]
    except KeyError as exc:
        raise ConversionError(translate(
            "不支持的图片输出格式：{target}",
            options.locale, target=options.target,
        )) from exc
    try:
        bits, sigma = _STRENGTHS[options.quality]
    except KeyError as exc:
        raise ConversionError(translate(
            "不支持的隐藏水印处理强度：{strength}",
            options.locale, strength=options.quality,
        )) from exc

    # The RGB LUT makes the selected low-order bit planes constant, independent
    # of their previous contents. Alpha is passed through untouched.  The mild
    # optional blur perturbs small high-frequency marks before quantization.
    divisor = 1 << bits
    lut = ":".join(
        f"{channel}=trunc(val/{divisor})*{divisor}"
        for channel in "rgb"
    )
    filters = []
    if sigma is not None:
        filters.append(f"format=gbrap,gblur=sigma={sigma}:planes=7")
    filters += ["format=rgba", f"lutrgb={lut}"]

    command = [
        str(ffmpeg_path(options.locale)),
        "-hide_banner", "-y", "-nostdin", "-stats_period", "0.5",
        "-i", str(source),
        "-map", "0:v:0", "-map_metadata", "-1" if strip_metadata else "0",
        "-vf", ",".join(filters),
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


def process_hidden_watermark(
    source: Path,
    options: ConversionOptions,
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
    strip_metadata: bool = False,
) -> HiddenWatermarkResult:
    """Reduce common low-bit marks and optionally omit copied image metadata."""
    source = source.resolve()
    if not source.is_file():
        raise ConversionError(translate("输入文件不存在。", options.locale))
    if source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ConversionError(translate("请选择受支持的图片文件。", options.locale))
    # Reject unsupported settings before creating an output directory.
    if options.target not in _TARGETS or options.quality not in _STRENGTHS:
        build_hidden_watermark_command(source, source, options, strip_metadata)

    cancel_event = cancel_event or Event()
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")
    if progress_callback:
        progress_callback(4, translate("正在分析画面…", options.locale))
    info: MediaInfo = probe_media(source, options.locale)
    if not info.video_codec or info.width <= 0 or info.height <= 0:
        raise ConversionError(translate("该文件没有可处理的画面。", options.locale))

    width, height = display_dimensions(source, info, options.locale)
    options.output_dir.mkdir(parents=True, exist_ok=True)
    output = make_hidden_output_path(source, options)
    temporary = output.with_name(
        f".{output.stem}.{uuid.uuid4().hex}.partial{output.suffix}"
    )
    try:
        command = build_hidden_watermark_command(
            source, temporary, options, strip_metadata,
        )
        if progress_callback:
            progress_callback(12, translate("正在处理隐藏水印…", options.locale))
        _run_ffmpeg(command, info, progress_callback, cancel_event, options.locale)
        if cancel_event.is_set():
            raise ConversionCancelled("任务已取消")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ConversionError(translate(
                "处理结束，但没有生成有效的输出文件。", options.locale))
        if not options.overwrite and output.exists():
            output = make_hidden_output_path(source, options)
        try:
            temporary.replace(output)
        except OSError as exc:
            raise ConversionError(translate(
                "无法保存输出文件：{error}",
                options.locale, error=exc,
            )) from exc
    finally:
        if temporary.exists():
            temporary.unlink()

    if progress_callback:
        progress_callback(100, translate("隐藏水印处理完成", options.locale))
    return HiddenWatermarkResult(output, width, height, options.locale)
