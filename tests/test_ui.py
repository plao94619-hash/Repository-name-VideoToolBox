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
except ModuleNotFoundError:
    QSettings = None
    QApplication = None
    MainWindow = None
else:
    from main import MainWindow

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
        self.window.close()
        self.settings.setValue("locale", "en_US")
        with patch("main.QSettings", return_value=self.settings):
            self.window = MainWindow()
        self.addCleanup(self.window.close)
        self.assertEqual(self.window.language_combo.currentData(), "en_US")
        self.assertEqual(self.window.mode_combo.currentData(), MODE_EXTRACT)
        self.assertEqual(self.window.target_combo.currentData(), RAW_AUDIO)
        self.assertEqual(self.window.start_button.text(), "Start")

    def test_theme_and_saved_geometry_do_not_change_task_settings(self):
        self.window.theme_combo.setCurrentIndex(self.window.theme_combo.findData("dark"))
        self.assertEqual(self.window.theme, "dark")
        self.assertEqual(self.window.effective_theme, "dark")
        self.assertEqual(self.settings.value("appearance/theme"), "dark")
        self.assertEqual(self.window.mode_combo.currentData(), MODE_EXTRACT)
        self.window.resize(860, 640)
        self.window._save_settings()
        self.assertIsNotNone(self.settings.value("window/geometry"))
        self.window.close()
        with patch("main.QSettings", return_value=self.settings):
            self.window = MainWindow()
        self.addCleanup(self.window.close)
        self.assertEqual(self.window.theme_combo.currentData(), "dark")
        self.assertEqual(self.window.mode_combo.currentData(), MODE_EXTRACT)
        self.assertEqual(self.window.target_combo.currentData(), RAW_AUDIO)

    def test_result_path_and_full_error_details_are_accessible(self):
        source = self.root / "clip.mp4"
        source.write_bytes(b"test")
        self.window._add_paths([source])
        result = str(self.root / "clip_audio.m4a")
        self.window._item_finished(0, True, "Completed", result)
        self.window._table_double_clicked(0, 4)
        self.assertEqual(QApplication.clipboard().text(), result)
        self.assertEqual(self.window.table.item(0, 4).text(), "clip_audio.m4a")
        self.window._item_finished(0, False, "FFmpeg: full diagnostic text", "")
        self.assertEqual(self.window._error_details_box(0).detailedText(),
                         "FFmpeg: full diagnostic text")

    def test_narrow_layout_keeps_controls_visible_in_all_languages(self):
        self.window.mode_combo.setCurrentIndex(self.window.mode_combo.findData("视频格式转换"))
        self.window.resize(850, 640)
        self.window.show()
        for locale in ("en_US", "zh_TW", "zh_CN"):
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData(locale))
            QApplication.processEvents()
            self.assertEqual(self.window.field_columns, 2)
            self.assertTrue(self.window.start_button.isVisible())
            self.assertTrue(self.window.output_edit.isVisible())
            self.assertGreaterEqual(self.window.output_edit.width(), 300)
            self.assertGreaterEqual(self.window.mode_combo.width(), 190)
            for button in (self.window.add_files_button, self.window.add_folder_button,
                           self.window.remove_button, self.window.clear_button,
                           self.window.start_button):
                self.assertGreaterEqual(button.width(),
                                        button.fontMetrics().horizontalAdvance(button.text()) + 16,
                                        f"{locale}: {button.text()}")
            preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
            if preview_dir:
                Path(preview_dir).mkdir(parents=True, exist_ok=True)
                self.window.grab().save(str(Path(preview_dir) / f"ui-{locale}-light.png"))
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData("dark"))
                QApplication.processEvents()
                self.window.grab().save(str(Path(preview_dir) / f"ui-{locale}-dark.png"))
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData("light"))
        self.window.resize(1200, 800)
        QApplication.processEvents()
        self.assertEqual(self.window.field_columns, 3)
