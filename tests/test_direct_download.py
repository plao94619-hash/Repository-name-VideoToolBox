"""Offline integration tests for the conservative direct-audio downloader."""

from __future__ import annotations

import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event

from direct_download import (
    DirectDownloadCancelled,
    DirectDownloadError,
    download_direct_audio,
    download_source_label,
    make_download_task,
    split_url_input,
)


class _AudioHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    song = b"ID3\x04\x00\x00" + (b"authorized-audio" * 32_768)

    def do_GET(self):
        if self.path == "/song.mp3":
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header(
                "Content-Disposition",
                "attachment; filename*=UTF-8''Authorized%20Song.mp3",
            )
            self.send_header("Content-Length", str(len(self.song)))
            self.end_headers()
            self.wfile.write(self.song)
            return
        if self.path == "/unknown":
            body = b"fLaC\x00\x00\x00\x22" + (b"audio" * 100)
            self.send_response(200)
            self.send_header("Content-Type", "audio/flac")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/playlist.mp3":
            body = b"#EXTM3U\n#EXTINF:10,Track\nsegment.ts\n"
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/protected.m4a":
            body = b"\x00\x00\x00\x18ftypM4A \x00\x00\x00\x00sinfenca" + (b"x" * 200)
            self.send_response(200)
            self.send_header("Content-Type", "audio/mp4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/not-audio.mp3":
            body = b"<html>not audio</html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/blocked-redirect":
            self.send_response(302)
            self.send_header("Location", "https://open.spotify.com/track/example")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, _format, *_args):
        return


class DirectDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _AudioHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def test_url_validation_blocks_platforms_credentials_and_manifests(self):
        blocked = (
            "https://open.spotify.com/track/abc",
            "https://music.apple.com/us/album/example/123?i=456",
            "https://user:secret@example.com/song.mp3",
            "https://example.com/stream.m3u8",
            "file:///tmp/song.mp3",
            "https://example.com/index.html",
        )
        for url in blocked:
            with self.subTest(url=url), self.assertRaises(DirectDownloadError):
                make_download_task(url)

    def test_split_and_safe_display_never_expose_query_tokens(self):
        urls = split_url_input(
            "https://example.com/a.mp3?token=secret\nhttps://example.org/b.flac"
        )
        self.assertEqual(len(urls), 2)
        label = download_source_label(urls[0])
        self.assertIn("a.mp3", label)
        self.assertNotIn("secret", label)

    def test_downloads_direct_audio_and_uses_unique_name(self):
        progress: list[tuple[int, str]] = []
        task = make_download_task(f"{self.base_url}/song.mp3")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = download_direct_audio(
                task, root, progress_callback=lambda percent, text: progress.append(
                    (percent, text)))
            second = download_direct_audio(task, root)
            self.assertEqual(first.output_path.name, "Authorized Song.mp3")
            self.assertEqual(second.output_path.name, "Authorized Song (1).mp3")
            self.assertEqual(first.output_path.read_bytes(), _AudioHandler.song)
            self.assertEqual(progress[-1][0], 100)
            self.assertFalse(list(root.glob("*.part")))

    def test_derives_extension_from_audio_content_type(self):
        task = make_download_task(f"{self.base_url}/unknown")
        with tempfile.TemporaryDirectory() as folder:
            result = download_direct_audio(task, Path(folder))
            self.assertEqual(result.output_path.suffix, ".flac")
            self.assertGreater(result.output_size, 0)

    def test_rejects_non_audio_streaming_and_protected_responses(self):
        for path in ("/not-audio.mp3", "/playlist.mp3", "/protected.m4a"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as folder:
                task = make_download_task(f"{self.base_url}{path}")
                with self.assertRaises(DirectDownloadError):
                    download_direct_audio(task, Path(folder))
                self.assertEqual(list(Path(folder).iterdir()), [])

    def test_rejects_redirect_before_contacting_blocked_platform(self):
        task = make_download_task(f"{self.base_url}/blocked-redirect")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(DirectDownloadError, "Spotify|Apple Music"):
                download_direct_audio(task, Path(folder))

    def test_pre_cancelled_download_creates_no_file(self):
        task = make_download_task(f"{self.base_url}/song.mp3")
        cancel = Event()
        cancel.set()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(DirectDownloadCancelled):
                download_direct_audio(task, Path(folder), cancel_event=cancel)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
