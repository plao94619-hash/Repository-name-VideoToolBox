"""Conservative downloader for authorized, non-DRM audio file URLs.

This module intentionally supports direct HTTP(S) files only.  It does not
accept streaming-service pages, credentials, cookies, HLS/DASH manifests, or
encrypted media.  Keeping this boundary here (rather than only in the UI)
makes it much harder for a future presentation change to weaken the policy.
"""

from __future__ import annotations

import os
import re
import socket
import uuid
from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from threading import Event
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from i18n import translate


MODE_DIRECT_DOWNLOAD = "授权音频下载"
DIRECT_TARGET = "保留原始音频格式"

AUDIO_SUFFIXES = {
    ".aac", ".aif", ".aiff", ".alac", ".amr", ".ape", ".flac",
    ".m4a", ".mka", ".mp3", ".oga", ".ogg", ".opus", ".wav", ".wma",
}
MANIFEST_SUFFIXES = {".m3u", ".m3u8", ".mpd", ".ism", ".ismv"}
BLOCKED_HOST_SUFFIXES = {
    "spotify.com", "spotify.link", "spoti.fi", "scdn.co", "spotifycdn.com",
    "music.apple.com", "itunes.apple.com", "applemusic.com", "mzstatic.com",
}
MANIFEST_CONTENT_TYPES = {
    "application/dash+xml",
    "application/mpegurl",
    "application/vnd.apple.mpegurl",
    "application/x-mpegurl",
    "audio/mpegurl",
    "audio/x-mpegurl",
}
GENERIC_CONTENT_TYPES = {
    "", "application/octet-stream", "binary/octet-stream", "application/download",
    "application/ogg", "application/x-flac", "application/mp4", "video/mp4",
}
CONTENT_TYPE_SUFFIXES = {
    "audio/aac": ".aac",
    "audio/aiff": ".aiff",
    "audio/flac": ".flac",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
    "audio/wav": ".wav",
    "audio/x-aiff": ".aiff",
    "audio/x-flac": ".flac",
    "audio/x-m4a": ".m4a",
    "audio/x-ms-wma": ".wma",
    "audio/x-wav": ".wav",
}
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class DirectDownloadError(RuntimeError):
    """A user-facing direct-download failure."""


class DirectDownloadCancelled(DirectDownloadError):
    """Raised when the user cancels a direct download."""


class _SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, locale: str):
        super().__init__()
        self.locale = locale

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl, self.locale)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass(frozen=True)
class DirectDownloadTask:
    url: str
    display_name: str
    source_label: str
    suffix_label: str


@dataclass(frozen=True)
class DirectDownloadResult:
    output_path: Path
    output_size: int
    locale: str = "zh_CN"

    @property
    def size_message(self) -> str:
        return translate("下载完成", self.locale)


def _host_is_blocked(host: str) -> bool:
    host = host.casefold().rstrip(".")
    return any(host == item or host.endswith(f".{item}")
               for item in BLOCKED_HOST_SUFFIXES)


def _validate_url(raw_url: str, locale: str) -> tuple[str, object]:
    url = raw_url.strip()
    if not url or len(url) > 8192:
        raise DirectDownloadError(translate("请输入有效的音频直链。", locale))
    parsed = urlsplit(url)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise DirectDownloadError(translate("仅支持 HTTP 或 HTTPS 音频直链。", locale))
    if parsed.username or parsed.password:
        raise DirectDownloadError(translate("下载地址不能包含账号或密码。", locale))
    if _host_is_blocked(parsed.hostname):
        raise DirectDownloadError(translate(
            "不支持 Spotify 或 Apple Music 链接；请使用官方应用离线播放。", locale))
    suffix = Path(unquote(parsed.path)).suffix.casefold()
    if suffix in MANIFEST_SUFFIXES:
        raise DirectDownloadError(translate(
            "不支持 M3U8、DASH 或其他流媒体播放清单。", locale))
    if suffix and suffix not in AUDIO_SUFFIXES:
        raise DirectDownloadError(translate(
            "该链接不是受支持的音频文件直链。", locale))
    return url, parsed


