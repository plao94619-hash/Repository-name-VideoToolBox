"""Tests for the isolated Unlock Music CLI adapter."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from engine import ConversionCancelled, ConversionError
from music_unlock import (
    is_unlockable_path,
    supported_unlock_suffix,
    unlock_file_patterns,
    unlock_music_file,
)


class _CompletedHelper:
    def __init__(self, command, *, stdout, **_kwargs):
        self.command = command
        self.returncode = 0
        stage = Path(command[command.index("--output") + 1])
        source = Path(command[command.index("--input") + 1])
        (stage / f"{source.stem}.flac").write_bytes(b"fLaC" + b"audio" * 30)
        stdout.write(b"successfully converted\n")
        stdout.flush()

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9


class _FailedHelper(_CompletedHelper):
    def __init__(self, command, *, stdout, **_kwargs):
        self.command = command
        self.returncode = 1
        stdout.write(b"run app failed: no any decoder can resolve the file\n")
        stdout.flush()


class MusicUnlockTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.helper = self.root / "um.exe"

    def test_registry_matches_long_suffixes_and_dialog_patterns(self):
        self.assertTrue(is_unlockable_path("SONG.NCM"))
        self.assertTrue(is_unlockable_path("song.mflac0"))
        self.assertEqual(supported_unlock_suffix("song.kgm.flac"), ".kgm.flac")
        self.assertFalse(is_unlockable_path("video.mp4"))
        patterns = unlock_file_patterns()
        self.assertIn("*.ncm", patterns)
        self.assertIn("*.qmcflac", patterns)
        self.assertIn("*.x2m", patterns)

    def test_completed_file_is_published_without_overwriting_or_deleting_source(self):
        source = self.root / "track.ncm"
        source.write_bytes(b"encrypted music")
        output_dir = self.root / "output"
        output_dir.mkdir()
        existing = output_dir / "track.flac"
        existing.write_bytes(b"keep me")
        progress = []

        with patch("music_unlock.unlocker_path", return_value=self.helper), \
                patch("music_unlock.subprocess.Popen", _CompletedHelper):
            result = unlock_music_file(
                source,
                output_dir,
                "en_US",
                lambda percent, text: progress.append((percent, text)),
            )

        self.assertTrue(source.exists())
        self.assertEqual(existing.read_bytes(), b"keep me")
        self.assertEqual(result.output_path.name, "track (1).flac")
        self.assertTrue(result.output_path.read_bytes().startswith(b"fLaC"))
        self.assertEqual(result.size_message, "Unlocked")
        self.assertEqual(progress[-1], (100, "Unlocked"))
        self.assertFalse(any(path.name.startswith(".umt-unlock-")
                             for path in output_dir.iterdir()))

    def test_helper_failure_is_localized_and_staging_is_cleaned(self):
        source = self.root / "broken.ncm"
        source.write_bytes(b"not really encrypted")
        output_dir = self.root / "output"

        with patch("music_unlock.unlocker_path", return_value=self.helper), \
                patch("music_unlock.subprocess.Popen", _FailedHelper):
            with self.assertRaisesRegex(ConversionError, "could not be recognized"):
                unlock_music_file(source, output_dir, "en_US")

        self.assertTrue(source.exists())
        self.assertEqual(list(output_dir.iterdir()), [])

    def test_cancel_before_start_never_launches_helper(self):
        source = self.root / "track.ncm"
        source.write_bytes(b"encrypted music")
        cancelled = Event()
        cancelled.set()

        with patch("music_unlock.subprocess.Popen") as popen:
            with self.assertRaises(ConversionCancelled):
                unlock_music_file(source, self.root / "output", cancel_event=cancelled)
        popen.assert_not_called()

    def test_unsupported_extension_is_rejected_before_helper_launch(self):
        source = self.root / "video.mp4"
        source.write_bytes(b"video")
        with patch("music_unlock.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ConversionError, "不支持的音乐文件格式"):
                unlock_music_file(source, self.root / "output")
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
