import subprocess
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from clarity_enhance import (
    MODE_IMAGE_ENHANCE,
    MODE_VIDEO_ENHANCE,
    build_enhance_command,
    enhance_filter,
    enhance_media_file,
    make_enhance_output_path,
    output_dimensions,
)
from engine import (
    ConversionCancelled,
    ConversionError,
    ConversionOptions,
    MediaInfo,
    ffmpeg_path,
    ffprobe_path,
    probe_media,
)


class ClarityEnhanceTests(unittest.TestCase):
    def options(
        self,
        root: Path,
        mode: str = MODE_VIDEO_ENHANCE,
        target: str = "MP4",
        resolution: str = "提升至 4K",
    ) -> ConversionOptions:
        return ConversionOptions(
            mode=mode,
            target=target,
            quality="标准增强",
            encoder="H.264（兼容优先）",
            resolution=resolution,
            output_dir=root,
        )

    def test_landscape_and_portrait_4k_keep_aspect_ratio(self):
        self.assertEqual(output_dimensions(1920, 1080, "提升至 4K"), (3840, 2160))
        self.assertEqual(output_dimensions(1080, 1920, "提升至 4K"), (2160, 3840))
        self.assertEqual(output_dimensions(800, 1200, "提升至 4K"), (2160, 3240))
        self.assertEqual(output_dimensions(1000, 1000, "提升至 4K"), (2160, 2160))

    def test_keep_size_never_upscales_and_caps_above_4k(self):
        keep = "保持原尺寸（最高 4K）"
        self.assertEqual(output_dimensions(1280, 720, keep), (1280, 720))
        self.assertEqual(output_dimensions(7680, 4320, keep), (3840, 2160))
        self.assertEqual(output_dimensions(4320, 7680, keep), (2160, 3840))

    def test_2k_and_1080p_targets_are_even(self):
        self.assertEqual(output_dimensions(853, 480, "提升至 1080p"), (1918, 1080))
        width, height = output_dimensions(641, 359, "提升至 2K")
        self.assertLessEqual(width, 2560)
        self.assertLessEqual(height, 1440)
        self.assertEqual(width % 2, 0)
        self.assertEqual(height % 2, 0)

    def test_filter_uses_denoise_lanczos_and_sharpening(self):
        filters = enhance_filter(3840, 2160, "标准增强")
        self.assertIn("hqdn3d=", filters)
        self.assertIn("scale=3840:2160:flags=lanczos", filters)
        self.assertIn("unsharp=", filters)
        self.assertTrue(filters.endswith("setsar=1"))

    def test_output_names_are_descriptive_and_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "photo.jpg"
            source.touch()
            options = self.options(
                root, MODE_IMAGE_ENHANCE, "PNG（无损）", "提升至 4K")
            first = make_enhance_output_path(source, options)
            self.assertEqual(first.name, "photo_enhanced_4k.png")
            first.touch()
            self.assertEqual(
                make_enhance_output_path(source, options).name,
                "photo_enhanced_4k_2.png",
            )

    @patch("clarity_enhance.ffmpeg_path", return_value=Path("ffmpeg.exe"))
    @patch("clarity_enhance._video_encoder", return_value="libx264")
    def test_video_command_preserves_audio_and_uses_high_quality_codec(
        self, _encoder, _ffmpeg,
    ):
        options = self.options(Path("."), resolution="提升至 1080p")
        command, dimensions, encoder = build_enhance_command(
            Path("input.mkv"), Path("output.mp4"), options,
            MediaInfo(
                duration=2, video_codec="h264", audio_codec="aac",
                width=640, height=360, video_stream_index=1,
            ),
        )
        self.assertEqual(dimensions, (1920, 1080))
        self.assertEqual(encoder, "libx264")
        self.assertIn("0:1", command)
        self.assertIn("0:a?", command)
        self.assertIn("-crf", command)
        self.assertIn("+faststart", command)

    @patch("clarity_enhance.ffmpeg_path", return_value=Path("ffmpeg.exe"))
    def test_image_command_outputs_one_lossless_png(self, _ffmpeg):
        options = self.options(
            Path("."), MODE_IMAGE_ENHANCE, "PNG（无损）", "提升至 2K")
        command, dimensions, encoder = build_enhance_command(
            Path("input.jpg"), Path("output.png"), options,
            MediaInfo(duration=0, video_codec="mjpeg", width=800, height=600),
        )
        self.assertEqual(dimensions, (1920, 1440))
        self.assertEqual(encoder, "png")
        self.assertEqual(command[command.index("-frames:v") + 1], "1")
        self.assertIn("-compression_level", command)

    def test_success_is_published_atomically_and_reports_dimensions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "photo.jpg"
            source.write_bytes(b"source")
            options = self.options(
                root, MODE_IMAGE_ENHANCE, "PNG（无损）", "提升至 1080p")
            progress = []

            def fake_run(command, *_args):
                Path(command[-1]).write_bytes(b"enhanced")

            with patch("clarity_enhance.probe_media", return_value=MediaInfo(
                duration=0, video_codec="mjpeg", width=640, height=360, size=6,
            )), patch("clarity_enhance.ffmpeg_path", return_value=Path("ffmpeg.exe")), \
                 patch("clarity_enhance._run_ffmpeg", side_effect=fake_run):
                result = enhance_media_file(
                    source, options,
                    lambda percent, _message: progress.append(percent),
                )
            self.assertEqual(result.output_path.name, "photo_enhanced_1080p.png")
            self.assertEqual((result.width, result.height), (1920, 1080))
            self.assertEqual(result.output_path.read_bytes(), b"enhanced")
            self.assertEqual(progress[-1], 100)
            self.assertEqual(list(root.glob(".*.partial.png")), [])

    def test_cancellation_before_start_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "clip.mp4"
            source.write_bytes(b"video")
            cancel = Event()
            cancel.set()
            with self.assertRaises(ConversionCancelled):
                enhance_media_file(source, self.options(root), cancel_event=cancel)
            self.assertEqual(list(root.glob("*enhanced*")), [])


