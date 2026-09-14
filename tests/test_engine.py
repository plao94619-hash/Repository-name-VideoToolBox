import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine import (
    ConversionOptions,
    MediaInfo,
    MODE_COMPRESS,
    MODE_EXTRACT,
    RAW_AUDIO,
    build_command,
    make_output_path,
    raw_audio_extension,
)


class EngineTests(unittest.TestCase):
    def make_options(self, root: Path, mode: str, target: str) -> ConversionOptions:
        return ConversionOptions(
            mode=mode,
            target=target,
            quality="均衡压缩",
            encoder="自动选择",
            resolution="保持原分辨率",
            output_dir=root,
        )

    def test_raw_audio_extension(self):
        self.assertEqual(raw_audio_extension("aac"), ".m4a")
        self.assertEqual(raw_audio_extension("opus"), ".opus")
        self.assertEqual(raw_audio_extension("unknown_codec"), ".mka")

    def test_lossless_extraction_output_name(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "sample.video.mkv"
            source.touch()
            options = self.make_options(root, MODE_EXTRACT, RAW_AUDIO)
            result = make_output_path(
                source,
                options,
                MediaInfo(duration=1, audio_codec="aac"),
            )
            self.assertEqual(result.name, "sample.video_audio.m4a")

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "movie.mkv"
            source.touch()
            (root / "movie_compressed.mp4").touch()
            options = self.make_options(root, MODE_COMPRESS, "MP4")
            result = make_output_path(
                source,
                options,
                MediaInfo(duration=1, video_codec="h264"),
            )
            self.assertEqual(result.name, "movie_compressed_2.mp4")

    @patch("engine.ffmpeg_path", return_value=Path("ffmpeg.exe"))
    def test_lossless_extraction_uses_stream_copy(self, _mock_ffmpeg):
        source = Path("input.mkv")
        output = Path("output.m4a")
        options = self.make_options(Path("."), MODE_EXTRACT, RAW_AUDIO)
        command = build_command(
            source,
            output,
            options,
            MediaInfo(duration=60, audio_codec="aac"),
        )
        self.assertIn("copy", command)
        self.assertIn("0:a:0", command)
        self.assertNotIn("libmp3lame", command)


if __name__ == "__main__":
    unittest.main()
