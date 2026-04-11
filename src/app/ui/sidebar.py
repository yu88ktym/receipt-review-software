from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QDateEdit, QSpinBox, QFrame,
)
from PySide6.QtCore import Qt, QDate
from app.config import theme


class Sidebar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(theme.SIDEBAR_WIDTH)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        self.refresh_btn = QPushButton("⟳ 更新")
        root.addWidget(self.refresh_btn)

        root.addWidget(_divider())

        heading = QLabel("フィルタ")
        heading.setProperty("heading", "true")
        root.addWidget(heading)

        root.addWidget(QLabel("キーワード"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("キーワードを入力")
        root.addWidget(self.keyword_edit)

        root.addWidget(QLabel("ステータス"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["すべて", "PENDING", "REVIEWED", "FINAL_UPDATED", "TRASHED"])
        root.addWidget(self.status_combo)

        root.addWidget(QLabel("品質レベル"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["すべて", "HIGH", "MEDIUM", "LOW", "UNSET"])
        root.addWidget(self.quality_combo)

        self.exclude_dups_chk = QCheckBox("重複除外")
        root.addWidget(self.exclude_dups_chk)

        root.addWidget(QLabel("Since"))
        self.since_date = QDateEdit()
        self.since_date.setDisplayFormat("yyyy-MM-dd")
        self.since_date.setCalendarPopup(True)
        self.since_date.setSpecialValueText("指定なし")
        self.since_date.setDate(QDate(2000, 1, 1))
        root.addWidget(self.since_date)

        root.addWidget(QLabel("Until"))
        self.until_date = QDateEdit()
        self.until_date.setDisplayFormat("yyyy-MM-dd")
        self.until_date.setCalendarPopup(True)
        self.until_date.setSpecialValueText("指定なし")
        self.until_date.setDate(QDate.currentDate())
        root.addWidget(self.until_date)

        root.addWidget(QLabel("ページサイズ"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(1, 500)
        self.page_size_spin.setValue(50)
        root.addWidget(self.page_size_spin)

        root.addStretch()


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