class ClarityEnhanceIntegrationTests(unittest.TestCase):
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

    def test_real_image_enhancement_is_readable(self):
        source = self.root / "source.bmp"
        subprocess.run(
            [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", "testsrc2=size=96x54:rate=1",
             "-frames:v", "1", str(source)],
            check=True, capture_output=True, timeout=30,
        )
        for target, suffix in (
            ("PNG（无损）", ".png"),
            ("JPG（高质量）", ".jpg"),
            ("WebP（高质量）", ".webp"),
        ):
            with self.subTest(target=target):
                options = ConversionOptions(
                    mode=MODE_IMAGE_ENHANCE,
                    target=target,
                    quality="标准增强",
                    encoder="自动选择",
                    resolution="保持原尺寸（最高 4K）",
                    output_dir=self.root,
                )
                result = enhance_media_file(source, options)
                info = probe_media(result.output_path)
                self.assertEqual((info.width, info.height), (96, 54))
                self.assertEqual(result.output_path.suffix, suffix)

    def test_real_image_can_be_enhanced_to_4k(self):
        source = self.root / "small-source.bmp"
        subprocess.run(
            [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", "testsrc2=size=64x36:rate=1",
             "-frames:v", "1", str(source)],
            check=True, capture_output=True, timeout=30,
        )
        options = ConversionOptions(
            mode=MODE_IMAGE_ENHANCE,
            target="PNG（无损）",
            quality="自然增强",
            encoder="自动选择",
            resolution="提升至 4K",
            output_dir=self.root,
        )
        result = enhance_media_file(source, options)
        info = probe_media(result.output_path)
        self.assertEqual((info.width, info.height), (3840, 2160))
        self.assertEqual((result.width, result.height), (3840, 2160))

    def test_real_video_enhancement_is_playable(self):
        source = self.root / "source.mp4"
        subprocess.run(
            [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", "testsrc2=size=96x54:rate=10:duration=0.3",
             "-c:v", "mpeg4", str(source)],
            check=True, capture_output=True, timeout=30,
        )
        options = ConversionOptions(
            mode=MODE_VIDEO_ENHANCE,
            target="MP4",
            quality="自然增强",
            encoder="H.264（兼容优先）",
            resolution="保持原尺寸（最高 4K）",
            output_dir=self.root,
        )
        result = enhance_media_file(source, options)
        info = probe_media(result.output_path)
        self.assertEqual((info.width, info.height), (96, 54))
        self.assertTrue(info.video_codec)
        self.assertGreater(info.duration, 0)


if __name__ == "__main__":
    unittest.main()
