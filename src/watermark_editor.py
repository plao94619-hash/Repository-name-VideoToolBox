"""Interactive, theme-aware editor for visible watermark repair regions."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QImage,
    QImageReader,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from i18n import translate
from watermark_repair import MAX_REGIONS, MAX_SELECTED_AREA, WatermarkRegion


class WatermarkSelectionCanvas(QWidget):
    """Image canvas that records normalized drag rectangles."""

    regions_changed = Signal()

    def __init__(self, image: QImage, parent: QWidget | None = None):
        super().__init__(parent)
        self.image = image
        self._regions: list[WatermarkRegion] = []
        self._drag_origin: QPointF | None = None
        self._drag_point: QPointF | None = None
        self.setObjectName("WatermarkCanvas")
        self.setMinimumSize(520, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAccessibleName("Visible watermark selection canvas")

    def sizeHint(self) -> QSize:
        return QSize(820, 500)

    def regions(self) -> tuple[WatermarkRegion, ...]:
        return tuple(self._regions)

    def set_regions(self, regions: tuple[WatermarkRegion, ...]) -> None:
        self._regions = list(regions[:MAX_REGIONS])
        self.regions_changed.emit()
        self.update()

    def undo(self) -> None:
        if self._regions:
            self._regions.pop()
            self.regions_changed.emit()
            self.update()

    def clear(self) -> None:
        if self._regions:
            self._regions.clear()
            self.regions_changed.emit()
            self.update()

    def _image_rect(self) -> QRectF:
        if self.image.isNull() or self.width() <= 0 or self.height() <= 0:
            return QRectF()
        bounds = QRectF(self.rect()).adjusted(14, 14, -14, -14)
        scale = min(bounds.width() / self.image.width(),
                    bounds.height() / self.image.height())
        width = self.image.width() * scale
        height = self.image.height() * scale
        return QRectF(
            bounds.center().x() - width / 2,
            bounds.center().y() - height / 2,
            width,
            height,
        )

    def _region_rect(self, region: WatermarkRegion) -> QRectF:
        image_rect = self._image_rect()
        return QRectF(
            image_rect.left() + region.x * image_rect.width(),
            image_rect.top() + region.y * image_rect.height(),
            region.width * image_rect.width(),
            region.height * image_rect.height(),
        )

    def _bounded_point(self, point: QPointF) -> QPointF:
        image_rect = self._image_rect()
        return QPointF(
            min(image_rect.right(), max(image_rect.left(), point.x())),
            min(image_rect.bottom(), max(image_rect.top(), point.y())),
        )

    def _selection_from_drag(self) -> QRectF:
        if self._drag_origin is None or self._drag_point is None:
            return QRectF()
        return QRectF(self._drag_origin, self._drag_point).normalized().intersected(
            self._image_rect())

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.palette().color(self.backgroundRole()))
        image_rect = self._image_rect()
        if image_rect.isEmpty():
            return

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(image_rect, self.image)
        painter.setPen(QPen(self.palette().color(self.foregroundRole()), 1))
        painter.drawRoundedRect(image_rect, 5, 5)

        for index, region in enumerate(self._regions, start=1):
            rect = self._region_rect(region)
            painter.fillRect(rect, QColor(217, 67, 76, 76))
            painter.setPen(QPen(QColor("#ef5962"), 2))
            painter.drawRoundedRect(rect, 3, 3)
            badge = QRectF(rect.left() + 5, rect.top() + 5, 24, 22)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#d9434c"))
            painter.drawRoundedRect(badge, 7, 7)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, str(index))

        drag_rect = self._selection_from_drag()
        if not drag_rect.isEmpty():
            painter.fillRect(drag_rect, QColor(56, 105, 201, 58))
            painter.setPen(QPen(QColor("#4f82e1"), 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(drag_rect, 3, 3)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (event.button() == Qt.MouseButton.LeftButton
                and len(self._regions) < MAX_REGIONS
                and self._image_rect().contains(event.position())):
            self._drag_origin = self._bounded_point(event.position())
            self._drag_point = self._drag_origin
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is not None:
            self._drag_point = self._bounded_point(event.position())
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_origin is not None:
            self._drag_point = self._bounded_point(event.position())
            rect = self._selection_from_drag()
            image_rect = self._image_rect()
            if rect.width() >= 6 and rect.height() >= 6 and not image_rect.isEmpty():
                region = WatermarkRegion(
                    (rect.left() - image_rect.left()) / image_rect.width(),
                    (rect.top() - image_rect.top()) / image_rect.height(),
                    rect.width() / image_rect.width(),
                    rect.height() / image_rect.height(),
                )
                if sum(item.area for item in self._regions) + region.area <= MAX_SELECTED_AREA:
                    self._regions.append(region)
                    self.regions_changed.emit()
            self._drag_origin = None
            self._drag_point = None
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class WatermarkRegionDialog(QDialog):
    """Modal editor that keeps all copy localized and leaves source untouched."""

    def __init__(
        self,
        source: Path,
        regions: tuple[WatermarkRegion, ...],
        language: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.language = language
        self.source = source
        self.setWindowTitle(self._t("框选可见水印区域"))
        self.setModal(True)
        self.resize(940, 700)
        self.setMinimumSize(680, 540)

        reader = QImageReader(str(source))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            raise ValueError(self._t("所选文件不是可读取的图片。"))

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel(self._t("框选需要修复的可见水印"))
        title.setObjectName("SectionTitle")
        root.addWidget(title)
        subtitle = QLabel(self._t(
            "在预览图上拖动鼠标框选水印，可添加多个区域；框选时尽量贴合水印边缘。"))
        subtitle.setObjectName("SectionHint")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        source_label = QLabel(source.name)
        source_label.setObjectName("FileCount")
        source_label.setToolTip(str(source))
        source_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        root.addWidget(source_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.canvas = WatermarkSelectionCanvas(image)
        self.canvas.set_regions(regions)
        root.addWidget(self.canvas, 1)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.undo_button = QPushButton(self._t("撤销上一步"))
        self.undo_button.setProperty("role", "ghost")
        self.undo_button.clicked.connect(self.canvas.undo)
        self.clear_button = QPushButton(self._t("清空区域"))
        self.clear_button.setProperty("role", "danger")
        self.clear_button.clicked.connect(self.canvas.clear)
        self.region_label = QLabel()
        self.region_label.setObjectName("SecondaryText")
        controls.addWidget(self.undo_button)
        controls.addWidget(self.clear_button)
        controls.addStretch()
        controls.addWidget(self.region_label)
        root.addLayout(controls)

        notice = QLabel(self._t(
            "仅用于你拥有或获授权编辑的图片。此功能只修复手动框选的可见区域，不检测或移除 C2PA、版权归属、平台溯源或其他不可见指纹。队列中的图片将使用相同的相对位置。"))
        notice.setObjectName("QualityHint")
        notice.setWordWrap(True)
        root.addWidget(notice)

        buttons = QDialogButtonBox()
        self.cancel_button = buttons.addButton(
            self._t("取消"), QDialogButtonBox.ButtonRole.RejectRole)
        self.save_button = buttons.addButton(
            self._t("保存区域"), QDialogButtonBox.ButtonRole.AcceptRole)
        self.save_button.setObjectName("PrimaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        undo_action = QAction(self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.canvas.undo)
        self.addAction(undo_action)
        self.canvas.regions_changed.connect(self._update_state)
        self._update_state()

    def _t(self, key: str, **values: object) -> str:
        return translate(key, self.language, **values)

    def regions(self) -> tuple[WatermarkRegion, ...]:
        return self.canvas.regions()

    def _update_state(self) -> None:
        count = len(self.canvas.regions())
        self.region_label.setText(self._t("已选择 {count} 个区域", count=count))
        self.undo_button.setEnabled(count > 0)
        self.clear_button.setEnabled(count > 0)
        self.save_button.setEnabled(count > 0)
