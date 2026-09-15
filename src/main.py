from __future__ import annotations

import os
import sys
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QLocale, QSettings, QThread, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStatusBar,
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
    VIDEO_TARGETS,
    ConversionCancelled,
    ConversionOptions,
    convert_file,
    self_test,
)
from version import APP_NAME, APP_VERSION
from i18n import (
    LANGUAGE_LABELS, SUPPORTED_LANGUAGES, language_for_system_locale, translate,
)


APP_STYLE = """
QMainWindow, QWidget {
    background: #f6f8fb;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}
QFrame#HeroCard {
    background: #16233f;
    border-radius: 16px;
}
QLabel#HeroTitle {
    color: white;
    font-size: 26px;
    font-weight: 700;
}
QLabel#HeroSubtitle {
    color: #b9c8e6;
    font-size: 13px;
}
QFrame#Panel {
    background: white;
    border: 1px solid #e3e8f1;
    border-radius: 12px;
}
QPushButton {
    min-height: 34px;
    padding: 0 16px;
    border: 1px solid #d4dbe7;
    border-radius: 8px;
    background: white;
    color: #24324a;
    font-weight: 600;
}
QPushButton:hover {
    background: #f0f5ff;
    border-color: #8eb2ff;
}
QPushButton:pressed {
    background: #e5eeff;
}
QPushButton:disabled {
    color: #a4adbb;
    background: #f1f3f6;
    border-color: #e1e5eb;
}
QPushButton#PrimaryButton {
    background: #2864dc;
    color: white;
    border: none;
    min-height: 42px;
    font-size: 14px;
}
QPushButton#PrimaryButton:hover {
    background: #1f56c5;
}
QPushButton#DangerButton {
    color: #b42318;
}
QComboBox, QLineEdit {
    min-height: 34px;
    padding: 0 10px;
    background: white;
    border: 1px solid #d6dde9;
    border-radius: 7px;
}
QComboBox:focus, QLineEdit:focus {
    border: 1px solid #4b83eb;
}
QTableWidget {
    background: white;
    alternate-background-color: #f8faff;
    border: 1px solid #e0e6ef;
    border-radius: 8px;
    gridline-color: #edf0f5;
    selection-background-color: #dce9ff;
    selection-color: #172033;
}
QHeaderView::section {
    background: #eef3fa;
    color: #3e4d66;
    border: none;
    border-bottom: 1px solid #dbe2ec;
    padding: 8px;
    font-weight: 600;
}
QProgressBar {
    min-height: 16px;
    border: none;
    border-radius: 7px;
    background: #e8edf5;
    text-align: center;
    color: #172033;
}
QProgressBar::chunk {
    border-radius: 7px;
    background: #3a75df;
}
QStatusBar {
    background: white;
    border-top: 1px solid #e2e7ef;
}
"""


def readable_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TB"


