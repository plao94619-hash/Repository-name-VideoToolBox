import subprocess
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from engine import (
    ConversionCancelled,
    ConversionError,
    ConversionOptions,
    MODE_AUDIO,
    build_command,
    convert_file,
    ffmpeg_path,
    ffprobe_path,
    probe_media,
)


class FFmpegIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.ffmpeg = str(ffmpeg_path())
            ffprobe_path()
        except ConversionError:
            raise unittest.SkipTest("FFmpeg and FFprobe are not yet installed")

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / "tone.wav"
        subprocess.run(
            [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=0.5",
             "-c:a", "pcm_s16le", str(self.source)],
            check=True, capture_output=True, timeout=30,
        )
        self.options = ConversionOptions(
            mode=MODE_AUDIO, target="FLAC", quality="均衡压缩",
            encoder="自动选择", resolution="保持原分辨率",
            output_dir=self.root,
        )

    def test_real_conversion_is_playable_and_complete(self):
        events = []
        result = convert_file(self.source, self.options,
                              lambda percent, message: events.append(percent))
        self.assertTrue(result.output_path.is_file())
        self.assertEqual(probe_media(result.output_path).audio_codec, "flac")
        self.assertEqual(events[-1], 100)
        self.assertEqual(list(self.root.glob(".*.partial.flac")), [])

    def test_failed_conversion_keeps_previous_file_and_cleans_partial(self):
        previous = self.root / "tone_converted.flac"
        previous.write_bytes(b"existing output")
        original = build_command

        def invalid_audio_codec(source, output, options, info):
            command = original(source, output, options, info)
            command[command.index("-c:a") + 1] = "nonexistent_encoder"
            return command

        with patch("engine.build_command", side_effect=invalid_audio_codec):
            with self.assertRaises(ConversionError):
                convert_file(self.source, self.options)
        self.assertEqual(previous.read_bytes(), b"existing output")
        self.assertFalse((self.root / "tone_converted_2.flac").exists())
        self.assertEqual(list(self.root.glob(".*.partial.flac")), [])

    def test_cancellation_before_start_leaves_no_output(self):
        cancel = Event()
        cancel.set()
        with self.assertRaises(ConversionCancelled):
            convert_file(self.source, self.options, cancel_event=cancel)
        self.assertEqual(list(self.root.glob("*.flac")), [])
        self.assertEqual(list(self.root.glob(".*.partial.flac")), [])
