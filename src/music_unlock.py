"""Offline adapter for the bundled Unlock Music command-line helper.

This module intentionally stays separate from :mod:`engine`: the existing
FFmpeg conversion pipeline keeps its inputs, outputs and behaviour unchanged.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from engine import ConversionCancelled, ConversionError, binary_path
from i18n import translate


MODE_MUSIC_UNLOCK = "音乐文件解锁"
UNLOCK_TARGET = "自动识别原始音频格式"

# Unlock Music CLI v0.2.12 decoder registry.  The normal-looking extensions
# are used by legacy Xiami files; the helper validates their file headers, so
# an ordinary MP3/FLAC/M4A/WAV is never rewritten by this mode.
UNLOCK_SUFFIXES = frozenset({
    ".kgg", ".kgm", ".kgma", ".vpr", ".kgm.flac", ".vpr.flac",
    ".kwm", ".ncm",
    ".qmc0", ".qmc2", ".qmc3", ".qmc4", ".qmc6", ".qmc8",
    ".qmcflac", ".qmcogg", ".tkm",
    ".bkcmp3", ".bkcm4a", ".bkcflac", ".bkcwav", ".bkcape",
    ".bkcogg", ".bkcwma",
    ".666c6163", ".6d7033", ".6f6767", ".6d3461", ".776176",
    ".mmp4",
    ".mgg", ".mgg0", ".mgg1", ".mgga", ".mggh", ".mggl", ".mggm",
    ".mflac", ".mflac0", ".mflac1", ".mflaca", ".mflach",
    ".mflacl", ".mflacm",
    ".tm0", ".tm2", ".tm3", ".tm6",
    ".x2m", ".x3m", ".xm",
    ".mp3", ".wav", ".flac", ".m4a",
})

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


@dataclass(frozen=True)
class MusicUnlockResult:
    output_path: Path
    input_size: int
    output_size: int
    locale: str = "zh_CN"

    @property
    def size_message(self) -> str:
        return translate("解锁完成", self.locale)


def supported_unlock_suffix(path: Path | str) -> str | None:
    """Return the longest matching registered suffix, case-insensitively."""
    name = Path(path).name.casefold()
    for suffix in sorted(UNLOCK_SUFFIXES, key=len, reverse=True):
        if name.endswith(suffix):
            return suffix
    return None


def is_unlockable_path(path: Path | str) -> bool:
    return supported_unlock_suffix(path) is not None


def unlock_file_patterns() -> str:
    """Return a Qt file-dialog pattern list."""
    return " ".join(f"*{suffix}" for suffix in sorted(UNLOCK_SUFFIXES))


def unlocker_path(language: str = "zh_CN") -> Path:
    return binary_path("um", language)


def _unique_destination(output_dir: Path, name: str) -> Path:
    candidate = output_dir / name
    if not candidate.exists():
        return candidate
    path = Path(name)
    counter = 1
    while True:
        candidate = output_dir / f"{path.stem} ({counter}){path.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _output_bytes(folder: Path) -> int:
    total = 0
    for path in folder.rglob("*"):
        if path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                pass
    return total


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _friendly_failure(log_text: str, language: str) -> str:
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    detail = "\n".join(lines[-14:])
    lowered = detail.casefold()
    if "no suitable decoder" in lowered or "no any decoder" in lowered:
        return translate("无法识别此音乐文件，文件可能不受支持或已经是普通音频。", language)
    if "output file already exist" in lowered:
        return translate("输出文件已存在。", language)
    if not detail:
        return translate("音乐解锁组件未返回可用的错误信息。", language)
    return translate("音乐解锁失败：{message}", language, message=detail)


def unlock_music_file(
    source: Path,
    output_dir: Path,
    locale: str = "zh_CN",
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
) -> MusicUnlockResult:
    """Unlock one local file into *output_dir* without touching the source.

    The helper writes into a private staging directory first.  Only a complete,
    non-empty result is moved into the user's output directory, and an existing
    file is never overwritten.
    """
    source = source.resolve()
    if not source.is_file():
        raise ConversionError(translate("输入文件不存在。", locale))
    if not is_unlockable_path(source):
        raise ConversionError(translate("不支持的音乐文件格式：{extension}", locale,
                                         extension=source.suffix or source.name))

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cancel_event = cancel_event or Event()
    if cancel_event.is_set():
        raise ConversionCancelled("任务已取消")

    helper = unlocker_path(locale)
    source_size = source.stat().st_size
    environment = os.environ.copy()
    environment["PATH"] = str(helper.parent) + os.pathsep + environment.get("PATH", "")

    process: subprocess.Popen[bytes] | None = None
    with tempfile.TemporaryDirectory(prefix=".umt-unlock-", dir=output_dir) as stage_name:
        stage = Path(stage_name)
        with tempfile.TemporaryFile() as log_file:
            command = [
                str(helper),
                "--output", str(stage),
                "--skip-noop",
                "--input", str(source),
            ]
            try:
                process = subprocess.Popen(
                    command,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    cwd=str(helper.parent),
                    env=environment,
                    creationflags=CREATE_NO_WINDOW,
                )
            except OSError as exc:
                raise ConversionError(translate(
                    "无法启动音乐解锁组件：{error}", locale, error=exc)) from exc

            last_percent = -1
            try:
                while process.poll() is None:
                    if cancel_event.is_set():
                        raise ConversionCancelled("任务已取消")
                    written = _output_bytes(stage)
                    percent = min(96, max(2, int(written / source_size * 100))) \
                        if source_size else 2
                    if progress_callback and percent != last_percent:
                        progress_callback(percent, translate(
                            "正在解锁 {percent}%", locale, percent=percent))
                        last_percent = percent
                    time.sleep(0.1)
                return_code = process.wait()
            finally:
                _terminate_process(process)

            if cancel_event.is_set():
                raise ConversionCancelled("任务已取消")

            log_file.seek(0)
            log_text = log_file.read().decode("utf-8", errors="replace")
            if return_code != 0:
                raise ConversionError(_friendly_failure(log_text, locale))

        outputs = [path for path in stage.rglob("*") if path.is_file()]
        if len(outputs) != 1 or outputs[0].stat().st_size <= 0:
            raise ConversionError(translate(
                "解锁结束，但没有生成有效的音频文件。", locale))

        staged_output = outputs[0]
        destination = _unique_destination(output_dir, staged_output.name)
        try:
            shutil.move(str(staged_output), str(destination))
        except OSError as exc:
            raise ConversionError(translate(
                "无法保存输出文件：{error}", locale, error=exc)) from exc

    if progress_callback:
        progress_callback(100, translate("解锁完成", locale))
    return MusicUnlockResult(
        output_path=destination,
        input_size=source_size,
        output_size=destination.stat().st_size,
        locale=locale,
    )


def self_test(language: str = "zh_CN") -> tuple[bool, str]:
    """Verify that the packaged helper starts and exposes its decoder list."""
    try:
        helper = unlocker_path(language)
        version = subprocess.run(
            [str(helper), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )
        extensions = subprocess.run(
            [str(helper), "--supported-ext"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )
        version_text = version.stdout.decode("utf-8", errors="replace")
        extension_text = extensions.stdout.decode("utf-8", errors="replace")
        if version.returncode != 0 or "Unlock Music CLI" not in version_text:
            return False, translate("音乐解锁组件版本信息异常", language)
        if extensions.returncode != 0 or "ncm:" not in extension_text:
            return False, translate("音乐解锁组件格式列表异常", language)
        return True, f"Unlock Music CLI: {helper}\n{version_text.strip()}"
    except Exception as exc:
        return False, str(exc)
