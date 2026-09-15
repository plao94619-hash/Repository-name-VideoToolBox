"""Qt Widgets presentation tokens; no media-processing dependencies."""

from PySide6.QtGui import QColor, QPalette


COLORS = {
    "light": {
        "canvas": "#f5f6f8", "surface": "#ffffff", "surface_alt": "#f8f9fb",
        "stroke": "#e1e4e9", "text": "#20232a", "muted": "#606976",
        "subtle": "#858d98", "accent": "#365fb5", "accent_hover": "#294fa4",
        "accent_pressed": "#214288", "accent_soft": "#eaf0fc",
        "focus": "#527dcf", "hover": "#f0f3f7", "pressed": "#e7ebf2",
        "primary": "#365fb5", "primary_hover": "#294fa4", "primary_pressed": "#214288",
        "selection": "#e5edfb", "track": "#e9edf3",
        "success": "#18724d", "warning": "#996112", "error": "#b33636",
        "disabled": "#9ca3ae", "disabled_bg": "#f3f4f6",
    },
    "dark": {
        "canvas": "#16181d", "surface": "#20232a", "surface_alt": "#272b33",
        "stroke": "#363b46", "text": "#edf0f4", "muted": "#bac1cc",
        "subtle": "#959dac", "accent": "#6691e6", "accent_hover": "#7ba2ee",
        "accent_pressed": "#527fda", "accent_soft": "#293b5b",
        "focus": "#91b3f8", "hover": "#30343d", "pressed": "#383e48",
        "primary": "#365fb5", "primary_hover": "#4974c7", "primary_pressed": "#2b54a9",
        "selection": "#304463", "track": "#353b46",
        "success": "#6cdaa6", "warning": "#f0c16e", "error": "#f48f91",
        "disabled": "#777f8e", "disabled_bg": "#292d35",
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
QWidget { font-family: "Segoe UI Variable", "Segoe UI", "Microsoft YaHei UI";
          font-size: 13px; color: %(text)s; }
QMainWindow, QWidget#Content, QScrollArea#ContentScroll,
QScrollArea#ContentScroll > QWidget > QWidget { background: %(canvas)s; }
QFrame#Panel, QFrame#HeaderPanel, QFrame#ActionPanel {
    background: %(surface)s; border: 1px solid %(stroke)s; border-radius: 12px;
}
QLabel#AppTitle { font-size: 23px; font-weight: 700; color: %(text)s; }
QLabel#SectionTitle { font-size: 15px; font-weight: 700; color: %(text)s; }
QLabel#SectionHint, QLabel#AppSubtitle, QLabel#FieldLabel,
QLabel#SecondaryText, QLabel#FileCount { color: %(muted)s; }
QLabel#FileCount { background: %(surface_alt)s; border-radius: 8px;
                     padding: 7px 10px; }
QLabel#TaskState { color: %(muted)s; font-weight: 600; }
QLabel#TaskState[state="success"] { color: %(success)s; }
QLabel#TaskState[state="warning"] { color: %(warning)s; }
QLabel#TaskState[state="error"] { color: %(error)s; }
QPushButton { min-height: 36px; padding: 0 14px; border: 1px solid %(stroke)s;
              border-radius: 8px; background: %(surface)s; color: %(text)s;
              font-weight: 600; }
QPushButton:hover { background: %(hover)s; border-color: %(focus)s; }
QPushButton:pressed { background: %(pressed)s; }
QPushButton:focus { border: 2px solid %(focus)s; padding: 0 13px; }
QPushButton:disabled { color: %(disabled)s; background: %(disabled_bg)s;
                       border-color: %(stroke)s; }
QPushButton#PrimaryButton { min-height: 44px; background: %(primary)s;
                            color: #ffffff; border: 1px solid %(primary)s;
                            font-size: 14px; }
QPushButton#PrimaryButton:hover { background: %(primary_hover)s;
                                  border-color: %(primary_hover)s; }
QPushButton#PrimaryButton:pressed { background: %(primary_pressed)s; }
QPushButton#PrimaryButton:focus { border: 2px solid %(focus)s; }
QPushButton#PrimaryButton:disabled { background: %(disabled_bg)s;
                                     color: %(disabled)s; border-color: %(stroke)s; }
QPushButton#DangerButton { color: %(error)s; }
QPushButton#DangerButton:disabled { color: %(disabled)s; }
QComboBox, QLineEdit { min-height: 37px; padding: 0 10px;
                       background: %(surface)s; color: %(text)s;
                       border: 1px solid %(stroke)s; border-radius: 8px;
                       selection-background-color: %(selection)s;
                       selection-color: %(text)s; }
QComboBox:hover, QLineEdit:hover { border-color: %(subtle)s; }
QComboBox:focus, QLineEdit:focus { border: 2px solid %(focus)s; padding: 0 9px; }
QComboBox:disabled, QLineEdit:disabled { background: %(disabled_bg)s;
                                        color: %(disabled)s; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView { background: %(surface)s; color: %(text)s;
                              selection-background-color: %(selection)s;
                              selection-color: %(text)s;
                              border: 1px solid %(stroke)s; outline: 0; }
QTableWidget { background: %(surface)s; alternate-background-color: %(surface_alt)s;
               color: %(text)s; border: 1px solid %(stroke)s; border-radius: 8px;
               gridline-color: %(stroke)s; outline: 0;
               selection-background-color: %(selection)s; selection-color: %(text)s; }
QTableWidget:focus { border: 2px solid %(focus)s; }
QTableWidget::item { padding: 5px 7px; border: none; }
QTableWidget::item:hover { background: %(hover)s; }
QTableWidget::item:selected { background: %(selection)s; color: %(text)s; }
QHeaderView::section { background: %(surface_alt)s; color: %(muted)s;
                       border: none; border-bottom: 1px solid %(stroke)s;
                       padding: 9px 7px; font-weight: 600; }
QProgressBar { min-height: 20px; background: %(track)s; color: %(text)s;
               border: none; border-radius: 7px; text-align: center; }
QProgressBar::chunk { background: %(accent)s; border-radius: 7px; }
QMenuBar, QStatusBar { background: %(surface)s; color: %(muted)s; }
QMenuBar::item { padding: 6px 10px; background: transparent; border-radius: 6px; }
QMenuBar::item:selected { background: %(hover)s; }
QMenu { background: %(surface)s; color: %(text)s; border: 1px solid %(stroke)s;
        padding: 5px; }
QMenu::item { padding: 6px 26px; border-radius: 5px; }
QMenu::item:selected { background: %(selection)s; }
QStatusBar { border-top: 1px solid %(stroke)s; }
QScrollBar:vertical { background: %(surface_alt)s; width: 10px; margin: 1px; }
QScrollBar::handle:vertical { background: %(subtle)s; min-height: 24px;
                              border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
""" % c
