from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

FONT_FAMILY = "Noto Sans CJK JP"
FONT_FAMILY_FALLBACK = "sans-serif"
FONT_SIZE_BASE = 10
FONT_SIZE_HEADING = 14

COLOR_PRIMARY = "#1976D2"
COLOR_ACCENT = "#FF9800"
COLOR_BACKGROUND = "#FFFFFF"
COLOR_DIVIDER = "#E6E6E6"

MARGIN = 8
PADDING = 12

SIDEBAR_WIDTH = 250
DETAIL_PANEL_WIDTH_PERCENT = 23


def apply_application_font(app: QApplication) -> None:
    font = QFont(FONT_FAMILY, FONT_SIZE_BASE)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)


STYLESHEET = f"""
QWidget {{
    font-family: "{FONT_FAMILY}", {FONT_FAMILY_FALLBACK};
    font-size: {FONT_SIZE_BASE}pt;
    background-color: {COLOR_BACKGROUND};
}}

QLabel[heading="true"] {{
    font-size: {FONT_SIZE_HEADING}pt;
    font-weight: bold;
}}

QPushButton {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 4px {PADDING}px;
}}

QPushButton:hover {{
    background-color: #1565C0;
}}

QPushButton:pressed {{
    background-color: #0D47A1;
}}

QPushButton[flat="true"] {{
    background-color: transparent;
    color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_PRIMARY};
}}

QPushButton[flat="true"]:hover {{
    background-color: #E3F2FD;
}}

QPushButton[danger="true"] {{
    background-color: #D32F2F;
}}

QPushButton[danger="true"]:hover {{
    background-color: #B71C1C;
}}

QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    border: 1px solid {COLOR_DIVIDER};
    border-radius: 4px;
    padding: 4px 6px;
    background-color: {COLOR_BACKGROUND};
}}

QLineEdit:focus, QDateEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {COLOR_PRIMARY};
}}

QTableWidget {{
    border: 1px solid {COLOR_DIVIDER};
    gridline-color: {COLOR_DIVIDER};
    selection-background-color: #E3F2FD;
    selection-color: #000000;
}}

QTableWidget QHeaderView::section {{
    background-color: #F5F5F5;
    border: none;
    border-bottom: 1px solid {COLOR_DIVIDER};
    border-right: 1px solid {COLOR_DIVIDER};
    padding: 4px {MARGIN}px;
    font-weight: bold;
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_DIVIDER};
}}

QTabBar::tab {{
    padding: 6px 14px;
    border: 1px solid {COLOR_DIVIDER};
    border-bottom: none;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_BACKGROUND};
    border-bottom: 2px solid {COLOR_PRIMARY};
    color: {COLOR_PRIMARY};
}}

QTabBar::tab:!selected {{
    background-color: #F5F5F5;
}}

QScrollArea {{
    border: none;
}}

QGroupBox {{
    border: 1px solid {COLOR_DIVIDER};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {COLOR_DIVIDER};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLOR_PRIMARY};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSplitter::handle {{
    background-color: {COLOR_DIVIDER};
    width: 1px;
}}
"""
