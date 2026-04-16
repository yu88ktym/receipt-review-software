from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QDateEdit, QSpinBox, QFrame,
)
from PySide6.QtCore import Qt, QDate, Signal
from app.config import theme

# Since/Until の「指定なし」に相当するセンチネル値
_DATE_UNSET = QDate(2000, 1, 1)


class Sidebar(QWidget):
    """左サイドバー。更新ボタンとフィルタ入力欄を持つ。

    filter_changed シグナルはフィルタ値が変わるたびに発火し、
    現在のフィルタ辞書を持って一覧タブへ通知する。
    """
    filter_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(theme.SIDEBAR_WIDTH)
        self._build_ui()
        self._connect_filter_signals()

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
        self.status_combo.addItems(
            ["すべて", "INGESTED", "OCR_DONE", "OCR_FAILED", "FINAL_UPDATED", "FINAL_UPDATED_CHILD", "DROPPED"]
        )
        root.addWidget(self.status_combo)

        root.addWidget(QLabel("品質レベル"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["すべて", "UNKNOWN", "NO_PROBLEM", "OCR_LOW", "LOW"])
        root.addWidget(self.quality_combo)

        self.exclude_dups_chk = QCheckBox("重複除外")
        root.addWidget(self.exclude_dups_chk)

        root.addWidget(QLabel("Since"))
        self.since_date = QDateEdit()
        self.since_date.setDisplayFormat("yyyy-MM-dd")
        self.since_date.setCalendarPopup(True)
        self.since_date.setSpecialValueText("指定なし")
        self.since_date.setDate(_DATE_UNSET)
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

    def _connect_filter_signals(self) -> None:
        """各フィルタウィジェットの変更イベントを filter_changed シグナルに接続する。"""
        self.keyword_edit.textChanged.connect(self._emit_filter_changed)
        self.status_combo.currentIndexChanged.connect(self._emit_filter_changed)
        self.quality_combo.currentIndexChanged.connect(self._emit_filter_changed)
        self.exclude_dups_chk.stateChanged.connect(self._emit_filter_changed)
        self.since_date.dateChanged.connect(self._emit_filter_changed)
        self.until_date.dateChanged.connect(self._emit_filter_changed)
        self.page_size_spin.valueChanged.connect(self._emit_filter_changed)

    def _emit_filter_changed(self, *_args) -> None:
        self.filter_changed.emit(self.get_filters())

    def get_filters(self) -> dict:
        """現在のフィルタ値を辞書で返す。"""
        status_text = self.status_combo.currentText()
        quality_text = self.quality_combo.currentText()

        since_date = self.since_date.date()
        until_date = self.until_date.date()

        return {
            "keyword": self.keyword_edit.text().strip() or None,
            "status": None if status_text == "すべて" else status_text,
            "quality_level": None if quality_text == "すべて" else quality_text,
            "exclude_duplicates": self.exclude_dups_chk.isChecked(),
            "since": since_date.toString("yyyy-MM-dd") if since_date != _DATE_UNSET else None,
            "until": until_date.toString("yyyy-MM-dd"),
            "page_size": self.page_size_spin.value(),
        }


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
