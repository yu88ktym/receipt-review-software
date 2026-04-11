from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.status_colors import apply_row_colors

_HEADERS = ["レシートID", "アップロード日", "購入日", "合計金額", "店名", "支払方法", "ステータス/重要", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 6

_DUMMY_ROWS = [
    ("R-0001", "2024-01-15", "2024-01-14", "¥3,200", "コンビニA", "現金", "FINAL_UPDATED"),
    ("R-0002", "2024-01-16", "2024-01-15", "¥1,500", "スーパーB", "クレジット", "REVIEWED"),
    ("R-0003", "2024-01-17", "2024-01-16", "¥8,400", "レストランC", "電子マネー", "PENDING"),
    ("R-0004", "2024-01-18", "2024-01-17", "¥640", "カフェD", "現金", "PENDING"),
    ("R-0005", "2024-01-19", "2024-01-18", "¥12,000", "百貨店E", "クレジット", "FINAL_UPDATED"),
]


class TabList(QWidget):
    detail_requested = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._page = 1
        self._total_pages = 3
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        self.table = QTableWidget(0, len(_HEADERS))
        self.table.setHorizontalHeaderLabels(_HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(len(_HEADERS) - 1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(len(_HEADERS) - 1, 80)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        root.addWidget(self.table)

        # ページネーション
        pager = QHBoxLayout()
        self.prev_btn = QPushButton("◀ 前へ")
        self.prev_btn.setProperty("flat", "true")
        self.prev_btn.clicked.connect(self._prev_page)
        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_btn = QPushButton("次へ ▶")
        self.next_btn.setProperty("flat", "true")
        self.next_btn.clicked.connect(self._next_page)

        pager.addStretch()
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_label)
        pager.addWidget(self.next_btn)
        pager.addStretch()
        root.addLayout(pager)

        self._update_pager()

    def _populate(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for row_data in _DUMMY_ROWS:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
            detail_btn = QPushButton("詳細")
            detail_btn.clicked.connect(lambda checked, r=row_data: self._on_detail(r))
            self.table.setCellWidget(row, len(_HEADERS) - 1, detail_btn)
        self._apply_row_colors()
        self.table.setSortingEnabled(True)

    def _apply_row_colors(self) -> None:
        apply_row_colors(self.table, _STATUS_COL)

    def _on_detail(self, row_data: tuple) -> None:
        keys = ["receipt_id", "upload_date", "purchase_date", "total_amount",
                "store_name", "payment_method", "status"]
        self.detail_requested.emit(dict(zip(keys, row_data)))

    def _prev_page(self) -> None:
        if self._page > 1:
            self._page -= 1
            self._update_pager()

    def _next_page(self) -> None:
        if self._page < self._total_pages:
            self._page += 1
            self._update_pager()

    def _update_pager(self) -> None:
        self.page_label.setText(f"ページ {self._page} / {self._total_pages}")
        self.prev_btn.setEnabled(self._page > 1)
        self.next_btn.setEnabled(self._page < self._total_pages)
