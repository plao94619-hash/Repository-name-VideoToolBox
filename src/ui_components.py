"""Small, reusable presentation widgets for the desktop interface."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)


_ICON_CONTENT = {
    "add": '<path d="M12 5v14M5 12h14"/>',
    "folder": '<path d="M3.5 7.5h6l2-2h9a1.5 1.5 0 0 1 1.5 1.5v11.5a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z"/>',
    "folder_open": '<path d="M3.5 7.5h6l2-2h8.5a2 2 0 0 1 2 2v2H7a2 2 0 0 0-1.8 1.1L2 17V9.5a2 2 0 0 1 1.5-2Z"/><path d="M7 9.5h14.2a1 1 0 0 1 .9 1.45l-4 8a2 2 0 0 1-1.8 1.05H3.2l3-9.4A.9.9 0 0 1 7 9.5Z"/>',
    "remove": '<path d="M5 7h14M9 7V4.5h6V7M7.5 7l.8 13h7.4l.8-13M10 10.5v6M14 10.5v6"/>',
    "clear": '<path d="m7 4 13 13-3 3L4 7l3-3Z"/><path d="m11.5 8.5-5 5M12 20h9"/>',
    "play": '<path d="m9 6 9 6-9 6V6Z"/>',
    "stop": '<rect x="7" y="7" width="10" height="10" rx="2"/>',
    "copy": '<rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
    "external": '<path d="M13 5h6v6M19 5l-8 8"/><path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/>',
    "settings": '<path d="M4 7h10M18 7h2M14 5v4M4 12h4M12 12h8M9 10v4M4 17h2M10 17h10M7 15v4"/>',
    "queue": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 9h8M8 13h8M8 17h5"/>',
    "file": '<path d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "shield": '<path d="M12 3 20 6v5c0 5-3.3 8.4-8 10-4.7-1.6-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "warning": '<path d="M12 3 2.5 20h19L12 3Z"/><path d="M12 9v5M12 17.5v.1"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.1"/>',
    "language": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.4 3 14.6 0 18M12 3c-3 3.4-3 14.6 0 18"/>',
    "theme": '<path d="M20 15.2A8.5 8.5 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2Z"/>',
}


def make_icon(name: str, color: str, size: int = 18) -> QIcon:
    """Render a crisp, theme-aware line icon at common device pixel ratios."""
    content = _ICON_CONTENT[name]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (color, content)
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    icon = QIcon()
    for ratio in (1, 2, 3):
        pixels = size * ratio
        pixmap = QPixmap(pixels, pixels)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        pixmap.setDevicePixelRatio(ratio)
        icon.addPixmap(pixmap)
    return icon


class BrandMark(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._accent = QColor("#3568d4")
        self.setFixedSize(48, 48)
        self.setAccessibleName("Universal Media Toolbox")

    def set_accent(self, color: str) -> None:
        self._accent = QColor(color)
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._accent)
        painter.drawRoundedRect(QRectF(1, 1, 46, 46), 13, 13)
        painter.setBrush(QColor("#ffffff"))
        triangle = QPainterPath()
        triangle.moveTo(19, 15)
        triangle.lineTo(33, 24)
        triangle.lineTo(19, 33)
        triangle.closeSubpath()
        painter.drawPath(triangle)
        painter.setBrush(QColor(255, 255, 255, 145))
        painter.drawRoundedRect(QRectF(11, 17, 3, 14), 1.5, 1.5)


class EmptyDropZone(QFrame):
    add_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setMinimumHeight(260)
        self.setAcceptDrops(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 30, 28, 30)
        layout.setSpacing(8)
        layout.addStretch()
        self.icon_label = QLabel()
        self.icon_label.setObjectName("DropIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(52, 52)
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(4)
        self.title_label = QLabel()
        self.title_label.setObjectName("DropTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("DropSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(8)
        self.add_button = QPushButton()
        self.add_button.setProperty("role", "accentSoft")
        self.add_button.clicked.connect(self.add_requested)
        layout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

    def set_texts(self, title: str, subtitle: str, button: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.add_button.setText(button)

    def set_theme(self, colors: dict[str, str]) -> None:
        self.icon_label.setPixmap(make_icon("file", colors["accent"], 25).pixmap(25, 25))
        self.add_button.setIcon(make_icon("add", colors["accent"], 17))
        self.add_button.setIconSize(QSize(17, 17))


class MediaTableDelegate(QStyledItemDelegate):
    """Paint compact type tags and semantic status pills without changing table data."""

    def __init__(self, colors: dict[str, str], parent: QWidget | None = None):
        super().__init__(parent)
        self.colors = colors

    def set_colors(self, colors: dict[str, str]) -> None:
        self.colors = colors

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        state = index.data(Qt.ItemDataRole.UserRole)
        is_type = index.column() == 1 and bool(index.data(Qt.ItemDataRole.DisplayRole))
        is_status = index.column() == 3 and state in {"pending", "success", "failed"}
        if not (is_type or is_status):
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text = opt.text
        opt.text = ""
        style = opt.widget.style() if opt.widget else None
        if style:
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(option.font)
        font.setPointSizeF(max(font.pointSizeF() - 0.5, 8.0))
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        if is_type:
            foreground = self.colors["accent"]
            background = self.colors["accent_soft"]
            dot = None
        else:
            palette = {
                "pending": (self.colors["muted"], self.colors["neutral_badge"], self.colors["subtle"]),
                "success": (self.colors["success"], self.colors["success_bg"], self.colors["success"]),
                "failed": (self.colors["error"], self.colors["error_bg"], self.colors["error"]),
            }
            foreground, background, dot = palette[state]

        dot_space = 13 if dot else 0
        ideal_width = metrics.horizontalAdvance(text) + 18 + dot_space
        width = min(ideal_width, max(option.rect.width() - 14, 34))
        height = min(26, option.rect.height() - 10)
        badge = QRectF(option.rect.left() + 7, option.rect.center().y() - height / 2, width, height)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(badge, height / 2, height / 2)
        text_left = badge.left() + 9
        if dot:
            painter.setBrush(QColor(dot))
            painter.drawEllipse(QRectF(text_left, badge.center().y() - 3, 6, 6))
            text_left += dot_space
        painter.setPen(QColor(foreground))
        available = int(badge.right() - text_left - 8)
        shown = metrics.elidedText(text, Qt.TextElideMode.ElideRight, available)
        painter.drawText(
            QRectF(text_left, badge.top(), available, badge.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            shown,
        )
        painter.restore()
