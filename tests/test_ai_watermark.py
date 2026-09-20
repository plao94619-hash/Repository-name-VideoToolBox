"""One-pass AI-image watermark workflow, including transparency and cleanup."""

import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from PIL import Image, ImageDraw

from ai_watermark import (
    MODE_AI_IMAGE_WATERMARK, build_ai_watermark_command,
    make_ai_output_path, repair_ai_watermark,
)
from engine import (
    ConversionCancelled, ConversionError, ConversionOptions, MediaInfo,
    ffmpeg_path, ffprobe_path,
)
from watermark_repair import WatermarkRegion


def _ffmpeg_available() -> bool:
    try:
        return ffmpeg_path().is_file() and ffprobe_path().is_file()
    except ConversionError:
        return False


def _write_sample(path: Path) -> bytes:
    image = Image.new("RGBA", (128, 96), (101, 149, 209, 157))
    ImageDraw.Draw(image).rectangle((88, 72, 119, 88), fill=(254, 254, 254, 157))
    image.save(path)
    return path.read_bytes()


class AIWatermarkTests(unittest.TestCase):
    def options(self, root: Path) -> ConversionOptions:
        return ConversionOptions(
            mode=MODE_AI_IMAGE_WATERMARK, target="PNG（无损）",
            quality="标准修复", encoder="自动选择",
            resolution="保持原分辨率", output_dir=root,
        )

    @patch("ai_watermark.ffmpeg_path", return_value=Path("ffmpeg.exe"))
    def test_combined_command_uses_one_graph_and_restores_alpha(self, _ffmpeg):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            mask = root / "mask.pgm"
            command = build_ai_watermark_command(
                root / "source.png", root / "out.png", self.options(root),
                mask, True,
            )
            graph = command[command.index("-filter_complex") + 1]
            self.assertIn("removelogo=filename=", graph)
            self.assertIn("lutrgb=r=trunc(val/4)*4:", graph)
            self.assertLess(graph.index("removelogo="), graph.index("lutrgb="))
            self.assertIn("[original_alpha]alphaextract[alpha]", graph)
            self.assertIn("[repaired][alpha]alphamerge", graph)
            self.assertEqual(command[command.index("-map") + 1], "[out]")
            self.assertEqual(command[command.index("-map_metadata") + 1], "0")
            hidden_only = build_ai_watermark_command(
                root / "source.png", root / "out.png", self.options(root),
                None, True)
            self.assertNotIn("removelogo", hidden_only[hidden_only.index("-filter_complex") + 1])
            with self.assertRaises(ConversionError):
                build_ai_watermark_command(
                    root / "source.png", root / "out.png", self.options(root),
                    None, False)

    def test_requires_a_selected_operation_and_never_overwrites_results(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "owned.png"
            _write_sample(source)
            with self.assertRaises(ConversionError):
                repair_ai_watermark(source, self.options(root), ())
            output = make_ai_output_path(source, self.options(root))
            self.assertEqual(output.name, "owned_ai_repaired.png")
            output.touch()
            self.assertEqual(make_ai_output_path(source, self.options(root)).name,
                             "owned_ai_repaired_2.png")

    def test_cancellation_and_failure_remove_mask_and_partial_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.png"
            original = _write_sample(source)
            regions = (WatermarkRegion(.69, .75, .24, .18),)
            cancelled = Event()
            cancelled.set()
            with self.assertRaises(ConversionCancelled):
                repair_ai_watermark(
                    source, self.options(root), regions,
                    cancel_event=cancelled)

            def fail(command, *_args):
                self.assertEqual(len(list(root.glob(".*.ai-mask.pgm"))), 1)
                Path(command[-1]).write_bytes(b"incomplete")
                raise ConversionError("simulated failure")

            with patch("ai_watermark.probe_media", return_value=MediaInfo(
                duration=0.04, video_codec="png", width=128, height=96,
            )), patch("ai_watermark.display_dimensions", return_value=(128, 96)), \
                 patch("ai_watermark.ffmpeg_path", return_value=Path("ffmpeg.exe")), \
                 patch("ai_watermark._run_ffmpeg", side_effect=fail):
                with self.assertRaises(ConversionError):
                    repair_ai_watermark(source, self.options(root), regions, True)
            self.assertEqual(list(root.glob(".*.ai-mask.pgm")), [])
            self.assertEqual(list(root.glob(".*.partial.png")), [])
            self.assertEqual(source.read_bytes(), original)

    @unittest.skipUnless(_ffmpeg_available(), "requires FFmpeg and FFprobe")
    def test_real_visible_and_hidden_repairs_are_combined_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "owned.png"
            original = _write_sample(source)
            region = (WatermarkRegion(.69, .75, .24, .18),)
            output = repair_ai_watermark(
                source, self.options(root), region, True)
            with Image.open(output.output_path) as result:
                self.assertEqual(result.size, (128, 96))
                self.assertEqual(result.mode, "RGBA")
                self.assertEqual(result.getpixel((5, 5))[3], 157)
                self.assertEqual(result.getpixel((98, 79))[3], 157)
                self.assertLess(result.getpixel((98, 79))[0], 170)
                self.assertEqual(result.getpixel((5, 5))[0] & 3, 0)
            self.assertEqual(output.region_count, 1)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(list(root.glob(".*.ai-mask.pgm")), [])

            hidden_only = repair_ai_watermark(
                source, self.options(root), (), True)
            with Image.open(hidden_only.output_path) as result:
                self.assertEqual(result.getpixel((5, 5))[3], 157)
                self.assertGreater(result.getpixel((98, 79))[0], 240)


if __name__ == "__main__":
    unittest.main()
