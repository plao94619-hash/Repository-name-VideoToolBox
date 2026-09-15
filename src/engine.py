from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from threading import Event
from typing import Callable


CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv", ".m4v",
    ".ts", ".mts", ".m2ts", ".3gp", ".vob", ".mpg", ".mpeg",
}
AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".opus", ".wma",
    ".ac3", ".eac3", ".mka", ".aiff", ".ape", ".amr",
}
SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

MODE_VIDEO = "视频格式转换"
MODE_AUDIO = "音频格式转换"
MODE_EXTRACT = "视频提取音频"
MODE_COMPRESS = "视频压缩"

RAW_AUDIO = "原始音轨（无损提取）"

VIDEO_TARGETS = ["MP4", "MKV", "MOV", "WebM", "AVI"]
AUDIO_TARGETS = ["MP3", "M4A", "AAC", "FLAC", "WAV", "OGG", "OPUS"]
EXTRACT_TARGETS = [RAW_AUDIO, "FLAC", "WAV", "MP3", "M4A", "AAC", "OGG", "OPUS"]
COMPRESS_TARGETS = ["MP4", "MKV", "WebM"]

QUALITY_PRESETS = ["画质优先", "均衡压缩", "极限压缩"]
RESOLUTION_PRESETS = ["保持原分辨率", "最高 4K", "最高 1080p", "最高 720p", "最高 480p"]
ENCODER_PRESETS = [
    "自动选择",
    "H.264（兼容优先）",
    "H.265 / HEVC（高压缩）",
    "AV1（压缩率最高，速度慢）",
]

TARGET_EXTENSION = {
    "MP4": ".mp4",
    "MKV": ".mkv",
    "MOV": ".mov",
    "WebM": ".webm",
    "AVI": ".avi",
    "MP3": ".mp3",
    "M4A": ".m4a",
    "AAC": ".aac",
    "FLAC": ".flac",
    "WAV": ".wav",
    "OGG": ".ogg",
    "OPUS": ".opus",
}

AUDIO_CODEC_EXTENSION = {
    "aac": ".m4a",
    "alac": ".m4a",
    "mp3": ".mp3",
    "flac": ".flac",
    "vorbis": ".ogg",
    "opus": ".opus",
    "pcm_s16le": ".wav",
    "pcm_s24le": ".wav",
    "pcm_s32le": ".wav",
    "pcm_f32le": ".wav",
    "ac3": ".ac3",
    "eac3": ".eac3",
    "dts": ".dts",
    "truehd": ".mka",
}


class ConversionError(RuntimeError):
    pass


class ConversionCancelled(RuntimeError):
    pass


@dataclass(frozen=True)
class ConversionOptions:
    mode: str
    target: str
    quality: str
    encoder: str
    resolution: str
    output_dir: Path
    overwrite: bool = False


@dataclass
class MediaInfo:
    duration: float
    video_codec: str = ""
    audio_codec: str = ""
    width: int = 0
    height: int = 0
    size: int = 0
    video_stream_index: int | None = None
    audio_stream_index: int | None = None

    @property
    def summary(self) -> str:
        parts: list[str] = []
        if self.video_codec:
            dimensions = f"{self.width}×{self.height}" if self.width and self.height else ""
            parts.append(" ".join(x for x in [self.video_codec.upper(), dimensions] if x))
        if self.audio_codec:
            parts.append(self.audio_codec.upper())
        if self.duration:
            seconds = int(self.duration)
            parts.append(f"{seconds // 60:02d}:{seconds % 60:02d}")
        return " / ".join(parts) or "媒体文件"


@dataclass
class ConversionResult:
    output_path: Path
    input_size: int
    output_size: int

    @property
    def size_message(self) -> str:
        if self.input_size <= 0:
            return "已完成"
        ratio = self.output_size / self.input_size
        if ratio < 1:
            return f"已完成，体积减少 {(1 - ratio) * 100:.1f}%"
        return f"已完成，输出为原文件的 {ratio * 100:.1f}%"