def split_url_input(text: str) -> list[str]:
    """Split a pasted list without trying to interpret platform pages."""
    return [part.strip() for part in re.split(r"\s+", text.strip()) if part.strip()]


def _safe_filename(name: str) -> str:
    name = Path(unquote(name)).name
    name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "_", name).strip(" .")
    if not name:
        return "downloaded_audio"
    path = Path(name)
    if path.stem.upper() in WINDOWS_RESERVED_NAMES:
        name = f"_{name}"
        path = Path(name)
    if len(name) > 180:
        available = max(1, 180 - len(path.suffix))
        name = f"{path.stem[:available]}{path.suffix}"
    return name


def _source_label(parsed: object) -> str:
    host = str(getattr(parsed, "hostname", "") or "")
    path = unquote(str(getattr(parsed, "path", "") or ""))
    leaf = Path(path).name
    return f"{host} / {leaf}" if leaf else host


def download_source_label(raw_url: str, locale: str = "zh_CN") -> str:
    """Return a display-safe URL label with credentials/query/fragment removed."""
    try:
        parsed = urlsplit(raw_url.strip())
    except ValueError:
        return translate("无效链接", locale)
    return _source_label(parsed) or translate("无效链接", locale)


def make_download_task(raw_url: str, locale: str = "zh_CN") -> DirectDownloadTask:
    url, parsed = _validate_url(raw_url, locale)
    leaf = _safe_filename(Path(unquote(parsed.path)).name)
    suffix = Path(leaf).suffix.casefold()
    display_name = leaf if suffix in AUDIO_SUFFIXES else _source_label(parsed)
    return DirectDownloadTask(
        url=url,
        display_name=display_name,
        source_label=_source_label(parsed),
        suffix_label=suffix.lstrip(".").upper() if suffix else "AUDIO",
    )


def _content_disposition_name(value: str) -> str:
    if not value:
        return ""
    message = Message()
    message["content-disposition"] = value
    return str(message.get_filename() or "")


def _unique_destination(output_dir: Path, name: str) -> Path:
    candidate = output_dir / name
    if not candidate.exists():
        return candidate
    path = Path(name)
    for counter in range(1, 100_000):
        candidate = output_dir / f"{path.stem} ({counter}){path.suffix}"
        if not candidate.exists():
            return candidate
    raise DirectDownloadError("Too many files with the same name.")


def _readable_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _looks_protected_or_streaming(path: Path) -> str | None:
    with path.open("rb") as handle:
        sample = handle.read(2 * 1024 * 1024)
    stripped = sample.lstrip().lower()
    if stripped.startswith(b"#extm3u") or b"<mpd" in stripped[:16_384]:
        return "manifest"
    # Common ISO-BMFF protection markers.  This is intentionally conservative:
    # direct encrypted containers are not a supported input even if a key is
    # supplied elsewhere.
    if any(marker in sample for marker in (b"pssh", b"sinf", b"encv", b"enca", b"skd://")):
        return "protected"
    return None


def _response_filename(response: object, task: DirectDownloadTask,
                       content_type: str, locale: str) -> str:
    headers = response.headers
    disposition_name = _content_disposition_name(
        str(headers.get("Content-Disposition", "")))
    final_url, parsed = _validate_url(str(response.geturl()), locale)
    del final_url
    candidates = (
        disposition_name,
        Path(unquote(parsed.path)).name,
        task.display_name,
    )
    name = next((_safe_filename(item) for item in candidates if item),
                "downloaded_audio")
    suffix = Path(name).suffix.casefold()
    if suffix not in AUDIO_SUFFIXES:
        mapped = CONTENT_TYPE_SUFFIXES.get(content_type)
        if not mapped:
            raise DirectDownloadError(translate(
                "服务器未提供可识别的音频文件格式。", locale))
        name = f"{Path(name).stem or 'downloaded_audio'}{mapped}"
    return _safe_filename(name)


