"""Qt Widgets presentation tokens; no media-processing dependencies."""

from PySide6.QtGui import QColor, QPalette


COLORS = {
    "light": {
        "canvas": "#f3f5f8", "surface": "#ffffff", "surface_alt": "#f7f9fc",
        "header": "#fbfcff", "stroke": "#e1e6ed", "stroke_strong": "#cdd5df",
        "text": "#171a21", "muted": "#5f6875", "subtle": "#8a94a3",
        "accent": "#3869c9", "accent_hover": "#2f5db5",
        "accent_pressed": "#264e99", "accent_soft": "#eaf1ff",
        "focus": "#4a78d1", "hover": "#f1f4f8", "pressed": "#e8edf4",
        "primary": "#3568d4", "primary_hover": "#2e5fc3", "primary_pressed": "#264fa4",
        "selection": "#e8f0ff", "track": "#e9edf3", "neutral_badge": "#edf0f4",
        "success": "#14764f", "success_bg": "#e4f5ed",
        "warning": "#996112", "warning_bg": "#fff3d8",
        "error": "#b33b3b", "error_bg": "#fdebea",
        "disabled": "#9aa3af", "disabled_bg": "#f1f3f6",
    },
    "dark": {
        "canvas": "#11141a", "surface": "#1a1e26", "surface_alt": "#212630",
        "header": "#191e28", "stroke": "#303744", "stroke_strong": "#46505f",
        "text": "#f1f3f6", "muted": "#b7bfcb", "subtle": "#8791a0",
        "accent": "#7aa2f2", "accent_hover": "#8cb0f6",
        "accent_pressed": "#638ddd", "accent_soft": "#263956",
        "focus": "#91b3f8", "hover": "#282e39", "pressed": "#303744",
        "primary": "#4778d8", "primary_hover": "#5b88e1", "primary_pressed": "#3967c4",
        "selection": "#2b4163", "track": "#313844", "neutral_badge": "#2c323d",
        "success": "#72d9a8", "success_bg": "#203d34",
        "warning": "#f0c16e", "warning_bg": "#46391f",
        "error": "#f29598", "error_bg": "#482b2e",
        "disabled": "#747d8b", "disabled_bg": "#252a33",
    },
}


def make_palette(theme: str) -> QPalette:
    c = COLORS[theme]
    palette = QPalette()
    for role, key in (
        (QPalette.ColorRole.Window, "canvas"),
        (QPalette.ColorRole.WindowText, "text"),
        (QPalette.ColorRole.Base, "surface"),
        (QPalette.ColorRole.AlternateBase, "surface_alt"),
        (QPalette.ColorRole.Text, "text"),
        (QPalette.ColorRole.Button, "surface"),
        (QPalette.ColorRole.ButtonText, "text"),
        (QPalette.ColorRole.Highlight, "selection"),
        (QPalette.ColorRole.HighlightedText, "text"),
        (QPalette.ColorRole.ToolTipBase, "surface"),
        (QPalette.ColorRole.ToolTipText, "text"),
    ):
        palette.setColor(role, QColor(c[key]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(c["subtle"]))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText,
                 QPalette.ColorRole.WindowText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(c["disabled"]))
    return palette