def _runtime_root() -> Path:
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled)
    return Path(__file__).resolve().parents[1]


def binary_path(name: str) -> Path:
    executable = f"{name}.exe" if os.name == "nt" else name
    candidates = [
        _runtime_root() / "tools" / executable,
        Path(sys.executable).resolve().parent / "tools" / executable,
        Path(__file__).resolve().parents[1] / "tools" / executable,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    found = shutil.which(executable) or shutil.which(name)
    if found:
        return Path(found)
    raise ConversionError(f"没有找到 {executable}。请重新安装软件或检查程序文件是否完整。")


def ffmpeg_path() -> Path:
    return binary_path("ffmpeg")


def ffprobe_path() -> Path:
    return binary_path("ffprobe")


def _run_capture(command: list[str], timeout: int = 30) -> str:
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConversionError(str(exc)) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ConversionError(detail[-1500:] or "外部程序执行失败")
    return completed.stdout or completed.stderr


def probe_media(path: Path) -> MediaInfo:
    command = [
        str(ffprobe_path()),
        "-v", "error",
        "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height:"
        "stream_disposition=attached_pic",
        "-of", "json",
        str(path),
    ]
    try:
        data = json.loads(_run_capture(command))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ConversionError(f"无法读取媒体信息：{path.name}") from exc

    format_info = data.get("format") or {}
    try:
        duration = float(format_info.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    try:
        size = int(format_info.get("size") or path.stat().st_size)
    except (TypeError, ValueError, OSError):
        size = 0

    info = MediaInfo(duration=duration, size=size)
    for stream in data.get("streams") or []:
        kind = stream.get("codec_type")
        if (
            kind == "video"
            and not info.video_codec
            and not (stream.get("disposition") or {}).get("attached_pic")
        ):
            info.video_codec = str(stream.get("codec_name") or "")
            info.width = int(stream.get("width") or 0)
            info.height = int(stream.get("height") or 0)
            if stream.get("index") is not None:
                info.video_stream_index = int(stream["index"])
        elif kind == "audio" and not info.audio_codec:
            info.audio_codec = str(stream.get("codec_name") or "")
            if stream.get("index") is not None:
                info.audio_stream_index = int(stream["index"])
    return info


def encoder_names() -> set[str]:
    output = _run_capture([str(ffmpeg_path()), "-hide_banner", "-encoders"], timeout=30)
    names: set[str] = set()
    for line in output.splitlines():
        match = re.match(r"^\s*[VAS][A-Z\.]{5}\s+(\S+)", line)
        if match:
            names.add(match.group(1))
    return names


_HARDWARE_CACHE: dict[str, bool] = {}


def hardware_encoder_works(encoder: str) -> bool:
    if encoder in _HARDWARE_CACHE:
        return _HARDWARE_CACHE[encoder]
    command = [
        str(ffmpeg_path()), "-hide_banner", "-loglevel", "error", "-nostdin",
        "-f", "lavfi", "-i", "color=size=128x128:rate=1",
        "-frames:v", "1", "-an", "-c:v", encoder, "-f", "null", "-",
    ]
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=12,
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )
        result = completed.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        result = False
    _HARDWARE_CACHE[encoder] = result
    return result


def _available(names: set[str], *candidates: str) -> str | None:
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _working_hardware(names: set[str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in names and hardware_encoder_works(candidate):
            return candidate
    return None


def choose_video_encoder(options: ConversionOptions, target: str) -> str:
    names = encoder_names()

    if target == "WebM":
        if options.encoder.startswith("AV1"):
            return _available(names, "libsvtav1", "libaom-av1") or "libvpx-vp9"
        return _available(names, "libvpx-vp9", "libsvtav1") or "libvpx-vp9"

    if target == "AVI":
        return "mpeg4"

    requested = options.encoder
    if requested.startswith("H.264"):
        return "libx264"
    if requested.startswith("H.265"):
        return "libx265"
    if requested.startswith("AV1"):
        return _available(names, "libsvtav1", "libaom-av1") or "libx265"

    if options.mode == MODE_VIDEO:
        return (
            _working_hardware(names, ("h264_nvenc", "h264_qsv", "h264_amf"))
            or _available(names, "libx264")
            or "libx264"
        )

    if options.quality == "极限压缩":
        return _available(names, "libsvtav1", "libx265", "libx264") or "libx264"

    return (
        _working_hardware(names, ("hevc_nvenc", "hevc_qsv", "hevc_amf"))
        or _working_hardware(names, ("h264_nvenc", "h264_qsv", "h264_amf"))
        or _available(names, "libx265", "libx264")
        or "libx264"
    )


def _video_quality_args(encoder: str, quality: str) -> list[str]:
    quality_index = {"画质优先": 0, "均衡压缩": 1, "极限压缩": 2}.get(quality, 1)

    if encoder == "libx264":
        return ["-preset", ["slow", "medium", "slow"][quality_index],
                "-crf", str([18, 23, 29][quality_index])]
    if encoder == "libx265":
        return ["-preset", ["slow", "medium", "slow"][quality_index],
                "-crf", str([20, 26, 32][quality_index]), "-tag:v", "hvc1"]
    if encoder in {"libsvtav1", "libaom-av1"}:
        crf = [24, 32, 40][quality_index]
        speed = ["5", "7", "8"][quality_index]
        if encoder == "libsvtav1":
            return ["-preset", speed, "-crf", str(crf)]
        return ["-cpu-used", speed, "-crf", str(crf), "-b:v", "0"]
    if encoder.endswith("_nvenc"):
        return ["-preset", ["p7", "p5", "p6"][quality_index], "-rc", "vbr",
                "-cq", str([18, 23, 29][quality_index]), "-b:v", "0"]
    if encoder.endswith("_qsv"):
        return ["-global_quality", str([18, 23, 29][quality_index])]
    if encoder.endswith("_amf"):
        qp = [18, 23, 29][quality_index]
        return ["-quality", ["quality", "balanced", "speed"][quality_index],
                "-rc", "cqp", "-qp_i", str(qp), "-qp_p", str(qp)]
    if encoder == "libvpx-vp9":
        return ["-deadline", "good", "-cpu-used", "2",
                "-crf", str([22, 31, 39][quality_index]), "-b:v", "0"]
    if encoder == "mpeg4":
        return ["-q:v", str([2, 4, 7][quality_index])]
    return []


def _scale_args(resolution: str) -> list[str]:
    limits = {
        "最高 4K": (3840, 2160),
        "最高 1080p": (1920, 1080),
        "最高 720p": (1280, 720),
        "最高 480p": (854, 480),
    }
    if resolution not in limits:
        return []
    width, height = limits[resolution]
    expression = (
        f"scale=w='min(iw,{width})':h='min(ih,{height})':"
        "force_original_aspect_ratio=decrease:force_divisible_by=2"
    )
    return ["-vf", expression]


def _audio_codec_args(target: str, quality: str = "均衡压缩") -> list[str]:
    high = quality == "画质优先"
    compact = quality == "极限压缩"
    if target == "MP3":
        return ["-c:a", "libmp3lame", "-b:a", "320k" if high else ("128k" if compact else "192k")]
    if target in {"M4A", "AAC"}:
        return ["-c:a", "aac", "-b:a", "320k" if high else ("128k" if compact else "192k")]
    if target == "FLAC":
        return ["-c:a", "flac", "-compression_level", "12" if compact else "8"]
    if target == "WAV":
        return ["-c:a", "pcm_s24le"]
    if target == "OGG":
        return ["-c:a", "libvorbis", "-q:a", "8" if high else ("3" if compact else "6")]
    if target == "OPUS":
        return ["-c:a", "libopus", "-b:a", "256k" if high else ("96k" if compact else "160k"), "-vbr", "on"]
    raise ConversionError(f"不支持的音频输出格式：{target}")


def raw_audio_extension(codec: str) -> str:
    return AUDIO_CODEC_EXTENSION.get(codec.lower(), ".mka")


def make_output_path(source: Path, options: ConversionOptions, info: MediaInfo) -> Path:
    if options.mode == MODE_EXTRACT and options.target == RAW_AUDIO:
        extension = raw_audio_extension(info.audio_codec)
        suffix = "_audio"
    else:
        extension = TARGET_EXTENSION.get(options.target)
        if not extension:
            raise ConversionError(f"不支持的输出格式：{options.target}")
        suffix = {
            MODE_VIDEO: "_converted",
            MODE_AUDIO: "_converted",
            MODE_EXTRACT: "_audio",
            MODE_COMPRESS: "_compressed",
        }.get(options.mode, "_output")

    base = options.output_dir / f"{source.stem}{suffix}{extension}"
    if options.overwrite or not base.exists():
        return base
    index = 2
    while True:
        candidate = options.output_dir / f"{source.stem}{suffix}_{index}{extension}"
        if not candidate.exists():
            return candidate
        index += 1


def build_command(source: Path, output: Path, options: ConversionOptions, info: MediaInfo) -> list[str]:
    command = [
        str(ffmpeg_path()), "-hide_banner", "-y", "-nostdin",
        "-stats_period", "0.5", "-i", str(source),
    ]

    if options.mode == MODE_EXTRACT:
        if not info.audio_codec:
            raise ConversionError("该文件没有可提取的音轨。")
        audio_map = (
            f"0:{info.audio_stream_index}"
            if info.audio_stream_index is not None else "0:a:0"
        )
        command += ["-map", audio_map, "-vn", "-map_metadata", "0"]
        command += ["-c:a", "copy"] if options.target == RAW_AUDIO else _audio_codec_args(
            options.target, options.quality
        )

    elif options.mode == MODE_AUDIO:
        if not info.audio_codec:
            raise ConversionError("该文件没有可转换的音轨。")
        audio_map = (
            f"0:{info.audio_stream_index}"
            if info.audio_stream_index is not None else "0:a:0"
        )
        command += ["-map", audio_map, "-vn", "-map_metadata", "0"]
        command += _audio_codec_args(options.target, options.quality)

    elif options.mode in {MODE_VIDEO, MODE_COMPRESS}:
        if not info.video_codec:
            raise ConversionError("该文件没有视频画面。")
        encoder = choose_video_encoder(options, options.target)
        video_map = (
            f"0:{info.video_stream_index}"
            if info.video_stream_index is not None else "0:v:0"
        )
        command += ["-map", video_map, "-map", "0:a?", "-map_metadata", "0", "-map_chapters", "0"]
        command += ["-c:v", encoder]
        command += _video_quality_args(encoder, options.quality)
        command += _scale_args(options.resolution)
        if encoder != "libsvtav1" and encoder != "libaom-av1":
            command += ["-pix_fmt", "yuv420p"]

        if options.target == "WebM":
            command += ["-c:a", "libopus", "-b:a", "160k"]
        elif options.target == "AVI":
            command += ["-c:a", "libmp3lame", "-b:a", "192k"]
        else:
            command += ["-c:a", "aac", "-b:a", "192k"]
            if options.target == "MP4":
                command += ["-movflags", "+faststart"]

    else:
        raise ConversionError(f"未知任务类型：{options.mode}")

    command += ["-progress", "pipe:1", "-nostats", str(output)]
    return command


def _run_ffmpeg(
    command: list[str],
    info: MediaInfo,
    progress_callback: Callable[[int, str], None] | None,
    cancel_event: Event,
) -> None:
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=CREATE_NO_WINDOW,
        )
    except OSError as exc:
        raise ConversionError(f"无法启动 FFmpeg：{exc}") from exc

    recent_lines: list[str] = []
    try:
        assert process.stdout is not None
        for raw_line in process.stdout:
            if cancel_event.is_set():
                raise ConversionCancelled("任务已取消")

            line = raw_line.strip()
            if line:
                recent_lines.append(line)
                recent_lines = recent_lines[-30:]

            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in {"out_time_us", "out_time_ms"}:
                try:
                    elapsed = int(value) / 1_000_000
                    percent = int(min(99, max(0, elapsed / info.duration * 100))) if info.duration else 0
                    if progress_callback:
                        progress_callback(percent, f"正在处理 {percent}%")
                except (ValueError, ZeroDivisionError):
                    pass
            elif key == "speed" and progress_callback:
                progress_callback(-1, f"处理速度 {value}")
        return_code = process.wait()
        if cancel_event.is_set():
            raise ConversionCancelled("任务已取消")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if process.stdout:
            process.stdout.close()

    if return_code != 0:
        detail = "\n".join(recent_lines[-12:])
        raise ConversionError(detail or f"FFmpeg 返回错误代码 {return_code}")

def convert_file(
    source: Path,
    options: ConversionOptions,
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
) -> ConversionResult:
    source = source.resolve()
    if not source.is_file():
        raise ConversionError("输入文件不存在。")
    options.output_dir.mkdir(parents=True, exist_ok=True)
    cancel_event = cancel_event or Event()
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")

    info = probe_media(source)
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")
    output = make_output_path(source, options, info)
    # Keep the real extension so FFmpeg selects the right muxer. Publish only
    # after the entire file is successfully encoded.
    temporary = output.with_name(f".{output.stem}.{uuid.uuid4().hex}.partial{output.suffix}")
    command = build_command(source, temporary, options, info)
    encoder = command[command.index("-c:v") + 1] if "-c:v" in command else ""

    try:
        try:
            _run_ffmpeg(command, info, progress_callback, cancel_event)
        except ConversionError:
            if options.encoder != "自动选择" or not encoder.endswith(("_nvenc", "_qsv", "_amf")):
                raise
            _HARDWARE_CACHE[encoder] = False
            fallback = "H.265 / HEVC（高压缩）" if encoder.startswith("hevc_") else "H.264（兼容优先）"
            cpu_command = build_command(
                source, temporary, replace(options, encoder=fallback), info
            )
            if temporary.exists():
                temporary.unlink()
            if progress_callback:
                progress_callback(0, "硬件编码失败，已切换 CPU 重试")
            _run_ffmpeg(cpu_command, info, progress_callback, cancel_event)

        if cancel_event.is_set():
            raise ConversionCancelled("任务已取消")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ConversionError("转换结束，但没有生成有效的输出文件。")
        if not options.overwrite and output.exists():
            output = make_output_path(source, options, info)
        try:
            temporary.replace(output)
        except OSError as exc:
            raise ConversionError(f"无法保存输出文件：{exc}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()

    if progress_callback:
        progress_callback(100, "处理完成")
    return ConversionResult(
        output_path=output,
        input_size=info.size or source.stat().st_size,
        output_size=output.stat().st_size,
    )


def self_test() -> tuple[bool, str]:
    try:
        ffmpeg = ffmpeg_path()
        ffprobe = ffprobe_path()
        ffmpeg_text = _run_capture([str(ffmpeg), "-version"])
        probe_text = _run_capture([str(ffprobe), "-version"])
        if "ffmpeg version" not in ffmpeg_text.lower() or "ffprobe version" not in probe_text.lower():
            return False, "FFmpeg 或 FFprobe 版本信息异常"
        return True, f"FFmpeg: {ffmpeg}\nFFprobe: {ffprobe}"
    except Exception as exc:
        return False, str(exc)
