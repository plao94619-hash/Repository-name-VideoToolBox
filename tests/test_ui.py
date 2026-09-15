"""Headless Qt checks for switching languages without changing task data."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QSettings, Qt
    from PySide6.QtWidgets import QApplication
    from main import MainWindow
except ImportError:
    QSettings = None
    QApplication = None
    MainWindow = None

from engine import MODE_EXTRACT, RAW_AUDIO


@unittest.skipIf(QApplication is None, "PySide6 not installed in this environment")
class LanguageUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.settings = QSettings(str(self.root / "settings.ini"), QSettings.Format.IniFormat)
        # These are the exact values saved by v1.1.0.
        self.settings.setValue("mode", MODE_EXTRACT)
        self.settings.setValue("target", RAW_AUDIO)
        self.settings.setValue("quality", "画质优先")
        self.settings.setValue("locale", "zh_CN")
        with patch("main.QSettings", return_value=self.settings):
            self.window = MainWindow()
        self.addCleanup(self.window.close)

    def test_switching_languages_preserves_legacy_options_and_files(self):
        source = self.root / "clip.mp4"
        source.write_bytes(b"test")
        self.window._add_paths([source])
        self.assertEqual(self.window.mode_combo.currentData(), MODE_EXTRACT)
        self.assertEqual(self.window.target_combo.currentData(), RAW_AUDIO)
        self.assertEqual(self.window.quality_combo.currentData(), "画质优先")

        for locale, mode_text, start_text in (
            ("en_US", "Extract audio from video", "Start"),
            ("zh_TW", "從影片擷取音訊", "開始處理"),
            ("zh_CN", MODE_EXTRACT, "开始处理"),
        ):
            index = self.window.language_combo.findData(locale)
            self.window.language_combo.setCurrentIndex(index)
            self.assertEqual(self.window.mode_combo.currentText(), mode_text)
            self.assertEqual(self.window.start_button.text(), start_text)
            self.assertEqual(self.window.mode_combo.currentData(), MODE_EXTRACT)
            self.assertEqual(self.window.target_combo.currentData(), RAW_AUDIO)
            self.assertEqual(self.window._current_paths(), [source.resolve()])
            self.assertEqual(self.window.table.item(0, 3).data(Qt.ItemDataRole.UserRole),
                             "pending")
            self.window._save_settings()
            self.assertEqual(self.settings.value("mode"), MODE_EXTRACT)
            self.assertEqual(self.settings.value("target"), RAW_AUDIO)
            self.assertEqual(self.settings.value("locale"), locale)

    def test_previous_language_is_restored_on_restart(self):
        self.settings.setValue("locale", "en_US")
        self.window.close()
        with patch("main.QSettings", return_value=self.settings):
            self.window = MainWindow()
        self.addCleanup(self.window.close)
        self.assertEqual(self.window.language_combo.currentData(), "en_US")
        self.assertEqual(self.window.mode_combo.currentData(), MODE_EXTRACT)
        self.assertEqual(self.window.target_combo.currentData(), RAW_AUDIO)
        self.assertEqual(self.window.start_button.text(), "Start")
