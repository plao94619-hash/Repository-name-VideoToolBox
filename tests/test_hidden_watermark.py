"""End-to-end checks for image pixel treatment and safe output lifecycle."""

import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from threading import Event
from unittest.mock import patch

from engine import (
    ConversionCancelled, ConversionError, ConversionOptions,
    ffmpeg_path, ffprobe_path,
)
from hidden_watermark import (
    MODE_IMAGE_HIDDEN_WATERMARK,
    build_hidden_watermark_command,
    make_hidden_output_path,
    process_hidden_watermark,
)


def _png_chunk(name: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + name + data
            + struct.pack(">I", zlib.crc32(name + data) & 0xffffffff))


def _write_sample(path: Path) -> bytes:
    width, height = 12, 10
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")  # PNG filter type: no filtering
        for x in range(width):
            row.extend((120 + (x + y) % 4, 132 + x % 4,
                        144 + y % 4, 31 + (x * 7 + y) % 200))
        rows.append(row)
    data = (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0))
            + _png_chunk(b"IDAT", zlib.compress(b"".join(rows)))
            + _png_chunk(b"IEND", b""))
    path.write_bytes(data)
    return data


def _rgba_pixels(path: Path) -> bytes:
    return subprocess.check_output([
        str(ffmpeg_path()), "-v", "error", "-i", str(path),
        "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-",
    ])


def _ffmpeg_available() -> bool:
    try:
        return ffmpeg_path().is_file() and ffprobe_path().is_file()
    except ConversionError:
        return False


class HiddenWatermarkTests(unittest.TestCase):
    def options(self, root: Path, strength: str = "标准处理") -> ConversionOptions:
        return ConversionOptions(
            mode=MODE_IMAGE_HIDDEN_WATERMARK,
            target="PNG（无损）", quality=strength,
            encoder="自动选择", resolution="保持原分辨率",
            output_dir=root,
        )

    def test_missing_ffmpeg_skips_instead_of_failing_test_collection(self):
        with patch(f"{__name__}.ffmpeg_path",
                   side_effect=ConversionError("missing")):
            self.assertFalse(_ffmpeg_available())

    def test_command_keeps_alpha_and_metadata_cleaning_is_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            options = self.options(root)
            command = build_hidden_watermark_command(
                root / "original.png", root / "out.png", options)
            graph = command[command.index("-vf") + 1]
            self.assertIn("format=gbrap,gblur=sigma=0.35:planes=7", graph)
            self.assertIn("format=rgba,lutrgb=r=trunc(val/4)*4:", graph)
            self.assertNotIn(":a=", graph)
            self.assertEqual(command[command.index("-map_metadata") + 1], "0")
            cleaned = build_hidden_watermark_command(
                root / "original.png", root / "out.png", options, True)
            self.assertEqual(cleaned[cleaned.index("-map_metadata") + 1], "-1")
            with self.assertRaises(ConversionError):
                build_hidden_watermark_command(
                    root / "original.png", root / "out.png",
                    self.options(root, "unknown"))

    def test_output_name_avoids_replacing_old_results(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "sample.png"
            first = make_hidden_output_path(source, self.options(root))
            self.assertEqual(first.name, "sample_hidden_processed.png")
            first.touch()
            self.assertEqual(make_hidden_output_path(source, self.options(root)).name,
                             "sample_hidden_processed_2.png")

    @unittest.skipUnless(_ffmpeg_available(),
                         "requires FFmpeg and FFprobe")
    def test_real_png_processing_clears_low_bits_preserves_alpha_and_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "original.png"
            original_bytes = _write_sample(source)
            before = _rgba_pixels(source)
            for name, mask in (("轻度处理", 1),
                               ("标准处理", 3),
                               ("强力处理", 7)):
                events = []
                result = process_hidden_watermark(
                    source, self.options(root, name),
                    lambda value, label: events.append((value, label)))
                self.assertEqual((result.width, result.height), (12, 10))
                self.assertIn("请自行核验", result.size_message)
                pixels = _rgba_pixels(result.output_path)
                self.assertEqual(len(pixels), len(before))
                self.assertEqual(pixels[3::4], before[3::4])
                self.assertTrue(all(value & mask == 0
                                    for index, value in enumerate(pixels)
                                    if index % 4 != 3))
                self.assertEqual(events[-1][0], 100)
                self.assertEqual(source.read_bytes(), original_bytes)
            self.assertEqual(list(root.glob(".*.partial.png")), [])

    def test_cancellation_before_start_and_failed_partial_are_cleaned(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.png"
            _write_sample(source)
            cancelled = Event()
            cancelled.set()
            with self.assertRaises(ConversionCancelled):
                process_hidden_watermark(source, self.options(root),
                                         cancel_event=cancelled)

            def fail(command, *_args):
                Path(command[-1]).write_bytes(b"incomplete")
                raise ConversionError("simulated failure")

            with patch("hidden_watermark._run_ffmpeg", side_effect=fail):
                with self.assertRaises(ConversionError):
                    process_hidden_watermark(source, self.options(root))
            self.assertEqual(list(root.glob("*hidden_processed*")), [])


if __name__ == "__main__":
    unittest.main()
