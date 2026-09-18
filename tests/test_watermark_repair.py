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
    MediaInfo,
    ffmpeg_path,
    ffprobe_path,
    probe_media,
)
from watermark_repair import (
    MODE_IMAGE_WATERMARK_REPAIR,
    WatermarkRegion,
    build_watermark_repair_command,
    display_dimensions,
    make_watermark_output_path,
    normalize_regions,
    padding_pixels,
    repair_visible_watermark,
    write_region_mask,
)


class WatermarkRepairTests(unittest.TestCase):
    def options(self, root: Path, target: str = "PNG（无损）") -> ConversionOptions:
        return ConversionOptions(
            mode=MODE_IMAGE_WATERMARK_REPAIR,
            target=target,
            quality="标准修复",
            encoder="自动选择",
            resolution="保持原分辨率",
            output_dir=root,
        )

    def test_regions_are_clipped_and_large_or_empty_selections_are_rejected(self):
        regions = normalize_regions([
            WatermarkRegion(-0.1, 0.2, 0.3, 0.4),
            WatermarkRegion(0.8, 0.8, 0.4, 0.4),
        ])
        self.assertEqual((regions[0].x, regions[0].y), (0.0, 0.2))
        self.assertAlmostEqual(regions[0].width, 0.2)
        self.assertAlmostEqual(regions[0].height, 0.4)
        self.assertAlmostEqual(regions[1].width, 0.2)
        self.assertAlmostEqual(regions[1].height, 0.2)
        with self.assertRaises(ValueError):
            normalize_regions([])
        with self.assertRaises(ValueError):
            normalize_regions([WatermarkRegion(0, 0, 0.8, 0.8)])

    def test_mask_has_black_border_and_white_selected_area(self):
        with tempfile.TemporaryDirectory() as folder:
            mask = Path(folder) / "mask.pgm"
            write_region_mask(
                mask, 20, 10, [WatermarkRegion(0.25, 0.2, 0.25, 0.4)], 1,
            )
            data = mask.read_bytes()
            header = b"P5\n20 10\n255\n"
            self.assertTrue(data.startswith(header))
            pixels = data[len(header):]
            self.assertEqual(len(pixels), 200)
            self.assertTrue(all(value == 0 for value in pixels[:20]))
            self.assertEqual(pixels[4 * 20 + 7], 255)
            self.assertEqual(pixels[-1], 0)

    def test_strength_padding_is_bounded(self):
        self.assertEqual(padding_pixels(800, 600, "精细修复"), 0)
        self.assertEqual(padding_pixels(800, 600, "标准修复"), 2)
        self.assertEqual(padding_pixels(8000, 6000, "扩展修复"), 16)

    @patch("watermark_repair.ffprobe_path", return_value=Path("ffprobe.exe"))
    @patch("watermark_repair._run_capture")
    def test_display_dimensions_follow_exif_rotation(self, capture, _ffprobe):
        capture.return_value = (
            '{"frames":[{"side_data_list":['
            '{"side_data_type":"3x3 displaymatrix","rotation":-90}]}]}'
        )
        info = MediaInfo(duration=0, video_codec="mjpeg", width=1200, height=800)
        self.assertEqual(
            display_dimensions(Path("portrait.jpg"), info),
            (800, 1200),
        )

    def test_output_names_are_descriptive_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "photo.jpg"
            source.touch()
            first = make_watermark_output_path(source, self.options(root))
            self.assertEqual(first.name, "photo_watermark_repaired.png")
            first.touch()
            self.assertEqual(
                make_watermark_output_path(source, self.options(root)).name,
                "photo_watermark_repaired_2.png",
            )

    @patch("watermark_repair.ffmpeg_path", return_value=Path("ffmpeg.exe"))
    def test_command_uses_mask_filter_one_frame_and_preserves_metadata(self, _ffmpeg):
        command = build_watermark_repair_command(
            Path("input.jpg"), Path("output.png"), Path("mask.pgm"),
            self.options(Path(".")),
        )
        self.assertIn("removelogo=filename=", command[command.index("-vf") + 1])
        self.assertEqual(command[command.index("-frames:v") + 1], "1")
        self.assertEqual(command[command.index("-map_metadata") + 1], "0")
        self.assertIn("-update", command)
        self.assertEqual(command[-1], "output.png")

    def test_success_is_atomic_and_temporary_mask_is_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "photo.jpg"
            source.write_bytes(b"source")
            progress = []

            def fake_run(command, *_args):
                masks = list(root.glob(".*.watermark-mask.pgm"))
                self.assertEqual(len(masks), 1)
                Path(command[-1]).write_bytes(b"repaired")

            with patch("watermark_repair.probe_media", return_value=MediaInfo(
                duration=0, video_codec="mjpeg", width=640, height=360, size=6,
            )), patch("watermark_repair.ffmpeg_path", return_value=Path("ffmpeg.exe")), \
                 patch("watermark_repair._run_ffmpeg", side_effect=fake_run):
                result = repair_visible_watermark(
                    source,
                    self.options(root),
                    [WatermarkRegion(0.7, 0.75, 0.2, 0.1)],
                    lambda percent, _message: progress.append(percent),
                )
            self.assertEqual(result.output_path.name, "photo_watermark_repaired.png")
            self.assertEqual(result.output_path.read_bytes(), b"repaired")
            self.assertEqual(result.region_count, 1)
            self.assertEqual(progress[-1], 100)
            self.assertEqual(list(root.glob(".*.partial.png")), [])
            self.assertEqual(list(root.glob(".*.watermark-mask.pgm")), [])

    def test_cancellation_before_start_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "photo.png"
            source.write_bytes(b"image")
            cancel = Event()
            cancel.set()
            with self.assertRaises(ConversionCancelled):
                repair_visible_watermark(
                    source,
                    self.options(root),
                    [WatermarkRegion(0.1, 0.1, 0.2, 0.2)],
                    cancel_event=cancel,
                )
            self.assertEqual(list(root.glob("*watermark_repaired*")), [])


class WatermarkRepairIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.ffmpeg = str(ffmpeg_path())
            ffprobe_path()
        except ConversionError:
            raise unittest.SkipTest("FFmpeg and FFprobe are not yet installed")

    def test_real_visible_region_repair_outputs_readable_image(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.png"
            subprocess.run(
                [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "lavfi", "-i", "color=c=0x557799:s=320x180:d=1",
                 "-vf", "drawbox=x=220:y=130:w=80:h=30:color=white:t=fill",
                 "-frames:v", "1", str(source)],
                check=True, capture_output=True, timeout=30,
            )
            result = repair_visible_watermark(
                source,
                ConversionOptions(
                    mode=MODE_IMAGE_WATERMARK_REPAIR,
                    target="PNG（无损）",
                    quality="标准修复",
                    encoder="自动选择",
                    resolution="保持原分辨率",
                    output_dir=root,
                ),
                [WatermarkRegion(0.66, 0.68, 0.31, 0.24)],
            )
            info = probe_media(result.output_path)
            self.assertEqual((info.width, info.height), (320, 180))
            self.assertEqual(result.output_path.suffix, ".png")
            self.assertGreater(result.output_path.stat().st_size, 0)
            self.assertEqual(list(root.glob(".*.watermark-mask.pgm")), [])


if __name__ == "__main__":
    unittest.main()
