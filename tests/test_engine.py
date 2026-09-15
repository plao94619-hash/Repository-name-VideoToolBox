import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from engine import (
    ConversionError,
    ConversionOptions,
    MediaInfo,
    MODE_COMPRESS,
    MODE_EXTRACT,
    MODE_VIDEO,
    RAW_AUDIO,
    build_command,
    convert_file,
    make_output_path,
    probe_media,
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

    @patch("engine.ffmpeg_path", return_value=Path("ffmpeg.exe"))
    @patch("engine.encoder_names", return_value={"libx264"})
    def test_attached_cover_is_not_selected_as_video(self, _encoders, _ffmpeg):
        streams = [
            {"index": 0, "codec_type": "video", "codec_name": "mjpeg",
             "disposition": {"attached_pic": 1}},
            {"index": 1, "codec_type": "audio", "codec_name": "aac"},
            {"index": 2, "codec_type": "video", "codec_name": "h264",
             "width": 1920, "height": 1080,
             "disposition": {"attached_pic": 0}},
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "cover.mp4"
            source.touch()
            with patch("engine.ffprobe_path", return_value=Path("ffprobe.exe")), \
                 patch("engine._run_capture", return_value=json.dumps(
                     {"format": {"duration": "10", "size": "100"}, "streams": streams}
                 )):
                info = probe_media(source)
            self.assertEqual(info.video_codec, "h264")
            self.assertEqual(info.video_stream_index, 2)
            self.assertEqual(info.audio_stream_index, 1)
            options = self.make_options(Path(folder), MODE_VIDEO, "MP4")
            command = build_command(source, Path(folder) / "out.mp4", options, info)
            self.assertIn("0:2", command)
            self.assertNotIn("0:v:0", command)

    @patch("engine.ffmpeg_path", return_value=Path("ffmpeg.exe"))
    @patch("engine.encoder_names", return_value={"h264_nvenc", "libx264"})
    @patch("engine.hardware_encoder_works", return_value=True)
    def test_failed_gpu_encode_retries_cpu(self, _hardware, _encoders, _ffmpeg):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "video.mp4"
            source.write_bytes(b"video")
            options = self.make_options(root, MODE_VIDEO, "MP4")
            commands = []

            def run_attempt(command, *_args):
                commands.append(command)
                if len(commands) == 1:
                    Path(command[-1]).write_bytes(b"incomplete")
                    raise ConversionError("GPU error")
                Path(command[-1]).write_bytes(b"complete")

            with patch("engine.probe_media", return_value=MediaInfo(
                duration=1, video_codec="h264", size=5
            )), patch("engine._run_ffmpeg", side_effect=run_attempt):
                result = convert_file(source, options)
            self.assertEqual(len(commands), 2)
            self.assertIn("h264_nvenc", commands[0])
            self.assertIn("libx264", commands[1])
            self.assertEqual(result.output_path.read_bytes(), b"complete")
            self.assertEqual(list(root.glob(".*.partial.mp4")), [])

    def test_cover_only_media_is_not_recognized_as_video(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "song.mp3"
            source.touch()
            data = {"streams": [
                {"index": 0, "codec_type": "video", "codec_name": "mjpeg",
                 "disposition": {"attached_pic": 1}},
                {"index": 1, "codec_type": "audio", "codec_name": "mp3"},
            ]}
            with patch("engine.ffprobe_path", return_value=Path("ffprobe.exe")), \
                 patch("engine._run_capture", return_value=json.dumps(data)):
                info = probe_media(source)
            self.assertFalse(info.video_codec)
            self.assertEqual(info.audio_stream_index, 1)


if __name__ == "__main__":
    unittest.main()
