from __future__ import annotations

import os
import sys
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QLocale, QSettings, QSize, QThread, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QAction, QBrush, QColor, QCloseEvent, QDesktopServices, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QGuiApplication, QResizeEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine import (
    AUDIO_TARGETS,
    COMPRESS_TARGETS,
    ENCODER_PRESETS,
    EXTRACT_TARGETS,
    MODE_AUDIO,
    MODE_COMPRESS,
    MODE_EXTRACT,
    MODE_VIDEO,
    QUALITY_PRESETS,
    RESOLUTION_PRESETS,
    SUPPORTED_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VIDEO_TARGETS,
    ConversionCancelled,
    ConversionOptions,
    convert_file,
    self_test as media_self_test,
)
from music_unlock import (
    MODE_MUSIC_UNLOCK,
    UNLOCK_TARGET,
    is_unlockable_path,
    self_test as music_unlock_self_test,
    supported_unlock_suffix,
    unlock_file_patterns,
    unlock_music_file,
)
from direct_download import (
    DIRECT_TARGET,
    MODE_DIRECT_DOWNLOAD,
    DirectDownloadCancelled,
    DirectDownloadTask,
    download_source_label,
    download_direct_audio,
    make_download_task,
    split_url_input,
)
from clarity_enhance import (
    ENHANCE_RESOLUTIONS,
    ENHANCE_STRENGTHS,
    IMAGE_ENHANCE_TARGETS,
    IMAGE_EXTENSIONS,
    MODE_IMAGE_ENHANCE,
    MODE_VIDEO_ENHANCE,
    VIDEO_ENHANCE_TARGETS,
    enhance_media_file,
)
from watermark_repair import (
    MODE_IMAGE_WATERMARK_REPAIR,
    WATERMARK_REPAIR_STRENGTHS,
    WATERMARK_REPAIR_TARGETS,
    WatermarkRegion,
    repair_visible_watermark,
)
from watermark_editor import WatermarkRegionDialog
from version import APP_NAME, APP_VERSION
from i18n import (
    LANGUAGE_LABELS, SUPPORTED_LANGUAGES, language_for_system_locale, translate,
)
from ui_theme import COLORS, make_palette, make_stylesheet
from ui_components import (
    BackgroundCanvas, BrandMark, EmptyDropZone, MediaTableDelegate, make_icon,
)


def readable_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TB"


def display_file_type(path: Path) -> str:
    unlock_suffix = supported_unlock_suffix(path)
    if unlock_suffix and len(unlock_suffix) > len(path.suffix):
        return unlock_suffix.upper().lstrip(".")
    return path.suffix.upper().lstrip(".")


