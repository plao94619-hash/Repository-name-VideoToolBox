"""Headless Qt checks for switching languages without changing task data."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Render tests headlessly on every CI host. Qt still uses the host font
# database, while avoiding hosted-desktop size caps and native window stalls.
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
    from watermark_editor import WatermarkRegionDialog

from engine import MODE_AUDIO, MODE_EXTRACT, MODE_VIDEO, RAW_AUDIO
from music_unlock import MODE_MUSIC_UNLOCK, UNLOCK_TARGET
from direct_download import DIRECT_TARGET, MODE_DIRECT_DOWNLOAD, DirectDownloadTask
from clarity_enhance import (
    MODE_IMAGE_ENHANCE,
    MODE_VIDEO_ENHANCE,
)
from watermark_repair import MODE_IMAGE_WATERMARK_REPAIR, WatermarkRegion
from hidden_watermark import MODE_IMAGE_HIDDEN_WATERMARK
from ai_watermark import MODE_AI_IMAGE_WATERMARK
from feature_navigation import FEATURE_MODES


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

    def test_all_features_have_independent_pages_and_shared_task_controls(self):
        self.assertEqual(self.window.feature_stack.count(), len(FEATURE_MODES))
        self.assertEqual(len(self.window.feature_pages), len(FEATURE_MODES))
        page_ids = {id(page) for page in self.window.feature_pages.values()}
        self.assertEqual(len(page_ids), len(FEATURE_MODES))
        video = self.root / "source.mp4"
        video.write_bytes(b"test")
        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(FEATURE_MODES[0]))
        self.window._add_paths([video])

        for index, mode in enumerate(FEATURE_MODES):
            self.window.feature_buttons[mode].click()
            self.assertEqual(self.window.mode_combo.currentData(), mode)
            self.assertIs(self.window.feature_stack.currentWidget(),
                          self.window.feature_pages[mode])
            self.assertIs(self.window.workspace_container.parentWidget(),
                          self.window.feature_pages[mode])
            self.assertEqual(self.window.feature_headers[mode][1].text(), mode)
            self.assertEqual(self.window.compact_group_combo.currentData(),
                             self.window.feature_details[mode][0])
            self.assertEqual(self.window.compact_modes[
                self.window.compact_nav.currentIndex()], mode)
            self.assertEqual(self.window.table.rowCount(), 1)
            self.assertTrue(self.window.feature_buttons[mode].isChecked())
            self.assertEqual(sum(button.isChecked() for button in
                                 self.window.feature_buttons.values()), 1)

        self.window.compact_group_combo.setCurrentIndex(
            self.window.compact_group_combo.findData("音频工具"))
        self.window.compact_nav.setCurrentIndex(
            self.window.compact_modes.index(MODE_DIRECT_DOWNLOAD))
        self.assertEqual(self.window.mode_combo.currentData(), MODE_DIRECT_DOWNLOAD)
        self.assertIs(self.window.url_input_panel.parentWidget(),
                      self.window.feature_pages[MODE_DIRECT_DOWNLOAD])
        self.window.language_combo.setCurrentIndex(
            self.window.language_combo.findData("en_US"))
        self.assertEqual(self.window.feature_headers[MODE_DIRECT_DOWNLOAD][1].text(),
                         "Authorized audio")
        self.assertEqual(self.window.feature_buttons[MODE_DIRECT_DOWNLOAD].text(),
                         "Authorized audio")
        self.assertEqual(self.window.table.item(0, 0).data(Qt.ItemDataRole.UserRole),
                         str(video.resolve()))
        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(FEATURE_MODES[0]))
        self.assertEqual(self.window._current_paths(), [video.resolve()])

    def test_feature_navigation_resizes_and_is_disabled_during_a_task(self):
        self.window.resize(850, 640)
        self.window.show()
        QApplication.processEvents()
        self.assertTrue(self.window.compact_nav.isVisible())
        self.assertFalse(self.window.sidebar.isVisible())
        self.window.compact_group_combo.setCurrentIndex(
            self.window.compact_group_combo.findData("音频工具"))
        self.window.compact_nav.setCurrentIndex(
            self.window.compact_modes.index(MODE_DIRECT_DOWNLOAD))
        QApplication.processEvents()
        self.assertTrue(self.window.url_input.isVisible())
        self.assertLess(self.window.url_input.mapTo(self.window,
                         self.window.url_input.rect().topLeft()).y(),
                        self.window.start_button.mapTo(self.window,
                         self.window.start_button.rect().topLeft()).y())
        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData("en_US"))
            self.window.theme_combo.setCurrentIndex(
                self.window.theme_combo.findData("dark"))
            QApplication.processEvents()
            self.window.grab().save(str(
                Path(preview_dir) / "navigation-compact-download-en_US-dark.png"))
        self.window._set_running(True)
        self.assertFalse(self.window.compact_nav.isEnabled())
        self.assertFalse(self.window.compact_group_combo.isEnabled())
        self.assertFalse(any(button.isEnabled() for button in
                             self.window.feature_buttons.values()))
        self.window._set_running(False)
        self.assertTrue(self.window.compact_nav.isEnabled())

        self.window.hide()
        self.window.resize(1440, 850)
        self.window._adapt_layout()
        self.window.show()
        QApplication.processEvents()
        self.assertFalse(self.window.sidebar.isHidden())
        self.assertTrue(self.window.compact_navigation.isHidden())
        self.assertTrue(self.window.workspace_wide)
        for button in self.window.feature_buttons.values():
            self.assertGreaterEqual(
                button.width(),
                button.fontMetrics().horizontalAdvance(button.text()) + 38,
                button.text(),
            )
        if preview_dir:
            for mode, theme in (
                (FEATURE_MODES[0], "light"),
                (MODE_EXTRACT, "dark"),
                (MODE_AI_IMAGE_WATERMARK, "dark"),
            ):
                self.window.mode_combo.setCurrentIndex(
                    self.window.mode_combo.findData(mode))
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(str(Path(preview_dir) /
                    f"navigation-wide-{FEATURE_MODES.index(mode)}-en_US-{theme}.png"))

    def test_feature_pages_do_not_overflow_at_layout_breakpoints(self):
        self.window.language_combo.setCurrentIndex(
            self.window.language_combo.findData("en_US"))
        self.window.show()
        for width in (850, 1160, 1280, 1360, 1490, 1530, 1280, 850):
            self.window.resize(width, 850)
            QApplication.processEvents()
            for mode in (MODE_VIDEO, MODE_AUDIO, MODE_AI_IMAGE_WATERMARK):
                self.window.mode_combo.setCurrentIndex(
                    self.window.mode_combo.findData(mode))
                QApplication.processEvents()
                self.assertLessEqual(
                    self.window.content_scroll.widget().width(),
                    self.window.content_scroll.viewport().width(),
                    f"{width}px, {mode}",
                )

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

    def test_authorized_download_mode_adds_safe_direct_links(self):
        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_DIRECT_DOWNLOAD))
        self.assertEqual(self.window.target_combo.currentData(), DIRECT_TARGET)
        self.assertFalse(self.window.target_combo.isEnabled())
        self.assertTrue(self.window.quality_combo.isHidden())
        self.assertFalse(self.window.url_input_panel.isHidden())
        self.assertTrue(self.window.add_files_button.isHidden())
        self.assertTrue(self.window.add_folder_button.isHidden())
        self.assertEqual(self.window.start_button.text(), "开始下载")
        self.assertIn("Spotify", self.window.quality_hint.text())
        self.assertIn("M3U8", self.window.quality_hint.text())

        self.window.url_input.setPlainText(
            "https://media.example.com/first.mp3?token=private\n"
            "https://cdn.example.org/second.flac"
        )
        self.window.add_download_links()
        self.assertEqual(self.window.table.rowCount(), 2)
        self.assertEqual(self.window.table.item(0, 0).text(), "first.mp3")
        self.assertNotIn("private", self.window.table.item(0, 0).toolTip())
        self.assertEqual(self.window.file_count_label.text(), "2 个链接")
        tasks = self.window._current_paths()
        self.assertTrue(all(isinstance(item, DirectDownloadTask) for item in tasks))

        self.window.language_combo.setCurrentIndex(
            self.window.language_combo.findData("en_US"))
        self.assertEqual(self.window.mode_combo.currentText(),
                         "Authorized audio")
        self.assertEqual(self.window.start_button.text(), "Start download")
        self.assertEqual(self.window.file_count_label.text(), "2 link(s)")
        self.assertEqual(self.window.target_combo.currentData(), DIRECT_TARGET)

        self.window.resize(850, 640)
        self.window.show()
        QApplication.processEvents()
        self.assertTrue(self.window.url_input.isVisible())
        self.assertGreaterEqual(self.window.url_input.width(), 420)
        self.assertGreaterEqual(
            self.window.mode_combo.width(),
            self.window.mode_combo.fontMetrics().horizontalAdvance(
                self.window.mode_combo.currentText()) + 44,
        )

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.resize(1280, 860)
            self.window.show()
            for locale, theme in (
                ("zh_CN", "light"), ("zh_CN", "dark"), ("en_US", "light"),
            ):
                self.window.language_combo.setCurrentIndex(
                    self.window.language_combo.findData(locale))
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(str(
                    Path(preview_dir) / f"authorized-download-{locale}-{theme}.png"
                ))

    def test_clarity_enhancement_modes_are_localized_and_filter_inputs(self):
        video = self.root / "soft-video.mp4"
        image = self.root / "soft-image.jpg"
        audio = self.root / "audio.mp3"
        for path in (video, image, audio):
            path.write_bytes(b"test")

        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_VIDEO_ENHANCE))
        self.assertEqual(self.window.target_combo.currentData(), "MP4")
        self.assertEqual(self.window.quality_combo.currentData(), "标准增强")
        self.assertEqual(self.window.resolution_combo.currentData(), "提升至 4K")
        self.assertFalse(self.window.quality_combo.isHidden())
        self.assertFalse(self.window.encoder_combo.isHidden())
        self.assertFalse(self.window.resolution_combo.isHidden())
        self.assertEqual(self.window.quality_label.text(), "增强强度")
        self.assertEqual(self.window.resolution_label.text(), "输出分辨率")
        self.assertTrue(self.window._path_matches_mode(video))
        self.assertFalse(self.window._path_matches_mode(image))
        self.assertFalse(self.window._path_matches_mode(audio))
        self.assertIn("真实细节", self.window.quality_hint.text())
        self.assertEqual(self.window.start_button.text(), "开始增强")

        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_IMAGE_ENHANCE))
        self.assertEqual(self.window.target_combo.currentData(), "PNG（无损）")
        self.assertTrue(self.window.encoder_combo.isHidden())
        self.assertFalse(self.window.resolution_combo.isHidden())
        self.assertTrue(self.window._path_matches_mode(image))
        self.assertFalse(self.window._path_matches_mode(video))
        self.window._add_paths([video, image, audio])
        self.assertEqual(self.window._current_paths(), [image.resolve()])

        for locale, mode_text, start_text in (
            ("en_US", "Enhance image clarity", "Start enhancement"),
            ("zh_TW", "圖片清晰度增強", "開始增強"),
            ("zh_CN", MODE_IMAGE_ENHANCE, "开始增强"),
        ):
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData(locale))
            self.assertEqual(self.window.mode_combo.currentText(), mode_text)
            self.assertEqual(self.window.start_button.text(), start_text)
            self.assertEqual(self.window.mode_combo.currentData(), MODE_IMAGE_ENHANCE)
            self.assertEqual(self.window.quality_combo.currentData(), "标准增强")
            self.assertEqual(self.window.resolution_combo.currentData(), "提升至 4K")

        self.window.language_combo.setCurrentIndex(
            self.window.language_combo.findData("en_US"))
        self.window.resize(850, 640)
        self.window.show()
        QApplication.processEvents()
        self.assertEqual(self.window.field_columns, 2)
        self.assertFalse(self.window.workspace_wide)
        self.assertTrue(self.window.start_button.isVisible())
        for combo in (
            self.window.mode_combo,
            self.window.target_combo,
            self.window.quality_combo,
            self.window.resolution_combo,
        ):
            self.assertGreaterEqual(
                combo.width(),
                combo.fontMetrics().horizontalAdvance(combo.currentText()) + 32,
            )

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.resize(1280, 820)
            self.window.show()
            for locale, theme in (
                ("zh_CN", "light"), ("zh_CN", "dark"), ("en_US", "light"),
            ):
                self.window.language_combo.setCurrentIndex(
                    self.window.language_combo.findData(locale))
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(str(
                    Path(preview_dir) / f"clarity-enhance-{locale}-{theme}.png"
                ))

    def test_visible_watermark_repair_mode_and_editor_are_localized(self):
        image_path = self.root / "authorized-photo.png"
        image = QImage(800, 450, QImage.Format.Format_RGB32)
        painter = QPainter(image)
        painter.fillRect(image.rect(), QColor("#587da3"))
        painter.fillRect(580, 350, 170, 52, QColor("#f7f9fc"))
        painter.end()
        self.assertTrue(image.save(str(image_path)))

        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_IMAGE_WATERMARK_REPAIR))
        self.assertEqual(self.window.target_combo.currentData(), "PNG（无损）")
        self.assertEqual(self.window.quality_combo.currentData(), "标准修复")
        self.assertFalse(self.window.quality_combo.isHidden())
        self.assertTrue(self.window.encoder_combo.isHidden())
        self.assertTrue(self.window.resolution_combo.isHidden())
        self.assertFalse(self.window.watermark_region_panel.isHidden())
        self.assertEqual(self.window.quality_label.text(), "修复边缘")
        self.assertEqual(self.window.start_button.text(), "开始修复")
        self.assertIn("C2PA", self.window.quality_hint.text())
        self.assertTrue(self.window._path_matches_mode(image_path))

        self.window._add_paths([image_path])
        self.assertTrue(self.window.watermark_edit_button.isEnabled())
        self.window.watermark_regions = (
            WatermarkRegion(0.70, 0.72, 0.25, 0.18),
        )
        self.window._update_watermark_region_ui()
        self.assertEqual(self.window.watermark_region_label.text(), "已选择 1 个区域")

        for locale, mode_text, start_text in (
            ("en_US", "Repair visible image watermark areas", "Start repair"),
            ("zh_TW", "圖片可見浮水印區域修復", "開始修復"),
            ("zh_CN", MODE_IMAGE_WATERMARK_REPAIR, "开始修复"),
        ):
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData(locale))
            self.assertEqual(self.window.mode_combo.currentText(), mode_text)
            self.assertEqual(self.window.start_button.text(), start_text)
            self.assertEqual(
                self.window.mode_combo.currentData(), MODE_IMAGE_WATERMARK_REPAIR)
            self.assertEqual(self.window.quality_combo.currentData(), "标准修复")

        dialog = WatermarkRegionDialog(
            image_path,
            self.window.watermark_regions,
            self.window.language,
            self.window,
        )
        self.addCleanup(dialog.close)
        self.assertEqual(len(dialog.regions()), 1)
        self.assertTrue(dialog.save_button.isEnabled())
        self.assertIn("1", dialog.region_label.text())

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.resize(1280, 860)
            self.window.show()
            for locale, theme in (
                ("zh_CN", "light"), ("zh_CN", "dark"), ("en_US", "light"),
            ):
                self.window.language_combo.setCurrentIndex(
                    self.window.language_combo.findData(locale))
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(str(
                    Path(preview_dir) / f"watermark-repair-{locale}-{theme}.png"
                ))
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData("zh_CN"))
            dialog.close()
            dialog = WatermarkRegionDialog(
                image_path,
                self.window.watermark_regions,
                self.window.language,
                self.window,
            )
            self.addCleanup(dialog.close)
            dialog.resize(940, 700)
            dialog.show()
            QApplication.processEvents()
            dialog.grab().save(str(
                Path(preview_dir) / "watermark-region-editor-zh_CN.png"
            ))

    def test_hidden_watermark_mode_is_localized_and_metadata_choice_is_saved(self):
        source = self.root / "owned-photo.png"
        image = QImage(96, 64, QImage.Format.Format_ARGB32)
        image.fill(QColor("#4477aa"))
        self.assertTrue(image.save(str(source)))
        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_IMAGE_HIDDEN_WATERMARK))
        self.window._add_paths([source])
        self.assertEqual(self.window.quality_combo.currentData(), "标准处理")
        self.assertEqual(self.window.target_combo.currentData(), "PNG（无损）")
        self.assertFalse(self.window.hidden_metadata_checkbox.isHidden())
        self.assertTrue(self.window.watermark_region_panel.isHidden())
        self.assertTrue(self.window._path_matches_mode(source))
        self.assertIn("C2PA", self.window.quality_hint.text())
        self.assertFalse(self.window.hidden_metadata_checkbox.isChecked())
        self.window.hidden_metadata_checkbox.setChecked(True)
        self.window._save_settings()
        self.assertEqual(self.settings.value("hidden_watermark/strip_metadata",
                                             type=bool), True)

        for locale, text in (("en_US", "Process hidden image watermarks"),
                             ("zh_TW", "圖片隱藏浮水印處理"),
                             ("zh_CN", MODE_IMAGE_HIDDEN_WATERMARK)):
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData(locale))
            self.assertEqual(self.window.mode_combo.currentText(), text)
            self.assertEqual(self.window.mode_combo.currentData(), MODE_IMAGE_HIDDEN_WATERMARK)
            self.assertTrue(self.window.hidden_metadata_checkbox.isChecked())

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.resize(1280, 820)
            self.window.show()
            for theme in ("light", "dark"):
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(str(
                    Path(preview_dir) / f"hidden-watermark-zh_CN-{theme}.png"
                ))

    def test_ai_watermark_mode_reuses_selection_and_is_localized(self):
        source = self.root / "ai-owned.png"
        image = QImage(320, 192, QImage.Format.Format_ARGB32)
        image.fill(QColor("#50729e"))
        self.assertTrue(image.save(str(source)))
        self.window.mode_combo.setCurrentIndex(
            self.window.mode_combo.findData(MODE_AI_IMAGE_WATERMARK))
        self.window._add_paths([source])
        self.assertEqual(self.window.target_combo.currentData(), "PNG（无损）")
        self.assertEqual(self.window.quality_combo.currentData(), "标准修复")
        self.assertFalse(self.window.watermark_region_panel.isHidden())
        self.assertFalse(self.window.ai_hidden_checkbox.isHidden())
        self.assertTrue(self.window.hidden_metadata_checkbox.isHidden())
        self.assertTrue(self.window.watermark_edit_button.isEnabled())
        self.assertIn("SynthID", self.window.quality_hint.text())
        self.assertFalse(self.window.ai_hidden_checkbox.isChecked())
        self.window.ai_hidden_checkbox.setChecked(True)
        self.window._save_settings()
        self.assertTrue(self.settings.value("ai_watermark/process_hidden", type=bool))

        dialog = WatermarkRegionDialog(
            source, (), self.window.language, self.window, ai_mode=True)
        self.addCleanup(dialog.close)
        self.assertIn("AI", dialog.windowTitle())
        dialog.canvas.set_regions((WatermarkRegion(.72, .75, .20, .15),))
        self.assertTrue(dialog.save_button.isEnabled())

        for locale, mode_text in (
            ("en_US", "Repair AI image watermarks"),
            ("zh_TW", "AI 圖片浮水印修復"),
            ("zh_CN", MODE_AI_IMAGE_WATERMARK),
        ):
            self.window.language_combo.setCurrentIndex(
                self.window.language_combo.findData(locale))
            self.assertEqual(self.window.mode_combo.currentText(), mode_text)
            self.assertEqual(self.window.mode_combo.currentData(), MODE_AI_IMAGE_WATERMARK)
            self.assertTrue(self.window.ai_hidden_checkbox.isChecked())

        preview_dir = os.environ.get("UI_SCREENSHOT_DIR")
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            self.window.resize(1280, 860)
            self.window.show()
            for locale, theme in (("zh_CN", "light"), ("en_US", "dark")):
                self.window.language_combo.setCurrentIndex(
                    self.window.language_combo.findData(locale))
                self.window.theme_combo.setCurrentIndex(
                    self.window.theme_combo.findData(theme))
                QApplication.processEvents()
                self.window.grab().save(str(
                    Path(preview_dir) / f"ai-watermark-{locale}-{theme}.png"
                ))

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
