"""Headless Qt checks for switching languages without changing task data."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Linux development environments need an offscreen backend. Windows CI uses
# the native platform for visual previews so system font fallback is exercised.
if os.name != "nt":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QSettings, Qt
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    QSettings = None
    QApplication = None
    MainWindow = None
else:
    from main import MainWindow

from engine import MODE_EXTRACT, RAW_AUDIO
from music_unlock import MODE_MUSIC_UNLOCK, UNLOCK_TARGET


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

    def test_music_unlock_mode_is_localized_and_accepts_protected_files(self):
        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_MUSIC_UNLOCK))
        self.assertEqual(self.window.target_combo.currentData(), UNLOCK_TARGET)
        self.assertFalse(self.window.target_combo.isEnabled())
        self.assertTrue(self.window.quality_combo.isHidden())
        self.assertEqual(self.window.start_button.text(), "开始解锁")
        self.assertIn("合法拥有", self.window.quality_hint.text())
        self.assertGreaterEqual(self.window.quality_hint.minimumHeight(), 54)

        source = self.root / "collection.NCM"
        source.write_bytes(b"encrypted")
        rejected = self.root / "clip.mp4"
        rejected.write_bytes(b"video")
        self.window._add_paths([source, rejected])
        self.assertEqual(self.window._current_paths(), [source.resolve()])
        self.assertEqual(self.window.table.item(0, 1).text(), "NCM")

        for locale, mode_text, start_text in (
            ("en_US", "Unlock local music files", "Start unlocking"),
            ("zh_TW", "解鎖本機音樂檔案", "開始解鎖"),
            ("zh_CN", MODE_MUSIC_UNLOCK, "开始解锁"),
        ):
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData(locale))
            self.assertEqual(self.window.mode_combo.currentText(), mode_text)
            self.assertEqual(self.window.start_button.text(), start_text)
            self.assertEqual(self.window.mode_combo.currentData(), MODE_MUSIC_UNLOCK)
            self.assertEqual(self.window.target_combo.currentData(), UNLOCK_TARGET)

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.resize(1280, 820)
            self.window.show()
            for theme in ("light", "dark"):
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(
                    str(Path(preview_dir) / f"music-unlock-zh_CN-{theme}.png")
                )

        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_EXTRACT))
        self.assertFalse(self.window.quality_combo.isHidden())
        self.assertTrue(self.window.target_combo.isEnabled())

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

    def test_custom_background_can_be_selected_persisted_and_removed(self):
        background = self.root / "background.png"
        image = QImage(640, 360, QImage.Format.Format_RGB32)
        painter = QPainter(image)
        painter.fillRect(0, 0, 320, 360, QColor("#264d8f"))
        painter.fillRect(320, 0, 320, 180, QColor("#765a9e"))
        painter.fillRect(320, 180, 320, 180, QColor("#2f7d72"))
        painter.end()
        self.assertTrue(image.save(str(background)))

        with patch("main.QFileDialog.getOpenFileName",
                   return_value=(str(background), "")):
            self.window.choose_background_image()
        QApplication.processEvents()
        self.assertTrue(self.window.background_canvas.has_image())
        self.assertEqual(self.window.background_path, str(background.resolve()))
        self.assertEqual(
            self.settings.value("appearance/background_image"),
            str(background.resolve()),
        )
        self.assertEqual(self.window.background_button.text(), "自定义图片")
        self.assertTrue(self.window.remove_background_action.isEnabled())

        self.window.language_combo.setCurrentIndex(
            self.window.language_combo.findData("en_US"))
        self.assertEqual(self.window.background_button.text(), "Custom image")
        self.window.language_combo.setCurrentIndex(
            self.window.language_combo.findData("zh_CN"))

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.theme_combo.setCurrentIndex(
                self.window.theme_combo.findData("light"))
            self.window.resize(1000, 720)
            self.window.show()
            QApplication.processEvents()
            self.window.grab().save(
                str(Path(preview_dir) / "background-zh_CN-light.png")
            )
            self.window.theme_combo.setCurrentIndex(
                self.window.theme_combo.findData("dark"))
            QApplication.processEvents()
            self.window.grab().save(
                str(Path(preview_dir) / "background-zh_CN-dark.png")
            )

        self.window.close()
        with patch("main.QSettings", return_value=self.settings):
            self.window = MainWindow()
        self.addCleanup(self.window.close)
        self.assertTrue(self.window.background_canvas.has_image())
        self.assertEqual(self.window.background_path, str(background.resolve()))

        self.window.remove_background_image()
        self.assertFalse(self.window.background_canvas.has_image())
        self.assertFalse(self.settings.contains("appearance/background_image"))
        self.assertFalse(self.window.remove_background_action.isEnabled())
        self.assertEqual(self.window.background_button.text(), "默认背景")

    def test_missing_saved_background_safely_uses_default(self):
        self.window.close()
        self.settings.setValue(
            "appearance/background_image", str(self.root / "missing-image.png")
        )
        with patch("main.QSettings", return_value=self.settings):
            self.window = MainWindow()
        self.addCleanup(self.window.close)
        self.assertFalse(self.window.background_canvas.has_image())
        self.assertFalse(self.settings.contains("appearance/background_image"))
        self.assertEqual(self.window.background_button.text(), "默认背景")

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
            self.assertFalse(self.window.workspace_wide)
            self.assertTrue(self.window.header_compact)
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
        # The hosted Windows desktop is only 1024 px wide and caps visible
        # top-level windows. Re-check the desktop breakpoint while hidden.
        self.window.hide()
        self.window.resize(1200, 800)
        self.window._adapt_layout()
        QApplication.processEvents()
        self.assertTrue(self.window.workspace_wide)
        self.assertFalse(self.window.header_compact)
        self.assertEqual(self.window.field_columns, 2)

    def test_empty_state_and_populated_queue_switch_cleanly(self):
        self.window.show()
        QApplication.processEvents()
        self.assertIs(self.window.file_stack.currentWidget(), self.window.empty_state)
        self.assertFalse(self.window.clear_button.isEnabled())
        self.assertFalse(self.window.remove_button.isEnabled())

        source = self.root / "clip.mp4"
        source.write_bytes(b"test")
        self.window._add_paths([source])
        QApplication.processEvents()
        self.assertIs(self.window.file_stack.currentWidget(), self.window.table)
        self.assertTrue(self.window.clear_button.isEnabled())
        self.window.table.selectRow(0)
        QApplication.processEvents()
        self.assertTrue(self.window.remove_button.isEnabled())
        self.window.clear_files()
        self.assertIs(self.window.file_stack.currentWidget(), self.window.empty_state)

    def test_populated_workspace_visual_states(self):
        sources = [self.root / name for name in ("holiday.mp4", "interview.wav", "archive.mkv")]
        for source in sources:
            source.write_bytes(b"test")
        self.window._add_paths(sources)
        self.assertGreaterEqual(self.window.table.columnWidth(1), 76)
        self.window._item_finished(
            0, True, "Completed: file size reduced by 42.0%",
            str(self.root / "holiday_small.mp4"),
        )
        self.window._item_finished(1, False, "FFmpeg: sample diagnostic text", "")
        self.window.resize(1280, 820)
        self.window.ensurePolished()
        self.window._adapt_layout()
        QApplication.processEvents()
        self.assertTrue(self.window.workspace_wide)
        self.assertEqual(self.window.table.item(0, 3).data(Qt.ItemDataRole.UserRole), "success")
        self.assertEqual(self.window.table.item(1, 3).data(Qt.ItemDataRole.UserRole), "failed")

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if not preview_dir:
            return
        Path(preview_dir).mkdir(parents=True, exist_ok=True)
        for locale in ("zh_CN", "zh_TW", "en_US"):
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData(locale))
            for theme in ("light", "dark"):
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(
                    str(Path(preview_dir) / f"workspace-{locale}-{theme}.png"))