class BatchWorker(QObject):
    item_started = Signal(int)
    item_progress = Signal(int, int, str)
    item_finished = Signal(int, bool, str, str)
    completed = Signal(bool, int, int)

    def __init__(
        self,
        paths: list[Path | DirectDownloadTask],
        options: ConversionOptions,
        watermark_regions: tuple[WatermarkRegion, ...] = (),
    ):
        super().__init__()
        self.paths = paths
        self.options = options
        self.watermark_regions = watermark_regions
        self.cancel_event = Event()

    def request_cancel(self) -> None:
        self.cancel_event.set()

    @Slot()
    def run(self) -> None:
        successes = 0
        failures = 0
        cancelled = False

        for index, path in enumerate(self.paths):
            if self.cancel_event.is_set():
                cancelled = True
                break

            self.item_started.emit(index)
            try:
                progress = lambda percent, text, row=index: self.item_progress.emit(
                    row, percent, text)
                if self.options.mode == MODE_DIRECT_DOWNLOAD:
                    result = download_direct_audio(
                        path,
                        self.options.output_dir,
                        self.options.locale,
                        progress,
                        self.cancel_event,
                    )
                elif self.options.mode == MODE_MUSIC_UNLOCK:
                    result = unlock_music_file(
                        path,
                        self.options.output_dir,
                        self.options.locale,
                        progress,
                        self.cancel_event,
                    )
                elif self.options.mode in {MODE_VIDEO_ENHANCE, MODE_IMAGE_ENHANCE}:
                    result = enhance_media_file(
                        path,
                        self.options,
                        progress,
                        self.cancel_event,
                    )
                elif self.options.mode == MODE_IMAGE_WATERMARK_REPAIR:
                    result = repair_visible_watermark(
                        path,
                        self.options,
                        self.watermark_regions,
                        progress,
                        self.cancel_event,
                    )
                else:
                    result = convert_file(
                        path,
                        self.options,
                        progress,
                        self.cancel_event,
                    )
                successes += 1
                self.item_finished.emit(
                    index,
                    True,
                    result.size_message,
                    str(result.output_path),
                )
            except (ConversionCancelled, DirectDownloadCancelled):
                cancelled = True
                self.item_finished.emit(index, False,
                                        translate("已取消", self.options.locale), "")
                break
            except Exception as exc:
                failures += 1
                detail = str(exc).strip() or exc.__class__.__name__
                self.item_finished.emit(index, False, detail, "")

        self.completed.emit(cancelled, successes, failures)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(850, 600)
        self.resize(1200, 800)
        self.setAcceptDrops(True)

        self.settings = QSettings("UniversalMediaToolbox", "UniversalMediaToolbox")
        ui_languages = QLocale.system().uiLanguages()
        preferred_locale = (
            ui_languages[0] if ui_languages else QLocale.system().name()
        )
        saved_locale = str(self.settings.value(
            "locale", language_for_system_locale(preferred_locale)))
        self.language = saved_locale if saved_locale in SUPPORTED_LANGUAGES else "zh_CN"
        saved_theme = str(self.settings.value("appearance/theme", "system"))
        self.theme = saved_theme if saved_theme in {"system", "light", "dark"} else "system"
        self.background_path = ""
        self.watermark_regions: tuple[WatermarkRegion, ...] = ()
        self.worker: BatchWorker | None = None
        self.worker_thread: QThread | None = None
        self.progress_bars: dict[int, QProgressBar] = {}

        self._build_actions()
        self._build_ui()
        self._restore_settings()
        self._restore_background()
        self._update_mode()
        last_target = str(self.settings.value("target", ""))
        target_index = self.target_combo.findData(last_target)
        if target_index >= 0:
            self.target_combo.setCurrentIndex(target_index)
        self._retranslate_ui()
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._apply_theme)
        self._set_os_theme_preference()
        self._apply_theme()
        self.statusBar().showMessage(self._ready_message())

    def _t(self, key: str, **values: object) -> str:
        return translate(key, self.language, **values)

    def _is_unlock_mode(self) -> bool:
        return self.mode_combo.currentData() == MODE_MUSIC_UNLOCK

    def _is_download_mode(self) -> bool:
        return self.mode_combo.currentData() == MODE_DIRECT_DOWNLOAD

    def _is_video_enhance_mode(self) -> bool:
        return self.mode_combo.currentData() == MODE_VIDEO_ENHANCE

    def _is_image_enhance_mode(self) -> bool:
        return self.mode_combo.currentData() == MODE_IMAGE_ENHANCE

    def _is_watermark_repair_mode(self) -> bool:
        return self.mode_combo.currentData() == MODE_IMAGE_WATERMARK_REPAIR

    def _is_enhance_mode(self) -> bool:
        return self.mode_combo.currentData() in {
            MODE_VIDEO_ENHANCE, MODE_IMAGE_ENHANCE,
        }

    def _ready_message(self) -> str:
        if self._is_download_mode():
            key = "就绪：可粘贴公开的无 DRM 音频直链"
        elif self._is_unlock_mode():
            key = "就绪：可拖入待解锁的本地音乐文件"
        elif self._is_video_enhance_mode():
            key = "就绪：可拖入要增强的视频文件"
        elif self._is_image_enhance_mode():
            key = "就绪：可拖入要增强的图片文件"
        elif self._is_watermark_repair_mode():
            key = "就绪：添加图片并框选可见水印区域"
        else:
            key = "就绪：可直接拖入音频或视频文件"
        return self._t(key)

    def _notify(self, icon: QMessageBox.Icon, title: str, message: str) -> None:
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(message)
        box.addButton(self._t("确定"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    @Slot(int)
    def _change_language(self, _index: int) -> None:
        selected = self.language_combo.currentData()
        if selected not in SUPPORTED_LANGUAGES or selected == self.language or self.worker:
            return
        self.language = selected
        self.settings.setValue("locale", selected)
        self._retranslate_ui()
        self.statusBar().showMessage(self._ready_message())

    @Slot(int)
    def _change_theme(self, _index: int) -> None:
        selected = self.theme_combo.currentData()
        if selected not in {"system", "light", "dark"} or selected == self.theme:
            return
        self.theme = selected
        self.settings.setValue("appearance/theme", selected)
        self._set_os_theme_preference()
        self._apply_theme()

    def _restore_background(self) -> None:
        saved = str(self.settings.value("appearance/background_image", "") or "").strip()
        if saved and Path(saved).is_file() and self.background_canvas.load_image(saved):
            self.background_path = saved
        else:
            self.background_path = ""
            self.background_canvas.clear_image()
            if saved:
                self.settings.remove("appearance/background_image")
        self._update_background_ui()

    def _update_background_ui(self) -> None:
        if not hasattr(self, "background_button"):
            return
        active = self.background_canvas.has_image()
        self.background_button.setText(self._t(
            "自定义图片" if active else "默认背景"
        ))
        self.background_button.setToolTip(
            self.background_path if active else self._t("选择背景图片…")
        )
        self.remove_background_action.setEnabled(active)

    @Slot()
    def choose_background_image(self) -> None:
        current = Path(self.background_path).parent if self.background_path else Path.home() / "Pictures"
        if not current.is_dir():
            current = Path.home()
        selected, _ = QFileDialog.getOpenFileName(
            self,
            self._t("选择背景图片"),
            str(current),
            self._t("图片文件") + " (*.png *.jpg *.jpeg *.webp *.bmp);;"
            + self._t("所有文件") + " (*.*)",
        )
        if not selected:
            return
        path = str(Path(selected).resolve())
        if not self.background_canvas.load_image(path):
            self._notify(
                QMessageBox.Icon.Warning,
                self._t("无法使用背景图片"),
                self._t("所选文件不是可读取的图片。"),
            )
            return
        self.background_path = path
        self.settings.setValue("appearance/background_image", path)
        self._update_background_ui()
        self._apply_theme()
        self.statusBar().showMessage(self._t("自定义背景已启用"), 4000)

    @Slot()
    def remove_background_image(self) -> None:
        self.background_path = ""
        self.background_canvas.clear_image()
        self.settings.remove("appearance/background_image")
        self._update_background_ui()
        self._apply_theme()
        self.statusBar().showMessage(self._t("已恢复默认背景"), 4000)

    def _set_os_theme_preference(self) -> None:
        scheme = {
            "system": Qt.ColorScheme.Unknown,
            "light": Qt.ColorScheme.Light,
            "dark": Qt.ColorScheme.Dark,
        }[self.theme]
        QGuiApplication.styleHints().setColorScheme(scheme)

    @Slot()
    def _apply_theme(self, *_args: object) -> None:
        system_dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        effective = self.theme if self.theme != "system" else ("dark" if system_dark else "light")
        self.effective_theme = effective
        self.background_canvas.set_theme(effective)
        app = QApplication.instance()
        if app:
            app.setPalette(make_palette(effective))
            app.setStyleSheet(make_stylesheet(
                effective, custom_background=self.background_canvas.has_image()
            ))
        colors = COLORS[effective]
        self.brand_mark.set_accent(colors["primary"])
        self.empty_state.set_theme(colors)
        self.table_delegate.set_colors(colors)
        self.table.viewport().update()
        self._apply_icons(colors)
        self._refresh_status_colors()

    def _apply_icons(self, colors: dict[str, str]) -> None:
        for widget, name, tone in self._icon_bindings:
            icon_color = {
                "primary": "#ffffff",
                "danger": colors["error"],
                "normal": colors["muted"],
            }[tone]
            widget.setIcon(make_icon(name, icon_color, 17))
            widget.setIconSize(QSize(17, 17))
        for label, name in self._section_icons:
            label.setPixmap(make_icon(name, colors["accent"], 18).pixmap(18, 18))
        self.add_action.setIcon(make_icon("add", colors["muted"], 16))
        self.add_folder_action.setIcon(make_icon("folder", colors["muted"], 16))
        self.choose_background_action.setIcon(make_icon("image", colors["muted"], 16))
        self.remove_background_action.setIcon(make_icon("clear", colors["muted"], 16))
        self.notices_action.setIcon(make_icon("shield", colors["muted"], 16))
        self.about_action.setIcon(make_icon("info", colors["muted"], 16))

    def _refresh_status_colors(self) -> None:
        color = COLORS.get(getattr(self, "effective_theme", "light"), COLORS["light"])
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 3)
            if item:
                state = item.data(Qt.ItemDataRole.UserRole)
                if state in ("success", "failed"):
                    item.setForeground(QBrush(QColor(color["success" if state == "success" else "error"])))

    def _set_task_state(self, state: str) -> None:
        self.overall_label.setProperty("state", state)
        self.overall_label.style().unpolish(self.overall_label)
        self.overall_label.style().polish(self.overall_label)

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(f"{self._t(APP_NAME)} {APP_VERSION}")
        for action, key in (
            (self.add_action, "添加文件"),
            (self.add_folder_action, "添加文件夹"),
            (self.choose_background_action, "选择背景图片…"),
            (self.remove_background_action, "移除自定义背景"),
            (self.exit_action, "退出"),
            (self.notices_action, "第三方许可"),
            (self.about_action, "关于"),
        ):
            action.setText(self._t(key))
        self.file_menu.setTitle(self._t("文件"))
        self.appearance_menu.setTitle(self._t("外观"))
        self.help_menu.setTitle(self._t("帮助"))
        for widget, key in (
            (self.hero_title, APP_NAME),
            (self.hero_subtitle, "格式转换 · 4K 清晰度增强 · 音乐解锁 · 授权下载"),
            (self.privacy_badge, "本地处理 · 文件不会上传"),
            (self.language_label, "语言"),
            (self.theme_label, "外观"),
            (self.background_label, "背景"),
            (self.files_title, "待处理文件"),
            (self.files_hint, "将文件或文件夹拖入此处，或使用下方按钮添加"),
            (self.options_title, "处理设置"),
            (self.options_hint, "按任务需要选择输出格式与质量"),
            (self.add_files_button, "添加文件"),
            (self.add_folder_button, "添加文件夹"),
            (self.add_links_button, "添加链接"),
            (self.remove_button, "移除选中"),
            (self.clear_button, "清空列表"),
            (self.mode_label, "任务类型"),
            (self.target_label, "输出格式"),
            (self.quality_label, "质量方案"),
            (self.encoder_label, "视频编码"),
            (self.resolution_label, "分辨率限制"),
            (self.watermark_edit_button, "框选修复区域"),
            (self.output_label, "输出文件夹"),
            (self.browse_output_button, "浏览…"),
            (self.open_output_button, "打开目录"),
            (self.cancel_button, "取消任务"),
            (self.start_button, "开始处理"),
        ):
            widget.setText(self._t(key))
        self.empty_state.set_texts(
            self._t("把媒体文件拖到这里"),
            self._t("支持常见音频和视频格式，也可以直接拖入整个文件夹"),
            self._t("选择文件"),
        )
        for index, key in enumerate(("跟随系统", "浅色", "深色")):
            self.theme_combo.setItemText(index, self._t(key))
        for combo in (
            self.mode_combo, self.target_combo, self.quality_combo,
            self.encoder_combo, self.resolution_combo,
        ):
            for index in range(combo.count()):
                text = self._t(str(combo.itemData(index)))
                combo.setItemText(index, text)
                combo.setItemData(index, text, Qt.ItemDataRole.ToolTipRole)
        for combo in (self.language_combo, self.theme_combo):
            for index in range(combo.count()):
                combo.setItemData(index, combo.itemText(index), Qt.ItemDataRole.ToolTipRole)
        self._update_background_ui()
        self.output_edit.setPlaceholderText(self._t("选择输出目录"))
        self.url_input.setPlaceholderText(self._t(
            "每行粘贴一个公开音频直链，例如 https://example.com/song.mp3"))
        self.table.setHorizontalHeaderLabels([
            self._t(key) for key in ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
        ])
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 3)
            if item and item.data(Qt.ItemDataRole.UserRole) == "pending":
                item.setText(self._t("等待处理"))
        self._update_count()
        self._update_watermark_region_ui()
        self._update_quality_hint()
        self._update_mode_copy()
        if not self.worker:
            self.overall_label.setText(self._t("等待任务"))

    def _build_actions(self) -> None:
        self.add_action = QAction(self._t("添加文件"), self)
        self.add_action.setShortcut("Ctrl+O")
        self.add_action.triggered.connect(self.add_files)

        self.add_folder_action = QAction(self._t("添加文件夹"), self)
        self.add_folder_action.setShortcut("Ctrl+Shift+O")
        self.add_folder_action.triggered.connect(self.add_folder)

        self.choose_background_action = QAction(self._t("选择背景图片…"), self)
        self.choose_background_action.setShortcut("Ctrl+Shift+B")
        self.choose_background_action.triggered.connect(self.choose_background_image)

        self.remove_background_action = QAction(self._t("移除自定义背景"), self)
        self.remove_background_action.triggered.connect(self.remove_background_image)
        self.remove_background_action.setEnabled(False)

        self.exit_action = QAction(self._t("退出"), self)
        self.exit_action.setShortcut("Alt+F4")
        self.exit_action.triggered.connect(self.close)

        self.notices_action = QAction(self._t("第三方许可"), self)
        self.notices_action.triggered.connect(self.open_notices)

        self.about_action = QAction(self._t("关于"), self)
        self.about_action.triggered.connect(self.show_about)

        self.file_menu = self.menuBar().addMenu(self._t("文件"))
        self.file_menu.addAction(self.add_action)
        self.file_menu.addAction(self.add_folder_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.appearance_menu = self.menuBar().addMenu(self._t("外观"))
        self.appearance_menu.addAction(self.choose_background_action)
        self.appearance_menu.addAction(self.remove_background_action)

        self.help_menu = self.menuBar().addMenu(self._t("帮助"))
        self.help_menu.addAction(self.notices_action)
        self.help_menu.addAction(self.about_action)

    def _build_ui(self) -> None:
        central = BackgroundCanvas()
        self.background_canvas = central
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.content_scroll = QScrollArea()
        self.content_scroll.setObjectName("ContentScroll")
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_scroll.setAutoFillBackground(False)
        self.content_scroll.viewport().setAutoFillBackground(False)
        content = QWidget()
        content.setObjectName("Content")
        content.setAutoFillBackground(False)
        self.content_root = QVBoxLayout(content)
        self.content_root.setContentsMargins(24, 20, 24, 20)
        self.content_root.setSpacing(16)

        self.header_panel = QFrame()
        self.header_panel.setObjectName("HeaderPanel")
        self.header_layout = QGridLayout(self.header_panel)
        self.header_layout.setContentsMargins(20, 17, 20, 17)
        self.header_layout.setHorizontalSpacing(24)
        self.header_layout.setVerticalSpacing(14)

        brand_block = QWidget()
        brand_layout = QHBoxLayout(brand_block)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(14)
        self.brand_mark = BrandMark()
        brand_layout.addWidget(self.brand_mark, 0, Qt.AlignmentFlag.AlignTop)
        brand_copy = QVBoxLayout()
        brand_copy.setContentsMargins(0, 0, 0, 0)
        brand_copy.setSpacing(3)
        title_row = QHBoxLayout()
        title_row.setSpacing(9)
        self.hero_title = QLabel(self._t(APP_NAME))
        self.hero_title.setObjectName("AppTitle")
        title_row.addWidget(self.hero_title)
        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setObjectName("AppVersion")
        title_row.addWidget(self.version_label, 0, Qt.AlignmentFlag.AlignBottom)
        title_row.addStretch()
        brand_copy.addLayout(title_row)
        self.hero_subtitle = QLabel(self._t(
            "格式转换 · 4K 清晰度增强 · 音乐解锁 · 授权下载"))
        self.hero_subtitle.setObjectName("AppSubtitle")
        self.hero_subtitle.setWordWrap(True)
        brand_copy.addWidget(self.hero_subtitle)
        self.privacy_badge = QLabel(self._t("本地处理 · 文件不会上传"))
        self.privacy_badge.setObjectName("PrivacyBadge")
        self.privacy_badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        brand_copy.addWidget(self.privacy_badge, 0, Qt.AlignmentFlag.AlignLeft)
        brand_layout.addLayout(brand_copy, 1)

        self.header_controls = QWidget()
        self.header_controls.setObjectName("HeaderControls")
        controls_layout = QHBoxLayout(self.header_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)
        language_group = QVBoxLayout()
        language_group.setContentsMargins(0, 0, 0, 0)
        language_group.setSpacing(5)
        self.language_label = QLabel(self._t("语言"))
        self.language_label.setObjectName("FieldLabel")
        language_group.addWidget(self.language_label)
        self.language_combo = QComboBox()
        for locale in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(LANGUAGE_LABELS[locale], locale)
        self.language_combo.setCurrentIndex(self.language_combo.findData(self.language))
        self.language_combo.setMinimumWidth(136)
        self.language_combo.currentIndexChanged.connect(self._change_language)
        language_group.addWidget(self.language_combo)
        controls_layout.addLayout(language_group)
        theme_group = QVBoxLayout()
        theme_group.setContentsMargins(0, 0, 0, 0)
        theme_group.setSpacing(5)
        self.theme_label = QLabel(self._t("外观"))
        self.theme_label.setObjectName("FieldLabel")
        theme_group.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        for value, key in (("system", "跟随系统"), ("light", "浅色"), ("dark", "深色")):
            self.theme_combo.addItem(self._t(key), value)
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(self.theme))
        self.theme_combo.setMinimumWidth(136)
        self.theme_combo.currentIndexChanged.connect(self._change_theme)
        theme_group.addWidget(self.theme_combo)
        controls_layout.addLayout(theme_group)
        background_group = QVBoxLayout()
        background_group.setContentsMargins(0, 0, 0, 0)
        background_group.setSpacing(5)
        self.background_label = QLabel(self._t("背景"))
        self.background_label.setObjectName("FieldLabel")
        background_group.addWidget(self.background_label)
        self.background_button = QPushButton(self._t("默认背景"))
        self.background_button.setProperty("role", "toolbar")
        self.background_button.setMinimumWidth(148)
        self.background_menu = QMenu(self.background_button)
        self.background_menu.addAction(self.choose_background_action)
        self.background_menu.addAction(self.remove_background_action)
        self.background_button.setMenu(self.background_menu)
        background_group.addWidget(self.background_button)
        controls_layout.addLayout(background_group)
        self.header_layout.addWidget(brand_block, 0, 0)
        self.header_layout.addWidget(
            self.header_controls, 0, 1,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        self.header_layout.setColumnStretch(0, 1)
        self.content_root.addWidget(self.header_panel)

        self.workspace_layout = QGridLayout()
        self.workspace_layout.setContentsMargins(0, 0, 0, 0)
        self.workspace_layout.setHorizontalSpacing(16)
        self.workspace_layout.setVerticalSpacing(16)

        self.file_panel = QFrame()
        self.file_panel.setObjectName("Panel")
        file_layout = QVBoxLayout(self.file_panel)
        file_layout.setContentsMargins(18, 17, 18, 18)
        file_layout.setSpacing(13)
        file_heading = QHBoxLayout()
        file_heading.setSpacing(10)
        self.file_section_icon = QLabel()
        self.file_section_icon.setObjectName("SectionIcon")
        self.file_section_icon.setFixedSize(34, 34)
        self.file_section_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_heading.addWidget(self.file_section_icon)
        file_heading_copy = QVBoxLayout()
        file_heading_copy.setContentsMargins(0, 0, 0, 0)
        file_heading_copy.setSpacing(2)
        self.files_title = QLabel(self._t("待处理文件"))
        self.files_title.setObjectName("SectionTitle")
        file_heading_copy.addWidget(self.files_title)
        self.files_hint = QLabel(self._t("将文件或文件夹拖入此处，或使用下方按钮添加"))
        self.files_hint.setObjectName("SectionHint")
        self.files_hint.setWordWrap(True)
        file_heading_copy.addWidget(self.files_hint)
        file_heading.addLayout(file_heading_copy, 1)
        file_heading.addStretch()
        self.file_count_label = QLabel(self._t("{count} 个文件", count=0))
        self.file_count_label.setObjectName("FileCount")
        file_heading.addWidget(self.file_count_label)
        file_layout.addLayout(file_heading)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.add_files_button = QPushButton(self._t("添加文件"))
        self.add_folder_button = QPushButton(self._t("添加文件夹"))
        self.remove_button = QPushButton(self._t("移除选中"))
        self.clear_button = QPushButton(self._t("清空列表"))
        for button in (self.add_files_button, self.add_folder_button,
                       self.remove_button, self.clear_button):
            button.setProperty("role", "toolbar")
        self.remove_button.setProperty("role", "danger")
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.clear_files)
        toolbar.addWidget(self.add_files_button)
        toolbar.addWidget(self.add_folder_button)
        toolbar.addWidget(self.remove_button)
        toolbar.addWidget(self.clear_button)
        toolbar.addStretch()
        file_layout.addLayout(toolbar)

        self.url_input_panel = QFrame()
        self.url_input_panel.setObjectName("UrlInputPanel")
        url_input_layout = QHBoxLayout(self.url_input_panel)
        url_input_layout.setContentsMargins(12, 12, 12, 12)
        url_input_layout.setSpacing(10)
        self.url_input = QPlainTextEdit()
        self.url_input.setObjectName("UrlInput")
        self.url_input.setPlaceholderText(self._t(
            "每行粘贴一个公开音频直链，例如 https://example.com/song.mp3"))
        self.url_input.setMinimumHeight(68)
        self.url_input.setMaximumHeight(88)
        self.url_input.setTabChangesFocus(True)
        self.add_links_button = QPushButton(self._t("添加链接"))
        self.add_links_button.setProperty("role", "accentSoft")
        self.add_links_button.setMinimumWidth(112)
        self.add_links_button.clicked.connect(self.add_download_links)
        url_input_layout.addWidget(self.url_input, 1)
        url_input_layout.addWidget(
            self.add_links_button, 0, Qt.AlignmentFlag.AlignBottom)
        self.url_input_panel.setVisible(False)
        file_layout.addWidget(self.url_input_panel)

        self.file_stack = QStackedWidget()
        self.file_stack.setMinimumHeight(280)
        self.empty_state = EmptyDropZone()
        self.empty_state.add_requested.connect(self.add_files)
        self.file_stack.addWidget(self.empty_state)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            self._t(key) for key in ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._table_context_menu)
        self.table.cellDoubleClicked.connect(self._table_double_clicked)
        self.table.itemSelectionChanged.connect(self._update_selection_actions)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(47)
        self.table.setMinimumHeight(280)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # File extensions are short, but the custom pill needs more breathing
        # room than the plain-text size hint reported by the default delegate.
        # Keep a stable initial width so WAV/MKV/MPEG never render as W…/M….
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 94)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table_delegate = MediaTableDelegate(COLORS["light"], self.table)
        self.table.setItemDelegate(self.table_delegate)
        self.file_stack.addWidget(self.table)
        file_layout.addWidget(self.file_stack, 1)

        self.options_panel = QFrame()
        self.options_panel.setObjectName("Panel")
        options_root = QVBoxLayout(self.options_panel)
        options_root.setContentsMargins(18, 17, 18, 18)
        options_root.setSpacing(13)
        options_heading = QHBoxLayout()
        options_heading.setSpacing(10)
        self.options_section_icon = QLabel()
        self.options_section_icon.setObjectName("SectionIcon")
        self.options_section_icon.setFixedSize(34, 34)
        self.options_section_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        options_heading.addWidget(self.options_section_icon)
        options_heading_copy = QVBoxLayout()
        options_heading_copy.setContentsMargins(0, 0, 0, 0)
        options_heading_copy.setSpacing(2)
        self.options_title = QLabel(self._t("处理设置"))
        self.options_title.setObjectName("SectionTitle")
        options_heading_copy.addWidget(self.options_title)
        self.options_hint = QLabel(self._t("按任务需要选择输出格式与质量"))
        self.options_hint.setObjectName("SectionHint")
        self.options_hint.setWordWrap(True)
        options_heading_copy.addWidget(self.options_hint)
        options_heading.addLayout(options_heading_copy, 1)
        options_root.addLayout(options_heading)
        options_root.addSpacing(2)
        self.fields_layout = QGridLayout()
        self.fields_layout.setHorizontalSpacing(16)
        self.fields_layout.setVerticalSpacing(7)
        options_root.addLayout(self.fields_layout)

        self.mode_combo = QComboBox()
        for item in (
            MODE_VIDEO, MODE_VIDEO_ENHANCE, MODE_IMAGE_ENHANCE,
            MODE_IMAGE_WATERMARK_REPAIR,
            MODE_AUDIO, MODE_EXTRACT, MODE_COMPRESS,
            MODE_MUSIC_UNLOCK, MODE_DIRECT_DOWNLOAD,
        ):
            self.mode_combo.addItem(self._t(item), item)
        self.target_combo = QComboBox()
        self.quality_combo = QComboBox()
        for item in QUALITY_PRESETS:
            self.quality_combo.addItem(self._t(item), item)
        self.encoder_combo = QComboBox()
        for item in ENCODER_PRESETS:
            self.encoder_combo.addItem(self._t(item), item)
        self.resolution_combo = QComboBox()
        for item in RESOLUTION_PRESETS:
            self.resolution_combo.addItem(self._t(item), item)

        self.mode_combo.currentIndexChanged.connect(self._update_mode)
        self.quality_combo.currentIndexChanged.connect(self._update_quality_hint)
        self.target_combo.currentIndexChanged.connect(self._update_quality_hint)

        self.mode_label = QLabel(self._t("任务类型"))
        self.target_label = QLabel(self._t("输出格式"))
        self.quality_label = QLabel(self._t("质量方案"))
        self.encoder_label = QLabel(self._t("视频编码"))
        self.resolution_label = QLabel(self._t("分辨率限制"))
        self.field_pairs = (
            (self.mode_label, self.mode_combo),
            (self.target_label, self.target_combo),
            (self.quality_label, self.quality_combo),
            (self.encoder_label, self.encoder_combo),
            (self.resolution_label, self.resolution_combo),
        )
        for label, combo in self.field_pairs:
            label.setObjectName("FieldLabel")
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._adapt_columns()

        self.quality_hint = QLabel()
        self.quality_hint.setWordWrap(True)
        self.quality_hint.setObjectName("QualityHint")
        options_root.addWidget(self.quality_hint)
        options_root.addSpacing(1)

        self.watermark_region_panel = QFrame()
        self.watermark_region_panel.setObjectName("WatermarkControlPanel")
        watermark_layout = QHBoxLayout(self.watermark_region_panel)
        watermark_layout.setContentsMargins(11, 10, 11, 10)
        watermark_layout.setSpacing(10)
        self.watermark_region_label = QLabel()
        self.watermark_region_label.setObjectName("SecondaryText")
        self.watermark_region_label.setWordWrap(True)
        self.watermark_edit_button = QPushButton(self._t("框选修复区域"))
        self.watermark_edit_button.setProperty("role", "accentSoft")
        self.watermark_edit_button.clicked.connect(self.edit_watermark_regions)
        watermark_layout.addWidget(self.watermark_region_label, 1)
        watermark_layout.addWidget(self.watermark_edit_button)
        options_root.addWidget(self.watermark_region_panel)
        self.watermark_region_panel.setVisible(False)

        self.output_label = QLabel(self._t("输出文件夹"))
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(self._t("选择输出目录"))
        self.output_edit.textChanged.connect(self.output_edit.setToolTip)
        self.browse_output_button = QPushButton(self._t("浏览…"))
        self.open_output_button = QPushButton(self._t("打开目录"))
        self.browse_output_button.setProperty("role", "toolbar")
        self.open_output_button.setProperty("role", "ghost")
        self.browse_output_button.clicked.connect(self.choose_output_dir)
        self.open_output_button.clicked.connect(self.open_output_dir)

        self.output_label.setObjectName("FieldLabel")
        options_root.addWidget(self.output_label)
        output_buttons = QHBoxLayout()
        output_buttons.setSpacing(8)
        output_buttons.addWidget(self.output_edit, 1)
        output_buttons.addWidget(self.browse_output_button)
        output_buttons.addWidget(self.open_output_button)
        options_root.addLayout(output_buttons)
        options_root.addStretch(1)

        self.workspace_layout.addWidget(self.file_panel, 0, 0)
        self.workspace_layout.addWidget(self.options_panel, 0, 1)
        self.content_root.addLayout(self.workspace_layout, 1)
        self.content_scroll.setWidget(content)
        root.addWidget(self.content_scroll, 1)

        action_panel = QFrame()
        action_panel.setObjectName("ActionPanel")
        action_panel_layout = QVBoxLayout(action_panel)
        action_panel_layout.setContentsMargins(24, 12, 24, 12)
        action_panel_layout.setSpacing(8)
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)
        self.overall_label = QLabel(self._t("等待任务"))
        self.overall_label.setObjectName("TaskState")
        self.overall_label.setMinimumWidth(200)
        self.overall_label.setWordWrap(True)
        self.overall_progress = QProgressBar()
        self.overall_progress.setObjectName("OverallProgress")
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_progress.setTextVisible(False)
        self.overall_progress.setVisible(False)
        self.cancel_button = QPushButton(self._t("取消任务"))
        self.cancel_button.setProperty("role", "danger")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.start_button = QPushButton(self._t("开始处理"))
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.setMinimumWidth(176)
        self.start_button.clicked.connect(self.start_conversion)
        action_bar.addWidget(self.overall_label)
        action_bar.addStretch()
        action_bar.addWidget(self.cancel_button)
        action_bar.addWidget(self.start_button)
        action_panel_layout.addLayout(action_bar)
        action_panel_layout.addWidget(self.overall_progress)
        root.addWidget(action_panel)

        self.setCentralWidget(central)
        status_bar = QStatusBar()
        status_bar.setSizeGripEnabled(False)
        self.setStatusBar(status_bar)

        self._icon_bindings = (
            (self.add_files_button, "add", "normal"),
            (self.add_folder_button, "folder", "normal"),
            (self.add_links_button, "add", "normal"),
            (self.remove_button, "remove", "danger"),
            (self.clear_button, "clear", "normal"),
            (self.browse_output_button, "folder_open", "normal"),
            (self.open_output_button, "external", "normal"),
            (self.background_button, "image", "normal"),
            (self.watermark_edit_button, "select", "normal"),
            (self.cancel_button, "stop", "danger"),
            (self.start_button, "play", "primary"),
        )
        self._section_icons = (
            (self.file_section_icon, "queue"),
            (self.options_section_icon, "settings"),
        )
        self.add_files_button.setToolTip("Ctrl+O")
        self.add_folder_button.setToolTip("Ctrl+Shift+O")
        self._update_empty_state()
        self._adapt_layout()

    def _adapt_columns(self) -> None:
        if not hasattr(self, "fields_layout") or not hasattr(self, "field_pairs"):
            return
        if getattr(self, "workspace_wide", False):
            columns = 2
        else:
            available = self.width() - 84
            columns = 3 if available >= 1080 else (2 if available >= 700 else 1)
        if getattr(self, "field_columns", None) == columns:
            return
        self.field_columns = columns
        for label, combo in self.field_pairs:
            self.fields_layout.removeWidget(label)
            self.fields_layout.removeWidget(combo)
        for index, (label, combo) in enumerate(self.field_pairs):
            row, column = divmod(index, columns)
            self.fields_layout.addWidget(label, row * 2, column)
            self.fields_layout.addWidget(combo, row * 2 + 1, column)
        for column in range(3):
            self.fields_layout.setColumnStretch(column, 1 if column < columns else 0)

    def _adapt_layout(self) -> None:
        if not hasattr(self, "workspace_layout"):
            return
        wide = self.width() >= 1160
        header_compact = self.width() < 1110
        if getattr(self, "workspace_wide", None) != wide:
            self.workspace_wide = wide
            self.workspace_layout.removeWidget(self.file_panel)
            self.workspace_layout.removeWidget(self.options_panel)
            if wide:
                self.workspace_layout.addWidget(self.file_panel, 0, 0)
                self.workspace_layout.addWidget(self.options_panel, 0, 1)
                self.workspace_layout.setColumnStretch(0, 7)
                self.workspace_layout.setColumnStretch(1, 5)
                self.workspace_layout.setRowStretch(0, 1)
                self.file_panel.setMinimumHeight(465)
                self.options_panel.setMinimumHeight(465)
            else:
                self.workspace_layout.addWidget(self.file_panel, 0, 0)
                self.workspace_layout.addWidget(self.options_panel, 1, 0)
                self.workspace_layout.setColumnStretch(0, 1)
                self.workspace_layout.setColumnStretch(1, 0)
                self.workspace_layout.setRowStretch(0, 1)
                self.workspace_layout.setRowStretch(1, 0)
                self.file_panel.setMinimumHeight(380)
                self.options_panel.setMinimumHeight(0)
            self.field_columns = None
            self._adapt_columns()

        if getattr(self, "header_compact", None) != header_compact:
            self.header_compact = header_compact
            self.header_layout.removeWidget(self.header_controls)
            if header_compact:
                self.header_layout.addWidget(
                    self.header_controls, 1, 0, 1, 2,
                    Qt.AlignmentFlag.AlignLeft,
                )
            else:
                self.header_layout.addWidget(
                    self.header_controls, 0, 1,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                )

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._adapt_layout()

    def _restore_settings(self) -> None:
        default_dir = Path.home() / "Videos" / self._t(APP_NAME)
        self.output_edit.setText(self.settings.value("output_dir", str(default_dir)))
        mode = self.settings.value("mode", MODE_VIDEO)
        quality = self.settings.value("quality", "均衡压缩")
        encoder = self.settings.value("encoder", "自动选择")
        resolution = self.settings.value("resolution", "保持原分辨率")
        for combo, value in (
            (self.mode_combo, mode),
            (self.quality_combo, quality),
            (self.encoder_combo, encoder),
            (self.resolution_combo, resolution),
        ):
            index = combo.findData(str(value))
            if index >= 0:
                combo.setCurrentIndex(index)

    def _save_settings(self) -> None:
        self.settings.setValue("output_dir", self.output_edit.text().strip())
        self.settings.setValue("mode", self.mode_combo.currentData())
        self.settings.setValue("target", self.target_combo.currentData())
        self.settings.setValue("quality", self.quality_combo.currentData())
        self.settings.setValue("encoder", self.encoder_combo.currentData())
        self.settings.setValue("resolution", self.resolution_combo.currentData())
        self.settings.setValue("locale", self.language)
        self.settings.setValue("window/geometry", self.saveGeometry())

    @Slot()
    def add_download_links(self) -> None:
        if not self._is_download_mode() or self.worker:
            return
        raw_urls = split_url_input(self.url_input.toPlainText())
        if not raw_urls:
            self._notify(
                QMessageBox.Icon.Information,
                self._t("尚未添加链接"),
                self._t("请粘贴公开、无 DRM 的音频文件直链。"),
            )
            return

        existing = {
            str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
            for row in range(self.table.rowCount())
        }
        failures: list[tuple[str, str]] = []
        added = 0
        for raw_url in raw_urls:
            try:
                task = make_download_task(raw_url, self.language)
            except Exception as exc:
                failures.append((raw_url, str(exc)))
                continue
            if task.url in existing:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(task.display_name)
            name_item.setData(Qt.ItemDataRole.UserRole, task.url)
            name_item.setData(Qt.ItemDataRole.UserRole.value + 2, "url")
            name_item.setToolTip(task.source_label)
            self.table.setItem(row, 0, name_item)
            type_item = QTableWidgetItem(task.suffix_label)
            type_item.setToolTip(type_item.text())
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, QTableWidgetItem(self._t("下载时获取")))
            pending = QTableWidgetItem(self._t("等待处理"))
            pending.setData(Qt.ItemDataRole.UserRole, "pending")
            self.table.setItem(row, 3, pending)
            self.table.setItem(row, 4, QTableWidgetItem(""))
            existing.add(task.url)
            added += 1

        self.url_input.clear()
        self._update_count()
        if added:
            self.statusBar().showMessage(self._t(
                "已添加 {count} 个链接", count=added), 4000)
        if failures:
            details = "\n".join(
                f"{download_source_label(url, self.language)}\n{message}"
                for url, message in failures[:5]
            )
            if len(failures) > 5:
                details += "\n" + self._t(
                    "另有 {count} 个链接未显示。", count=len(failures) - 5)
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle(self._t("部分链接无法添加") if added
                               else self._t("无法添加链接"))
            box.setText(self._t(
                "有 {count} 个链接不符合直接音频下载规则。",
                count=len(failures),
            ))
            box.setDetailedText(details)
            box.addButton(self._t("关闭"), QMessageBox.ButtonRole.AcceptRole)
            box.exec()

    @Slot()
    def add_files(self) -> None:
        if self._is_download_mode():
            self.url_input.setFocus()
            return
        if self._is_unlock_mode():
            title = self._t("选择待解锁音乐文件")
            file_filter = (
                self._t("受支持的音乐文件") + f" ({unlock_file_patterns()});;"
                + self._t("所有文件") + " (*.*)"
            )
        elif self._is_video_enhance_mode():
            title = self._t("选择要增强的视频文件")
            patterns = " ".join(f"*{suffix}" for suffix in sorted(VIDEO_EXTENSIONS))
            file_filter = (
                self._t("视频文件") + f" ({patterns});;"
                + self._t("所有文件") + " (*.*)"
            )
        elif self._is_image_enhance_mode() or self._is_watermark_repair_mode():
            title = self._t(
                "选择要修复的图片文件" if self._is_watermark_repair_mode()
                else "选择要增强的图片文件")
            patterns = " ".join(f"*{suffix}" for suffix in sorted(IMAGE_EXTENSIONS))
            file_filter = (
                self._t("图片文件") + f" ({patterns});;"
                + self._t("所有文件") + " (*.*)"
            )
        else:
            title = self._t("选择音频或视频文件")
            file_filter = (
                self._t("媒体文件") + " (*.mp4 *.mkv *.mov *.avi *.webm *.wmv *.flv *.m4v *.ts *.mts *.m2ts "
                "*.3gp *.vob *.mpg *.mpeg *.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma "
                "*.ac3 *.eac3 *.mka *.aiff *.ape *.amr);;"
                + self._t("所有文件") + " (*.*)"
            )
        files, _ = QFileDialog.getOpenFileNames(
            self,
            title,
            "",
            file_filter,
        )
        self._add_paths([Path(item) for item in files])

    @Slot()
    def add_folder(self) -> None:
        if self._is_download_mode():
            self.url_input.setFocus()
            return
        if self._is_unlock_mode():
            title = self._t("选择待解锁音乐文件夹")
        elif self._is_video_enhance_mode():
            title = self._t("选择视频文件夹")
        elif self._is_image_enhance_mode() or self._is_watermark_repair_mode():
            title = self._t("选择图片文件夹")
        else:
            title = self._t("选择媒体文件夹")
        folder = QFileDialog.getExistingDirectory(self, title)
        if not folder:
            return
        paths = [
            path for path in Path(folder).rglob("*")
            if path.is_file() and self._path_matches_mode(path)
        ]
        self._add_paths(paths)

    def _path_matches_mode(self, path: Path) -> bool:
        if self._is_download_mode():
            return False
        if self._is_unlock_mode():
            return is_unlockable_path(path)
        if self._is_video_enhance_mode():
            return path.suffix.lower() in VIDEO_EXTENSIONS
        if self._is_image_enhance_mode() or self._is_watermark_repair_mode():
            return path.suffix.lower() in IMAGE_EXTENSIONS
        return path.suffix.lower() in SUPPORTED_EXTENSIONS

    def _add_paths(self, paths: list[Path]) -> None:
        if self._is_download_mode():
            return
        existing = {
            str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
            for row in range(self.table.rowCount())
        }
        added = 0
        for path in paths:
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if (
                not resolved.is_file()
                or not self._path_matches_mode(resolved)
                or str(resolved) in existing
            ):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(resolved.name)
            name_item.setData(Qt.ItemDataRole.UserRole, str(resolved))
            name_item.setToolTip(str(resolved))
            self.table.setItem(row, 0, name_item)
            type_item = QTableWidgetItem(display_file_type(resolved))
            type_item.setToolTip(type_item.text())
            self.table.setItem(row, 1, type_item)
            try:
                size_text = readable_size(resolved.stat().st_size)
            except OSError:
                size_text = self._t("未知")
            self.table.setItem(row, 2, QTableWidgetItem(size_text))
            pending = QTableWidgetItem(self._t("等待处理"))
            pending.setData(Qt.ItemDataRole.UserRole, "pending")
            self.table.setItem(row, 3, pending)
            self.table.setItem(row, 4, QTableWidgetItem(""))
            existing.add(str(resolved))
            added += 1

        self._update_count()
        if added:
            self.statusBar().showMessage(self._t(
                "已添加 {count} 个文件", count=added), 4000)

    @Slot()
    def remove_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)
        if self.table.rowCount() == 0:
            self.watermark_regions = ()
        self._update_count()
        self._update_watermark_region_ui()

    @Slot()
    def clear_files(self) -> None:
        self.table.setRowCount(0)
        self.progress_bars.clear()
        self.watermark_regions = ()
        self._update_count()
        self._update_watermark_region_ui()

    def _update_count(self) -> None:
        key = "{count} 个链接" if self._is_download_mode() else "{count} 个文件"
        self.file_count_label.setText(self._t(key, count=self.table.rowCount()))
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        if not hasattr(self, "file_stack"):
            return
        has_files = self.table.rowCount() > 0
        self.file_stack.setCurrentWidget(self.table if has_files else self.empty_state)
        self.clear_button.setEnabled(has_files and not self.worker)
        self._update_selection_actions()

    @Slot()
    def _update_selection_actions(self) -> None:
        if not hasattr(self, "remove_button"):
            return
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.remove_button.setEnabled(has_selection and not self.worker)
        if hasattr(self, "watermark_edit_button"):
            has_image = any(
                Path(str(self.table.item(row, 0).data(
                    Qt.ItemDataRole.UserRole))).suffix.lower() in IMAGE_EXTENSIONS
                for row in range(self.table.rowCount())
            )
            self.watermark_edit_button.setEnabled(
                self._is_watermark_repair_mode()
                and has_image
                and not self.worker
            )

    def _update_watermark_region_ui(self) -> None:
        if not hasattr(self, "watermark_region_label"):
            return
        count = len(self.watermark_regions)
        self.watermark_region_label.setText(
            self._t("已选择 {count} 个区域", count=count)
            if count else self._t("尚未选择修复区域")
        )
        self._update_selection_actions()

    @Slot()
    def edit_watermark_regions(self) -> None:
        if not self._is_watermark_repair_mode() or self.worker:
            return
        if self.table.rowCount() == 0:
            self._notify(
                QMessageBox.Icon.Information,
                self._t("尚未添加图片"),
                self._t("请先添加需要修复的图片。"),
            )
            return
        selected_rows = [index.row() for index in self.table.selectionModel().selectedRows()]
        candidate_rows = selected_rows + [
            row for row in range(self.table.rowCount()) if row not in selected_rows
        ]
        row = next(
            (candidate for candidate in candidate_rows
             if Path(str(self.table.item(candidate, 0).data(
                 Qt.ItemDataRole.UserRole))).suffix.lower() in IMAGE_EXTENSIONS),
            -1,
        )
        if row < 0:
            self._notify(
                QMessageBox.Icon.Information,
                self._t("尚未添加图片"),
                self._t("请先添加需要修复的图片。"),
            )
            return
        item = self.table.item(row, 0)
        source = Path(str(item.data(Qt.ItemDataRole.UserRole)))
        try:
            dialog = WatermarkRegionDialog(
                source,
                self.watermark_regions,
                self.language,
                self,
            )
        except (OSError, ValueError) as exc:
            self._notify(
                QMessageBox.Icon.Warning,
                self._t("无法读取图片"),
                str(exc),
            )
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.watermark_regions = dialog.regions()
            self._update_watermark_region_ui()
            self.statusBar().showMessage(self._t(
                "已保存 {count} 个修复区域",
                count=len(self.watermark_regions),
            ), 4000)

    @Slot(object)
    def _table_context_menu(self, point: object) -> None:
        index = self.table.indexAt(point)
        if not index.isValid():
            return
        row = index.row()
        status = self.table.item(row, 3)
        output = self.table.item(row, 4)
        menu = QMenu(self)
        if output and output.data(Qt.ItemDataRole.UserRole):
            menu.addAction(self._t("复制输出路径"), lambda: self._copy_output_path(row))
        if status and status.data(Qt.ItemDataRole.UserRole) == "failed":
            menu.addAction(self._t("查看错误详情"), lambda: self._show_error_details(row))
        if not menu.actions():
            return
        menu.exec(self.table.viewport().mapToGlobal(point))

    @Slot(int, int)
    def _table_double_clicked(self, row: int, column: int) -> None:
        if column == 4:
            self._copy_output_path(row)
        elif column == 3:
            self._show_error_details(row)

    def _copy_output_path(self, row: int) -> None:
        item = self.table.item(row, 4)
        path = item.data(Qt.ItemDataRole.UserRole) if item else None
        if path:
            QGuiApplication.clipboard().setText(str(path))
            self.statusBar().showMessage(self._t("已复制输出路径"), 4000)

    def _show_error_details(self, row: int) -> None:
        box = self._error_details_box(row)
        if box:
            box.exec()

    def _error_details_box(self, row: int) -> QMessageBox | None:
        item = self.table.item(row, 3)
        if not item or item.data(Qt.ItemDataRole.UserRole) != "failed":
            return None
        detail = str(item.data(Qt.ItemDataRole.UserRole.value + 1) or item.toolTip())
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self._t("错误详情"))
        box.setText(self._t("此文件未能完成处理。"))
        box.setDetailedText(detail)
        box.addButton(self._t("关闭"), QMessageBox.ButtonRole.AcceptRole)
        return box

    def _replace_combo_choices(
        self,
        combo: QComboBox,
        choices: list[str],
        fallback: str,
    ) -> None:
        if [combo.itemData(index) for index in range(combo.count())] == choices:
            return
        previous = combo.currentData()
        combo.blockSignals(True)
        try:
            combo.clear()
            for item in choices:
                combo.addItem(self._t(item), item)
            index = combo.findData(previous)
            if index < 0:
                index = combo.findData(fallback)
            combo.setCurrentIndex(max(index, 0))
        finally:
            combo.blockSignals(False)

    @Slot()
    def _update_mode(self) -> None:
        mode = self.mode_combo.currentData()
        enhance_mode = mode in {MODE_VIDEO_ENHANCE, MODE_IMAGE_ENHANCE}
        watermark_mode = mode == MODE_IMAGE_WATERMARK_REPAIR
        self._replace_combo_choices(
            self.quality_combo,
            (WATERMARK_REPAIR_STRENGTHS if watermark_mode
             else ENHANCE_STRENGTHS if enhance_mode else QUALITY_PRESETS),
            ("标准修复" if watermark_mode
             else "标准增强" if enhance_mode else "均衡压缩"),
        )
        self._replace_combo_choices(
            self.resolution_combo,
            ENHANCE_RESOLUTIONS if enhance_mode else RESOLUTION_PRESETS,
            "提升至 4K" if enhance_mode else "保持原分辨率",
        )
        choices = {
            MODE_VIDEO: VIDEO_TARGETS,
            MODE_VIDEO_ENHANCE: VIDEO_ENHANCE_TARGETS,
            MODE_IMAGE_ENHANCE: IMAGE_ENHANCE_TARGETS,
            MODE_IMAGE_WATERMARK_REPAIR: WATERMARK_REPAIR_TARGETS,
            MODE_AUDIO: AUDIO_TARGETS,
            MODE_EXTRACT: EXTRACT_TARGETS,
            MODE_COMPRESS: COMPRESS_TARGETS,
            MODE_MUSIC_UNLOCK: [UNLOCK_TARGET],
            MODE_DIRECT_DOWNLOAD: [DIRECT_TARGET],
        }.get(mode, VIDEO_TARGETS)
        previous = self.target_combo.currentData()
        self.target_combo.clear()
        for item in choices:
            self.target_combo.addItem(self._t(item), item)
        index = self.target_combo.findData(previous)
        if index >= 0:
            self.target_combo.setCurrentIndex(index)

        simple_mode = mode in {MODE_MUSIC_UNLOCK, MODE_DIRECT_DOWNLOAD}
        download_mode = mode == MODE_DIRECT_DOWNLOAD
        self.target_combo.setEnabled(not simple_mode)
        self.quality_label.setVisible(not simple_mode)
        self.quality_combo.setVisible(not simple_mode)
        video_controls = mode in {MODE_VIDEO, MODE_COMPRESS, MODE_VIDEO_ENHANCE}
        self.encoder_label.setVisible(video_controls)
        self.encoder_combo.setVisible(video_controls)
        resolution_controls = video_controls or mode == MODE_IMAGE_ENHANCE
        self.resolution_label.setVisible(resolution_controls)
        self.resolution_combo.setVisible(resolution_controls)
        self.watermark_region_panel.setVisible(watermark_mode)
        self.url_input_panel.setVisible(download_mode)
        self.add_files_button.setVisible(not download_mode)
        self.add_folder_button.setVisible(not download_mode)
        self.add_action.setEnabled(not download_mode and not self.worker)
        self.add_folder_action.setEnabled(not download_mode and not self.worker)
        self._update_watermark_region_ui()
        self._update_quality_hint()
        self._update_mode_copy()

    def _update_mode_copy(self) -> None:
        if not hasattr(self, "empty_state"):
            return
        enhance_mode = self._is_enhance_mode()
        watermark_mode = self._is_watermark_repair_mode()
        self.quality_label.setText(self._t(
            "修复边缘" if watermark_mode else
            "增强强度" if enhance_mode else "质量方案"))
        self.resolution_label.setText(self._t(
            "输出分辨率" if enhance_mode else "分辨率限制"))
        if self._is_download_mode():
            self.files_title.setText(self._t("待下载音频"))
            self.files_hint.setText(self._t("粘贴公开音频文件直链；支持一次添加多行"))
            self.options_hint.setText(self._t("下载无 DRM 音频直链，并保留原始格式"))
            self.empty_state.set_texts(
                self._t("在上方粘贴音频直链"),
                self._t("仅支持公开 HTTP/HTTPS 音频文件，不支持平台页面或流媒体清单"),
                self._t("定位到链接输入框"),
            )
            self.start_button.setText(self._t("开始下载"))
            self.table.setHorizontalHeaderLabels([
                self._t(key) for key in
                ("来源 / 文件名", "类型", "大小", "状态 / 进度", "输出文件")
            ])
        elif self._is_unlock_mode():
            self.files_title.setText(self._t("待处理文件"))
            self.files_hint.setText(self._t("将文件或文件夹拖入此处，或使用下方按钮添加"))
            self.options_hint.setText(self._t("离线解锁本地音乐，并保留原始文件"))
            self.empty_state.set_texts(
                self._t("把待解锁音乐拖到这里"),
                self._t("支持网易云、QQ 音乐、酷狗、酷我等本地文件，可批量添加文件夹"),
                self._t("选择音乐文件"),
            )
            self.start_button.setText(self._t("开始解锁"))
            self.table.setHorizontalHeaderLabels([
                self._t(key) for key in
                ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
            ])
        elif self._is_video_enhance_mode():
            self.files_title.setText(self._t("待增强视频"))
            self.files_hint.setText(self._t("拖入视频或文件夹，可批量增强"))
            self.options_hint.setText(self._t(
                "降噪、锐化并按原比例输出，最高支持 4K"))
            self.empty_state.set_texts(
                self._t("把要增强的视频拖到这里"),
                self._t("支持常见视频格式；输出为兼容性良好的 MP4"),
                self._t("选择视频文件"),
            )
            self.start_button.setText(self._t("开始增强"))
            self.table.setHorizontalHeaderLabels([
                self._t(key) for key in
                ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
            ])
        elif self._is_image_enhance_mode():
            self.files_title.setText(self._t("待增强图片"))
            self.files_hint.setText(self._t("拖入图片或文件夹，可批量增强"))
            self.options_hint.setText(self._t(
                "降噪、锐化并按原比例输出，最高支持 4K"))
            self.empty_state.set_texts(
                self._t("把要增强的图片拖到这里"),
                self._t("支持 JPG、PNG、WebP、BMP 与 TIFF"),
                self._t("选择图片文件"),
            )
            self.start_button.setText(self._t("开始增强"))
            self.table.setHorizontalHeaderLabels([
                self._t(key) for key in
                ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
            ])
        elif self._is_watermark_repair_mode():
            self.files_title.setText(self._t("待修复图片"))
            self.files_hint.setText(self._t("拖入图片或文件夹，可批量套用所选区域"))
            self.options_hint.setText(self._t(
                "框选一处或多处可见水印，由本地 FFmpeg 修复周围纹理"))
            self.empty_state.set_texts(
                self._t("把要修复的图片拖到这里"),
                self._t("支持 JPG、PNG、WebP、BMP 与 TIFF；原图不会改动"),
                self._t("选择图片文件"),
            )
            self.start_button.setText(self._t("开始修复"))
            self.table.setHorizontalHeaderLabels([
                self._t(key) for key in
                ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
            ])
        else:
            self.files_title.setText(self._t("待处理文件"))
            self.files_hint.setText(self._t("将文件或文件夹拖入此处，或使用下方按钮添加"))
            self.options_hint.setText(self._t("按任务需要选择输出格式与质量"))
            self.empty_state.set_texts(
                self._t("把媒体文件拖到这里"),
                self._t("支持常见音频和视频格式，也可以直接拖入整个文件夹"),
                self._t("选择文件"),
            )
            self.start_button.setText(self._t("开始处理"))
            self.table.setHorizontalHeaderLabels([
                self._t(key) for key in
                ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
            ])
        self._update_count()
        if not self.worker:
            self.statusBar().showMessage(self._ready_message())

    @Slot()
    def _update_quality_hint(self) -> None:
        target = self.target_combo.currentData()
        mode = self.mode_combo.currentData()
        if mode == MODE_DIRECT_DOWNLOAD:
            self.quality_combo.setEnabled(False)
            self.quality_hint.setMinimumHeight(66)
            self.quality_hint.setText(self._t(
                "仅下载你有权保存的公开无 DRM 音频直链；不支持 Spotify、Apple Music 页面、Cookie、M3U8/DASH 或加密媒体。"))
            return
        if mode == MODE_MUSIC_UNLOCK:
            self.quality_combo.setEnabled(False)
            self.quality_hint.setMinimumHeight(54)
            self.quality_hint.setText(self._t(
                "仅处理你合法拥有或获授权的本地文件；源文件不会删除。\n应用不会联网下载音乐或访问账号。"))
            return
        if mode in {MODE_VIDEO_ENHANCE, MODE_IMAGE_ENHANCE}:
            self.quality_combo.setEnabled(True)
            self.quality_hint.setMinimumHeight(68)
            hints = {
                "自然增强": "轻度降噪与锐化，适合本身质量较好的素材。",
                "标准增强": "平衡降噪与细节增强，推荐用于大多数素材。",
                "强力增强": "更强的降噪与边缘增强，适合模糊或噪点明显的素材。",
            }
            hint = hints.get(self.quality_combo.currentData(), hints["标准增强"])
            self.quality_hint.setText(
                self._t(hint) + "\n" + self._t(
                    "增强可改善观感并放大至 4K，但无法凭空恢复源文件中不存在的真实细节。"))
            return
        if mode == MODE_IMAGE_WATERMARK_REPAIR:
            self.quality_combo.setEnabled(True)
            self.quality_hint.setMinimumHeight(84)
            hints = {
                "精细修复": "严格使用框选范围，适合边界清楚且选择准确的水印。",
                "标准修复": "轻微扩展选区边缘，兼顾抗锯齿与自然过渡，推荐使用。",
                "扩展修复": "进一步覆盖水印阴影和描边，可能影响更多周围纹理。",
            }
            hint = hints.get(self.quality_combo.currentData(), hints["标准修复"])
            self.quality_hint.setText(
                self._t(hint) + "\n" + self._t(
                    "仅针对手动框选的可见区域修复画面；不提供隐藏标记的检测或定向清除。导出重新编码可能使 C2PA 等内容凭证失效，请保留原图。"))
            return
        self.quality_hint.setMinimumHeight(0)
        raw_copy = mode == MODE_EXTRACT and target == EXTRACT_TARGETS[0]
        self.quality_combo.setEnabled(not raw_copy and target != "WAV")
        if raw_copy:
            self.quality_hint.setText(self._t(
                "直接复制原音轨，不重新编码；质量选项不影响无损提取。"))
            return
        if target in {"FLAC", "WAV"} and mode in {MODE_AUDIO, MODE_EXTRACT}:
            self.quality_hint.setText(self._t(
                "FLAC/WAV 输出为无损格式，但有损源文件已丢失的音质无法恢复。"))
            return
        quality = self.quality_combo.currentData()
        hints = {
            "画质优先": "接近视觉无损，输出文件通常较大。",
            "均衡压缩": "兼顾画质、速度和文件大小，推荐日常使用。",
            "极限压缩": "优先减小体积，可能非常耗时并损失部分细节。",
        }
        self.quality_hint.setText(self._t(hints[quality]) if quality in hints else "")

    @Slot()
    def choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            self._t("选择输出文件夹"),
            self.output_edit.text().strip(),
        )
        if folder:
            self.output_edit.setText(folder)

    @Slot()
    def open_output_dir(self) -> None:
        text = self.output_edit.text().strip()
        if not text:
            return
        folder = Path(text)
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._notify(QMessageBox.Icon.Warning, self._t("无法打开目录"), str(exc))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def _current_paths(self) -> list[Path | DirectDownloadTask]:
        values = [
            str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
            for row in range(self.table.rowCount())
        ]
        if self._is_download_mode():
            return [make_download_task(value, self.language) for value in values]
        return [Path(value) for value in values]

    @Slot()
    def start_conversion(self) -> None:
        try:
            paths = self._current_paths()
        except Exception as exc:
            self._notify(QMessageBox.Icon.Warning, self._t("无法添加链接"), str(exc))
            return
        if not paths:
            if self._is_download_mode():
                self._notify(QMessageBox.Icon.Information, self._t("尚未添加链接"),
                             self._t("请先添加需要下载的音频直链。"))
            else:
                self._notify(QMessageBox.Icon.Information, self._t("尚未添加文件"),
                             self._t("请先添加需要处理的文件。"))
            return

        incompatible = ([] if self._is_download_mode() else
                        [path for path in paths if not self._path_matches_mode(path)])
        if incompatible:
            self._notify(
                QMessageBox.Icon.Information,
                self._t("文件与任务类型不匹配"),
                self._t(
                    "当前任务不支持列表中的 {count} 个文件。请移除这些文件，或切换任务类型。",
                    count=len(incompatible),
                ),
            )
            return

        if self._is_watermark_repair_mode() and not self.watermark_regions:
            self._notify(
                QMessageBox.Icon.Information,
                self._t("尚未选择修复区域"),
                self._t("请先在图片预览中框选至少一个可见水印区域。"),
            )
            self.edit_watermark_regions()
            return

        output_text = self.output_edit.text().strip()
        if not output_text:
            self._notify(QMessageBox.Icon.Information, self._t("请选择输出目录"),
                         self._t("请先指定转换后的文件保存位置。"))
            return

        output_dir = Path(output_text)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._notify(QMessageBox.Icon.Critical,
                         self._t("无法创建输出目录"), str(exc))
            return

        options = ConversionOptions(
            mode=self.mode_combo.currentData(),
            target=self.target_combo.currentData(),
            quality=self.quality_combo.currentData(),
            encoder=self.encoder_combo.currentData(),
            resolution=self.resolution_combo.currentData(),
            output_dir=output_dir,
            locale=self.language,
        )
        self._save_settings()
        self._set_running(True)

        for row in range(self.table.rowCount()):
            self.table.setCellWidget(row, 3, None)
            pending = QTableWidgetItem(self._t("等待处理"))
            pending.setData(Qt.ItemDataRole.UserRole, "pending")
            self.table.setItem(row, 3, pending)
            self.table.setItem(row, 4, QTableWidgetItem(""))
        self.progress_bars.clear()

        self.worker_thread = QThread(self)
        self.worker = BatchWorker(paths, options, self.watermark_regions)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.item_started.connect(self._item_started)
        self.worker.item_progress.connect(self._item_progress)
        self.worker.item_finished.connect(self._item_finished)
        self.worker.completed.connect(self._batch_completed)
        self.worker.completed.connect(self.worker_thread.quit)
        self.worker.completed.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _set_running(self, running: bool) -> None:
        for widget in (
            self.add_files_button,
            self.add_folder_button,
            self.url_input,
            self.add_links_button,
            self.remove_button,
            self.clear_button,
            self.language_combo,
            self.mode_combo,
            self.target_combo,
            self.quality_combo,
            self.encoder_combo,
            self.resolution_combo,
            self.watermark_edit_button,
            self.output_edit,
            self.browse_output_button,
        ):
            widget.setEnabled(not running)
        self.add_action.setEnabled(not running and not self._is_download_mode())
        self.add_folder_action.setEnabled(not running and not self._is_download_mode())
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.overall_progress.setVisible(running)
        if running:
            self.overall_progress.setValue(0)
        self._set_task_state("active" if running else "idle")
        if not running:
            self.target_combo.setEnabled(
                not self._is_unlock_mode() and not self._is_download_mode())
            self._update_quality_hint()
            self._update_empty_state()
            self._update_watermark_region_ui()
        self.overall_label.setText(
            self._t("正在下载…" if running and self._is_download_mode() else
                    "正在解锁…" if running and self._is_unlock_mode() else
                    "正在增强…" if running and self._is_enhance_mode() else
                    "正在修复…" if running and self._is_watermark_repair_mode() else
                    "正在处理…" if running else "等待任务"))

    @Slot(int)
    def _item_started(self, row: int) -> None:
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setFormat(self._t("正在准备…"))
        self.progress_bars[row] = progress
        self.table.setCellWidget(row, 3, progress)
        self.table.scrollToItem(self.table.item(row, 0))
        self.overall_progress.setValue(int(100 * row / max(self.table.rowCount(), 1)))
        self.overall_label.setText(self._t(
            "正在处理第 {current}/{total} 项",
            current=row + 1, total=self.table.rowCount()))

    @Slot(int, int, str)
    def _item_progress(self, row: int, percent: int, text: str) -> None:
        progress = self.progress_bars.get(row)
        if not progress:
            return
        if percent >= 0:
            progress.setValue(percent)
            self.overall_progress.setValue(int(
                100 * (row + min(max(percent, 0), 100) / 100)
                / max(self.table.rowCount(), 1)))
        progress.setFormat(text)

    @Slot(int, bool, str, str)
    def _item_finished(self, row: int, success: bool, message: str, output: str) -> None:
        self.table.setCellWidget(row, 3, None)
        status = QTableWidgetItem(
            message if success else self._t("失败：{message}", message=message))
        status.setData(Qt.ItemDataRole.UserRole, "success" if success else "failed")
        status.setData(Qt.ItemDataRole.UserRole.value + 1, message)
        color = COLORS[getattr(self, "effective_theme", "light")]
        status.setForeground(QBrush(QColor(color["success" if success else "error"])))
        status.setToolTip(message)
        self.table.setItem(row, 3, status)
        output_item = QTableWidgetItem(Path(output).name if output else "")
        output_item.setData(Qt.ItemDataRole.UserRole, output)
        output_item.setToolTip(output)
        self.table.setItem(row, 4, output_item)
        self.overall_progress.setValue(int(
            100 * (row + 1) / max(self.table.rowCount(), 1)))

    @Slot(bool, int, int)
    def _batch_completed(self, cancelled: bool, successes: int, failures: int) -> None:
        self._set_running(False)
        self.worker = None
        self.worker_thread = None

        if cancelled:
            text = self._t("任务已取消；成功 {successes} 个，失败 {failures} 个。",
                           successes=successes, failures=failures)
            self.statusBar().showMessage(text)
            self.overall_label.setText(self._t("任务已取消"))
            self._set_task_state("warning")
            return

        text = self._t("全部完成：成功 {successes} 个，失败 {failures} 个。",
                       successes=successes, failures=failures)
        self.statusBar().showMessage(text)
        self.overall_label.setText(text)
        self._set_task_state("warning" if failures else "success")
        if failures:
            self._notify(QMessageBox.Icon.Warning, self._t("处理完成"), text + "\n"
                         + self._t("可将鼠标停在失败状态上查看详细错误。"))
        else:
            box = QMessageBox(self)
            box.setWindowTitle(self._t("处理完成"))
            box.setText(text)
            box.setInformativeText(self._t("是否打开输出文件夹？"))
            open_button = box.addButton(
                self._t("打开"), QMessageBox.ButtonRole.AcceptRole)
            box.addButton(self._t("关闭"), QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() == open_button:
                self.open_output_dir()

    @Slot()
    def cancel_conversion(self) -> None:
        if self.worker:
            self.cancel_button.setEnabled(False)
            self.overall_label.setText(self._t("正在安全停止任务…"))
            self.worker.request_cancel()

    def open_notices(self) -> None:
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        notice = root / "THIRD_PARTY_NOTICES.md"
        if notice.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(notice)))
        else:
            self._notify(
                QMessageBox.Icon.Information, self._t("第三方许可"),
                "FFmpeg：https://ffmpeg.org/\n"
                "Qt for Python：https://doc.qt.io/qtforpython-6/\n"
                "Unlock Music：https://git.unlock-music.dev/um/cli\n"
                + self._t("完整声明见项目 THIRD_PARTY_NOTICES.md。"),
            )

    def show_about(self) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(f"{self._t('关于')} {self._t(APP_NAME)}")
        box.setText(
            f"<h3>{self._t(APP_NAME)}</h3>"
            f"<p>{self._t('版本 {version}', version=APP_VERSION)}</p>"
            f"<p>{self._t('基于 FFmpeg 与 Qt for Python 构建的本地音视频转换工具。')}</p>"
            f"<p>{self._t('转换全程在本机完成，不上传用户文件。')}</p>"
            f"<p>{self._t('图片与视频清晰度增强支持按原比例输出，最高可达 4K。')}</p>"
            f"<p>{self._t('可见水印区域修复适用于有权编辑的图片；重新编码可能改变元数据或使内容凭证失效。')}</p>"
            f"<p>{self._t('音乐解锁功能由 Unlock Music CLI 提供，仅供处理合法拥有或获授权的本地文件。')}</p>"
            f"<p>{self._t('授权下载仅连接链接所在服务器，不支持订阅平台页面、Cookie、流媒体清单或加密媒体。')}</p>"
            '<p><a href="https://github.com/plao94619-hash/Repository-name-VideoToolBox">'
            + self._t("项目主页") + "</a></p>"
        )
        box.addButton(self._t("关闭"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if not self.worker and event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_drag_active(False)
        event.accept()

    def _set_drag_active(self, active: bool) -> None:
        for widget in (self.file_panel, self.empty_state):
            widget.setProperty("dragActive", active)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drag_active(False)
        if self._is_download_mode():
            urls = [url.toString() for url in event.mimeData().urls()
                    if not url.isLocalFile()]
            if urls:
                current = self.url_input.toPlainText().strip()
                combined = "\n".join(([current] if current else []) + urls)
                self.url_input.setPlainText(combined)
                self.add_download_links()
                event.acceptProposedAction()
            else:
                event.ignore()
            return
        paths: list[Path] = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if not local:
                continue
            path = Path(local)
            if path.is_dir():
                paths.extend(
                    item for item in path.rglob("*")
                    if item.is_file() and self._path_matches_mode(item)
                )
            else:
                paths.append(path)
        self._add_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_settings()
        if self.worker:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Question)
            box.setWindowTitle(self._t("任务仍在运行"))
            box.setText(self._t("需要先停止当前任务。是否取消任务？"))
            yes_button = box.addButton(self._t("是"), QMessageBox.ButtonRole.YesRole)
            box.addButton(self._t("否"), QMessageBox.ButtonRole.NoRole)
            box.exec()
            if box.clickedButton() == yes_button:
                self.cancel_conversion()
            event.ignore()
            return
        event.accept()


def run_self_test() -> int:
    media_ok, media_message = media_self_test()
    unlock_ok, unlock_message = music_unlock_self_test()
    message = f"{media_message}\n{unlock_message}"
    safe_message = message.encode("ascii", errors="backslashreplace").decode("ascii")
    print(safe_message)
    return 0 if media_ok and unlock_ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return run_self_test()
    if "--version" in sys.argv:
        print(APP_VERSION)
        return 0

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("UniversalMediaToolbox")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