class BatchWorker(QObject):
    item_started = Signal(int)
    item_progress = Signal(int, int, str)
    item_finished = Signal(int, bool, str, str)
    completed = Signal(bool, int, int)

    def __init__(self, paths: list[Path], options: ConversionOptions):
        super().__init__()
        self.paths = paths
        self.options = options
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
                result = convert_file(
                    path,
                    self.options,
                    lambda percent, text, row=index: self.item_progress.emit(row, percent, text),
                    self.cancel_event,
                )
                successes += 1
                self.item_finished.emit(
                    index,
                    True,
                    result.size_message,
                    str(result.output_path),
                )
            except ConversionCancelled:
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
        self.setMinimumSize(980, 680)
        self.resize(1120, 760)
        self.setAcceptDrops(True)

        self.settings = QSettings("UniversalMediaToolbox", "UniversalMediaToolbox")
        ui_languages = QLocale.system().uiLanguages()
        preferred_locale = (
            ui_languages[0] if ui_languages else QLocale.system().name()
        )
        saved_locale = str(self.settings.value(
            "locale", language_for_system_locale(preferred_locale)))
        self.language = saved_locale if saved_locale in SUPPORTED_LANGUAGES else "zh_CN"
        self.worker: BatchWorker | None = None
        self.worker_thread: QThread | None = None
        self.progress_bars: dict[int, QProgressBar] = {}

        self._build_actions()
        self._build_ui()
        self._restore_settings()
        self._update_mode()
        last_target = str(self.settings.value("target", ""))
        target_index = self.target_combo.findData(last_target)
        if target_index >= 0:
            self.target_combo.setCurrentIndex(target_index)
        self._retranslate_ui()
        self.statusBar().showMessage(self._t("就绪：可直接拖入音频或视频文件"))

    def _t(self, key: str, **values: object) -> str:
        return translate(key, self.language, **values)

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
        self.statusBar().showMessage(self._t("就绪：可直接拖入音频或视频文件"))

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(f"{self._t(APP_NAME)} {APP_VERSION}")
        for action, key in (
            (self.add_action, "添加文件"),
            (self.add_folder_action, "添加文件夹"),
            (self.exit_action, "退出"),
            (self.notices_action, "第三方许可"),
            (self.about_action, "关于"),
        ):
            action.setText(self._t(key))
        self.file_menu.setTitle(self._t("文件"))
        self.help_menu.setTitle(self._t("帮助"))
        for widget, key in (
            (self.hero_title, APP_NAME),
            (self.hero_subtitle, "格式转换 · 无损提取音轨 · 画质优先压缩 · 极限压缩"),
            (self.language_label, "语言"),
            (self.add_files_button, "＋ 添加文件"),
            (self.add_folder_button, "添加文件夹"),
            (self.remove_button, "移除选中"),
            (self.clear_button, "清空列表"),
            (self.mode_label, "任务类型"),
            (self.target_label, "输出格式"),
            (self.quality_label, "质量方案"),
            (self.encoder_label, "视频编码"),
            (self.resolution_label, "分辨率限制"),
            (self.output_label, "输出文件夹"),
            (self.browse_output_button, "浏览…"),
            (self.open_output_button, "打开目录"),
            (self.cancel_button, "取消任务"),
            (self.start_button, "开始处理"),
        ):
            widget.setText(self._t(key))
        for combo in (
            self.mode_combo, self.target_combo, self.quality_combo,
            self.encoder_combo, self.resolution_combo,
        ):
            for index in range(combo.count()):
                combo.setItemText(index, self._t(str(combo.itemData(index))))
        self.output_edit.setPlaceholderText(self._t("选择输出目录"))
        self.table.setHorizontalHeaderLabels([
            self._t(key) for key in ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
        ])
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 3)
            if item and item.data(Qt.ItemDataRole.UserRole) == "pending":
                item.setText(self._t("等待处理"))
        self._update_count()
        self._update_quality_hint()
        if not self.worker:
            self.overall_label.setText(self._t("等待任务"))

    def _build_actions(self) -> None:
        self.add_action = QAction(self._t("添加文件"), self)
        self.add_action.setShortcut("Ctrl+O")
        self.add_action.triggered.connect(self.add_files)

        self.add_folder_action = QAction(self._t("添加文件夹"), self)
        self.add_folder_action.setShortcut("Ctrl+Shift+O")
        self.add_folder_action.triggered.connect(self.add_folder)

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

        self.help_menu = self.menuBar().addMenu(self._t("帮助"))
        self.help_menu.addAction(self.notices_action)
        self.help_menu.addAction(self.about_action)

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 18, 24, 18)
        hero_top = QHBoxLayout()
        self.hero_title = QLabel(self._t(APP_NAME))
        self.hero_title.setObjectName("HeroTitle")
        hero_top.addWidget(self.hero_title)
        hero_top.addStretch()
        self.language_label = QLabel(self._t("语言"))
        self.language_label.setObjectName("HeroSubtitle")
        hero_top.addWidget(self.language_label)
        self.language_combo = QComboBox()
        for locale in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(LANGUAGE_LABELS[locale], locale)
        self.language_combo.setCurrentIndex(self.language_combo.findData(self.language))
        self.language_combo.setMinimumWidth(140)
        self.language_combo.currentIndexChanged.connect(self._change_language)
        hero_top.addWidget(self.language_combo)
        self.hero_subtitle = QLabel(self._t(
            "格式转换 · 无损提取音轨 · 画质优先压缩 · 极限压缩"))
        self.hero_subtitle.setObjectName("HeroSubtitle")
        hero_layout.addLayout(hero_top)
        hero_layout.addWidget(self.hero_subtitle)
        root.addWidget(hero)

        file_panel = QFrame()
        file_panel.setObjectName("Panel")
        file_layout = QVBoxLayout(file_panel)
        file_layout.setContentsMargins(14, 14, 14, 14)
        file_layout.setSpacing(10)

        toolbar = QHBoxLayout()
        self.add_files_button = QPushButton(self._t("＋ 添加文件"))
        self.add_folder_button = QPushButton(self._t("添加文件夹"))
        self.remove_button = QPushButton(self._t("移除选中"))
        self.clear_button = QPushButton(self._t("清空列表"))
        self.remove_button.setObjectName("DangerButton")
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.clear_files)
        toolbar.addWidget(self.add_files_button)
        toolbar.addWidget(self.add_folder_button)
        toolbar.addWidget(self.remove_button)
        toolbar.addWidget(self.clear_button)
        toolbar.addStretch()
        self.file_count_label = QLabel(self._t("{count} 个文件", count=0))
        toolbar.addWidget(self.file_count_label)
        file_layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            self._t(key) for key in ("文件名", "类型", "大小", "状态 / 进度", "输出文件")
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.table)
        root.addWidget(file_panel, 1)

        options_panel = QFrame()
        options_panel.setObjectName("Panel")
        options_layout = QGridLayout(options_panel)
        options_layout.setContentsMargins(16, 14, 16, 14)
        options_layout.setHorizontalSpacing(16)
        options_layout.setVerticalSpacing(10)

        self.mode_combo = QComboBox()
        for item in (MODE_VIDEO, MODE_AUDIO, MODE_EXTRACT, MODE_COMPRESS):
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
        options_layout.addWidget(self.mode_label, 0, 0)
        options_layout.addWidget(self.mode_combo, 1, 0)
        self.target_label = QLabel(self._t("输出格式"))
        options_layout.addWidget(self.target_label, 0, 1)
        options_layout.addWidget(self.target_combo, 1, 1)
        self.quality_label = QLabel(self._t("质量方案"))
        options_layout.addWidget(self.quality_label, 0, 2)
        options_layout.addWidget(self.quality_combo, 1, 2)

        self.encoder_label = QLabel(self._t("视频编码"))
        self.resolution_label = QLabel(self._t("分辨率限制"))
        options_layout.addWidget(self.encoder_label, 2, 0)
        options_layout.addWidget(self.encoder_combo, 3, 0)
        options_layout.addWidget(self.resolution_label, 2, 1)
        options_layout.addWidget(self.resolution_combo, 3, 1)

        self.quality_hint = QLabel()
        self.quality_hint.setWordWrap(True)
        self.quality_hint.setStyleSheet("color:#68758b; padding:4px 0;")
        options_layout.addWidget(self.quality_hint, 3, 2)

        self.output_label = QLabel(self._t("输出文件夹"))
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(self._t("选择输出目录"))
        self.browse_output_button = QPushButton(self._t("浏览…"))
        self.open_output_button = QPushButton(self._t("打开目录"))
        self.browse_output_button.clicked.connect(self.choose_output_dir)
        self.open_output_button.clicked.connect(self.open_output_dir)

        options_layout.addWidget(self.output_label, 4, 0)
        options_layout.addWidget(self.output_edit, 5, 0, 1, 2)
        output_buttons = QHBoxLayout()
        output_buttons.addWidget(self.browse_output_button)
        output_buttons.addWidget(self.open_output_button)
        options_layout.addLayout(output_buttons, 5, 2)

        root.addWidget(options_panel)

        action_bar = QHBoxLayout()
        self.overall_label = QLabel(self._t("等待任务"))
        self.overall_label.setStyleSheet("color:#5f6d83;")
        self.cancel_button = QPushButton(self._t("取消任务"))
        self.cancel_button.setObjectName("DangerButton")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.start_button = QPushButton(self._t("开始处理"))
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.setMinimumWidth(190)
        self.start_button.clicked.connect(self.start_conversion)
        action_bar.addWidget(self.overall_label)
        action_bar.addStretch()
        action_bar.addWidget(self.cancel_button)
        action_bar.addWidget(self.start_button)
        root.addLayout(action_bar)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _restore_settings(self) -> None:
        default_dir = Path.home() / "Videos" / APP_NAME
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

    @Slot()
    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._t("选择音频或视频文件"),
            "",
            self._t("媒体文件") + " (*.mp4 *.mkv *.mov *.avi *.webm *.wmv *.flv *.m4v *.ts *.mts *.m2ts "
            "*.3gp *.vob *.mpg *.mpeg *.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma "
            "*.ac3 *.eac3 *.mka *.aiff *.ape *.amr);;"
            + self._t("所有文件") + " (*.*)",
        )
        self._add_paths([Path(item) for item in files])

    @Slot()
    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, self._t("选择媒体文件夹"))
        if not folder:
            return
        paths = [
            path for path in Path(folder).rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        self._add_paths(paths)

    def _add_paths(self, paths: list[Path]) -> None:
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
                or resolved.suffix.lower() not in SUPPORTED_EXTENSIONS
                or str(resolved) in existing
            ):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(resolved.name)
            name_item.setData(Qt.ItemDataRole.UserRole, str(resolved))
            name_item.setToolTip(str(resolved))
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(resolved.suffix.upper().lstrip(".")))
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
        self._update_count()

    @Slot()
    def clear_files(self) -> None:
        self.table.setRowCount(0)
        self.progress_bars.clear()
        self._update_count()

    def _update_count(self) -> None:
        self.file_count_label.setText(self._t(
            "{count} 个文件", count=self.table.rowCount()))

    @Slot()
    def _update_mode(self) -> None:
        mode = self.mode_combo.currentData()
        choices = {
            MODE_VIDEO: VIDEO_TARGETS,
            MODE_AUDIO: AUDIO_TARGETS,
            MODE_EXTRACT: EXTRACT_TARGETS,
            MODE_COMPRESS: COMPRESS_TARGETS,
        }.get(mode, VIDEO_TARGETS)
        previous = self.target_combo.currentData()
        self.target_combo.clear()
        for item in choices:
            self.target_combo.addItem(self._t(item), item)
        index = self.target_combo.findData(previous)
        if index >= 0:
            self.target_combo.setCurrentIndex(index)

        video_controls = mode in {MODE_VIDEO, MODE_COMPRESS}
        self.encoder_label.setVisible(video_controls)
        self.encoder_combo.setVisible(video_controls)
        self.resolution_label.setVisible(video_controls)
        self.resolution_combo.setVisible(video_controls)
        self._update_quality_hint()

    @Slot()
    def _update_quality_hint(self) -> None:
        target = self.target_combo.currentData()
        mode = self.mode_combo.currentData()
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

    def _current_paths(self) -> list[Path]:
        return [
            Path(str(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)))
            for row in range(self.table.rowCount())
        ]

    @Slot()
    def start_conversion(self) -> None:
        paths = self._current_paths()
        if not paths:
            self._notify(QMessageBox.Icon.Information, self._t("尚未添加文件"),
                         self._t("请先添加需要处理的音频或视频文件。"))
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
        self.worker = BatchWorker(paths, options)
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
            self.remove_button,
            self.clear_button,
            self.language_combo,
            self.mode_combo,
            self.target_combo,
            self.quality_combo,
            self.encoder_combo,
            self.resolution_combo,
            self.output_edit,
            self.browse_output_button,
        ):
            widget.setEnabled(not running)
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        if not running:
            self._update_quality_hint()
        self.overall_label.setText(
            self._t("正在处理…") if running else self._t("等待任务"))

    @Slot(int)
    def _item_started(self, row: int) -> None:
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setFormat(self._t("正在准备…"))
        self.progress_bars[row] = progress
        self.table.setCellWidget(row, 3, progress)
        self.table.scrollToItem(self.table.item(row, 0))
        self.overall_label.setText(self._t(
            "正在处理第 {current}/{total} 个文件",
            current=row + 1, total=self.table.rowCount()))

    @Slot(int, int, str)
    def _item_progress(self, row: int, percent: int, text: str) -> None:
        progress = self.progress_bars.get(row)
        if not progress:
            return
        if percent >= 0:
            progress.setValue(percent)
        progress.setFormat(text)

    @Slot(int, bool, str, str)
    def _item_finished(self, row: int, success: bool, message: str, output: str) -> None:
        self.table.setCellWidget(row, 3, None)
        status = QTableWidgetItem(
            message if success else self._t("失败：{message}", message=message))
        status.setForeground(Qt.GlobalColor.darkGreen if success else Qt.GlobalColor.darkRed)
        status.setToolTip(message)
        self.table.setItem(row, 3, status)
        output_item = QTableWidgetItem(Path(output).name if output else "")
        output_item.setToolTip(output)
        self.table.setItem(row, 4, output_item)

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
            return

        text = self._t("全部完成：成功 {successes} 个，失败 {failures} 个。",
                       successes=successes, failures=failures)
        self.statusBar().showMessage(text)
        self.overall_label.setText(text)
        if failures:
            self._notify(QMessageBox.Icon.Warning, self._t("处理完成"), text + "\n"
                         + self._t("可将鼠标停在失败状态上查看 FFmpeg 错误。"))
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
            '<p><a href="https://github.com/plao94619-hash/Repository-name-VideoToolBox">'
            + self._t("项目主页") + "</a></p>"
        )
        box.addButton(self._t("关闭"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if not self.worker and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: list[Path] = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if not local:
                continue
            path = Path(local)
            if path.is_dir():
                paths.extend(
                    item for item in path.rglob("*")
                    if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS
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
            box.setText(self._t("需要先停止当前转换。是否取消任务？"))
            yes_button = box.addButton(self._t("是"), QMessageBox.ButtonRole.YesRole)
            box.addButton(self._t("否"), QMessageBox.ButtonRole.NoRole)
            box.exec()
            if box.clickedButton() == yes_button:
                self.cancel_conversion()
            event.ignore()
            return
        event.accept()


def run_self_test() -> int:
    ok, message = self_test()
    safe_message = message.encode("ascii", errors="backslashreplace").decode("ascii")
    print(safe_message)
    return 0 if ok else 1


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
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
