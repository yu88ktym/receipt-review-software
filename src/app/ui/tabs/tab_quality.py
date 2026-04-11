from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QCheckBox, QHeaderView, QFrame,
    QGroupBox,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.status_colors import get_row_color

_HEADERS = ["画像ID", "サムネイル", "ステータス", "品質", "重複", "ゴミ箱", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 2

_DUMMY_ROWS = [
    ("IMG-001", "—", "REVIEWED", "HIGH", "なし", "—"),
    ("IMG-002", "—", "PENDING", "LOW", "あり", "—"),
    ("IMG-003", "—", "FINAL_UPDATED", "MEDIUM", "なし", "—"),
]


class TabQuality(QWidget):
    detail_requested = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded_row: int | None = None
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        # 品質レベルフィルター
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("品質レベルフィルター"))
        self.quality_filter = QComboBox()
        self.quality_filter.addItems(["すべて", "HIGH", "MEDIUM", "LOW", "UNSET"])
        filter_row.addWidget(self.quality_filter)
        filter_row.addStretch()
        root.addLayout(filter_row)

        self.table = QTableWidget(0, len(_HEADERS))
        self.table.setHorizontalHeaderLabels(_HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(len(_HEADERS) - 1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(len(_HEADERS) - 1, 160)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        root.addWidget(self.table)

        # 品質確認パネル（展開式）
        self.qa_group = QGroupBox("品質確認")
        self.qa_group.setVisible(False)
        qa_layout = QVBoxLayout(self.qa_group)
        qa_layout.setSpacing(theme.MARGIN)

        self.chk_readable = QCheckBox("画像が読み取り可能")
        self.chk_correct = QCheckBox("金額・店名が正確")
        qa_layout.addWidget(self.chk_readable)
        qa_layout.addWidget(self.chk_correct)

        confirm_btn = QPushButton("品質確認を確定")
        qa_layout.addWidget(confirm_btn)

        root.addWidget(self.qa_group)

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

            ops_widget = QWidget()
            ops_layout = QHBoxLayout(ops_widget)
            ops_layout.setContentsMargins(2, 2, 2, 2)
            ops_layout.setSpacing(4)

            detail_btn = QPushButton("詳細")
            detail_btn.clicked.connect(lambda checked, r=row_data: self._on_detail(r))

            qa_btn = QPushButton("品質確認")
            qa_btn.clicked.connect(lambda checked, r=row: self._toggle_qa(r))

            ops_layout.addWidget(detail_btn)
            ops_layout.addWidget(qa_btn)
            self.table.setCellWidget(row, len(_HEADERS) - 1, ops_widget)
        self._apply_row_colors()
        self.table.setSortingEnabled(True)

    def _apply_row_colors(self) -> None:
        """ステータス列の値に応じて行全体の背景色を設定する。"""
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, _STATUS_COL)
            status = status_item.text() if status_item else ""
            color = get_row_color(status)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is not None:
                    item.setBackground(color)

    def _on_detail(self, row_data: tuple) -> None:
        keys = ["receipt_id", "status", "quality_level"]
        vals = [row_data[0], row_data[2], row_data[3]]
        self.detail_requested.emit(dict(zip(keys, vals)))

    def _toggle_qa(self, row: int) -> None:
        if self._expanded_row == row:
            self.qa_group.setVisible(False)
            self._expanded_row = None
        else:
            self.qa_group.setVisible(True)
            self._expanded_row = row