def make_stylesheet(theme: str) -> str:
    c = COLORS[theme]
    return """
QWidget { font-family: "Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI",
                      "Microsoft YaHei UI"; font-size: 13px; color: %(text)s; }
QMainWindow, QWidget#Content, QScrollArea#ContentScroll,
QScrollArea#ContentScroll > QWidget > QWidget { background: %(canvas)s; }
QFrame#Panel { background: %(surface)s; border: 1px solid %(stroke)s;
               border-radius: 14px; }
QFrame#Panel[dragActive="true"] { border: 2px dashed %(accent)s; }
QFrame#HeaderPanel { background: %(header)s; border: 1px solid %(stroke)s;
                     border-radius: 16px; }
QFrame#ActionPanel { background: %(surface)s; border: none;
                     border-top: 1px solid %(stroke)s; }
QFrame#DropZone { background: %(surface_alt)s; border: 1px dashed %(stroke_strong)s;
                  border-radius: 12px; }
QFrame#DropZone:hover { border-color: %(accent)s; background: %(accent_soft)s; }
QFrame#DropZone[dragActive="true"] { border: 2px dashed %(accent)s;
                                     background: %(accent_soft)s; }
QWidget#HeaderControls { background: transparent; }
QLabel#AppTitle { font-family: "Segoe UI Variable Display", "Segoe UI Variable",
                              "Segoe UI", "Microsoft YaHei UI";
                  font-size: 24px; font-weight: 700; color: %(text)s; }
QLabel#SectionTitle { font-size: 16px; font-weight: 700; color: %(text)s; }
QLabel#SectionIcon { background: %(accent_soft)s; border-radius: 9px; padding: 7px; }
QLabel#PrivacyBadge { color: %(success)s; background: %(success_bg)s;
                      border-radius: 9px; padding: 5px 9px; font-weight: 600; }
QLabel#DropIcon { background: %(accent_soft)s; border-radius: 16px; }
QLabel#DropTitle { font-size: 15px; font-weight: 700; color: %(text)s; }
QLabel#DropSubtitle { color: %(muted)s; }
QLabel#AppVersion { color: %(subtle)s; font-size: 12px; }
QLabel#SectionHint, QLabel#AppSubtitle, QLabel#FieldLabel,
QLabel#SecondaryText, QLabel#FileCount { color: %(muted)s; }
QLabel#FieldLabel { font-size: 12px; font-weight: 600; }
QLabel#FileCount { background: %(surface_alt)s; border: 1px solid %(stroke)s;
                   border-radius: 9px; padding: 5px 10px; font-weight: 600; }
QLabel#QualityHint { background: %(accent_soft)s; color: %(muted)s;
                     border-radius: 9px; padding: 9px 11px; }
QLabel#TaskState { color: %(muted)s; font-weight: 600; }
QLabel#TaskState[state="active"] { color: %(accent)s; }
QLabel#TaskState[state="success"] { color: %(success)s; }
QLabel#TaskState[state="warning"] { color: %(warning)s; }
QLabel#TaskState[state="error"] { color: %(error)s; }
QPushButton { min-height: 36px; padding: 0 14px; border: 1px solid %(stroke)s;
              border-radius: 9px; background: %(surface)s; color: %(text)s;
              font-weight: 600; }
QPushButton:hover { background: %(hover)s; border-color: %(stroke_strong)s; }
QPushButton:pressed { background: %(pressed)s; }
QPushButton:focus { border: 2px solid %(focus)s; padding: 0 13px; }
QPushButton:disabled { color: %(disabled)s; background: %(disabled_bg)s;
                       border-color: %(stroke)s; }
QPushButton[role="toolbar"] { min-height: 34px; padding: 0 12px;
                              background: %(surface_alt)s; }
QPushButton[role="ghost"] { background: transparent; border-color: transparent; }
QPushButton[role="ghost"]:hover { background: %(hover)s; border-color: %(stroke)s; }
QPushButton[role="danger"] { color: %(error)s; background: transparent; }
QPushButton[role="danger"]:hover { background: %(error_bg)s; border-color: %(error)s; }
QPushButton[role="accentSoft"] { color: %(accent)s; background: %(accent_soft)s;
                                 border-color: transparent; }
QPushButton[role="accentSoft"]:hover { border-color: %(accent)s; }
QPushButton#PrimaryButton { min-height: 44px; background: %(primary)s;
                            color: #ffffff; border: 1px solid %(primary)s;
                            border-radius: 10px; font-size: 14px; padding: 0 20px; }
QPushButton#PrimaryButton:hover { background: %(primary_hover)s;
                                  border-color: %(primary_hover)s; }
QPushButton#PrimaryButton:pressed { background: %(primary_pressed)s; }
QPushButton#PrimaryButton:focus { border: 2px solid %(focus)s; }
QPushButton#PrimaryButton:disabled { background: %(disabled_bg)s;
                                     color: %(disabled)s; border-color: %(stroke)s; }
QComboBox, QLineEdit { min-height: 39px; padding: 0 11px;
                       background: %(surface_alt)s; color: %(text)s;
                       border: 1px solid %(stroke)s; border-radius: 9px;
                       selection-background-color: %(selection)s;
                       selection-color: %(text)s; }
QComboBox:hover, QLineEdit:hover { background: %(surface)s;
                                   border-color: %(stroke_strong)s; }
QComboBox:focus, QLineEdit:focus { background: %(surface)s;
                                   border: 2px solid %(focus)s; padding: 0 10px; }
QComboBox:disabled, QLineEdit:disabled { background: %(disabled_bg)s;
                                        color: %(disabled)s; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox QAbstractItemView { background: %(surface)s; color: %(text)s;
                              selection-background-color: %(selection)s;
                              selection-color: %(text)s; border: 1px solid %(stroke)s;
                              border-radius: 8px; padding: 4px; outline: 0; }
QTableWidget { background: %(surface)s; alternate-background-color: %(surface_alt)s;
               color: %(text)s; border: 1px solid %(stroke)s; border-radius: 10px;
               gridline-color: %(stroke)s; outline: 0;
               selection-background-color: %(selection)s; selection-color: %(text)s; }
QTableWidget:focus { border: 2px solid %(focus)s; }
QTableWidget::item { padding: 6px 8px; border: none; }
QTableWidget::item:hover { background: %(hover)s; }
QTableWidget::item:selected { background: %(selection)s; color: %(text)s; }
QHeaderView::section { background: %(surface_alt)s; color: %(muted)s;
                       border: none; border-bottom: 1px solid %(stroke)s;
                       padding: 10px 8px; font-size: 12px; font-weight: 600; }
QProgressBar { min-height: 20px; background: %(track)s; color: %(text)s;
               border: none; border-radius: 7px; text-align: center; }
QProgressBar::chunk { background: %(accent)s; border-radius: 7px; }
QProgressBar#OverallProgress { min-height: 4px; max-height: 4px; border-radius: 2px; }
QProgressBar#OverallProgress::chunk { border-radius: 2px; }
QMenuBar, QStatusBar { background: %(surface)s; color: %(muted)s; }
QMenuBar { border-bottom: 1px solid %(stroke)s; }
QMenuBar::item { padding: 6px 11px; margin: 2px; background: transparent;
                 border-radius: 6px; }
QMenuBar::item:selected { background: %(hover)s; }
QMenu { background: %(surface)s; color: %(text)s; border: 1px solid %(stroke)s;
        border-radius: 8px; padding: 5px; }
QMenu::item { padding: 7px 28px; border-radius: 6px; }
QMenu::item:selected { background: %(selection)s; }
QStatusBar { border-top: 1px solid %(stroke)s; }
QToolTip { background: %(surface)s; color: %(text)s; border: 1px solid %(stroke_strong)s;
           border-radius: 6px; padding: 6px; }
QMessageBox { background: %(surface)s; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: %(stroke_strong)s; min-height: 28px;
                              border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: %(subtle)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: %(stroke_strong)s; min-width: 28px;
                                border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
""" % c