def download_direct_audio(
    task: DirectDownloadTask,
    output_dir: Path,
    locale: str = "zh_CN",
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
) -> DirectDownloadResult:
    """Download one authorized direct audio file without cookies or auth state."""
    _validate_url(task.url, locale)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cancel_event = cancel_event or Event()
    if cancel_event.is_set():
        raise DirectDownloadCancelled(translate("已取消", locale))

    request = Request(
        task.url,
        headers={
            "User-Agent": "Universal-Media-Toolbox/1.7",
            "Accept": "audio/*, application/octet-stream;q=0.8, */*;q=0.1",
        },
        method="GET",
    )
    temporary = output_dir / f".umt-download-{uuid.uuid4().hex}.part"
    destination: Path | None = None
    try:
        try:
            response_context = build_opener(
                _SafeRedirectHandler(locale)).open(request, timeout=30)
        except HTTPError as exc:
            raise DirectDownloadError(translate(
                "服务器返回 HTTP {code}。", locale, code=exc.code)) from exc
        except (URLError, TimeoutError, socket.timeout) as exc:
            reason = getattr(exc, "reason", exc)
            raise DirectDownloadError(translate(
                "无法连接到下载地址：{error}", locale, error=reason)) from exc

        with response_context as response:
            _validate_url(str(response.geturl()), locale)
            content_type = str(response.headers.get_content_type() or "").casefold()
            if content_type in MANIFEST_CONTENT_TYPES:
                raise DirectDownloadError(translate(
                    "不支持 M3U8、DASH 或其他流媒体播放清单。", locale))
            filename = _response_filename(response, task, content_type, locale)
            suffix = Path(filename).suffix.casefold()
            if not content_type.startswith("audio/") and content_type not in GENERIC_CONTENT_TYPES:
                raise DirectDownloadError(translate(
                    "服务器返回的内容不是音频文件。", locale))
            if suffix not in AUDIO_SUFFIXES:
                raise DirectDownloadError(translate(
                    "该链接不是受支持的音频文件直链。", locale))

            destination = _unique_destination(output_dir, filename)
            try:
                total = int(response.headers.get("Content-Length", "0") or 0)
            except ValueError:
                total = 0
            downloaded = 0
            with temporary.open("xb") as output:
                while True:
                    if cancel_event.is_set():
                        raise DirectDownloadCancelled(translate("已取消", locale))
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        if total > 0:
                            percent = min(99, int(downloaded / total * 100))
                            message = translate(
                                "正在下载 {percent}%", locale, percent=percent)
                        else:
                            percent = -1
                            message = translate(
                                "已下载 {size}", locale, size=_readable_size(downloaded))
                        progress_callback(percent, message)

        if cancel_event.is_set():
            raise DirectDownloadCancelled(translate("已取消", locale))
        if not temporary.exists() or temporary.stat().st_size <= 0:
            raise DirectDownloadError(translate(
                "下载结束，但没有生成有效的音频文件。", locale))
        detected = _looks_protected_or_streaming(temporary)
        if detected == "manifest":
            raise DirectDownloadError(translate(
                "检测到流媒体播放清单，已停止下载。", locale))
        if detected == "protected":
            raise DirectDownloadError(translate(
                "检测到加密或受保护的媒体，已停止下载。", locale))

        os.replace(temporary, destination)
        if progress_callback:
            progress_callback(100, translate("下载完成", locale))
        return DirectDownloadResult(
            output_path=destination,
            output_size=destination.stat().st_size,
            locale=locale,
        )
    except DirectDownloadError:
        raise
    except OSError as exc:
        raise DirectDownloadError(translate(
            "无法保存输出文件：{error}", locale, error=exc)) from exc
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
