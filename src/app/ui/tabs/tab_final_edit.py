from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDateEdit, QComboBox, QHeaderView,
    QFrame, QFormLayout, QGroupBox,
)
from PySide6.QtCore import Qt, QDate
from app.config import theme
from app.config.status_colors import get_row_color

_HEADERS = ["レシートID", "アップロード日", "購入日", "合計金額", "店名", "支払方法", "ステータス", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 6

_DUMMY_ROWS = [
    ("R-0001", "2024-01-15", "2024-01-14", "3200", "コンビニA", "現金", "FINAL_UPDATED"),
    ("R-0002", "2024-01-16", "2024-01-15", "1500", "スーパーB", "クレジット", "REVIEWED"),
    ("R-0003", "2024-01-17", "2024-01-16", "8400", "レストランC", "電子マネー", "PENDING"),
]

_STORE_CANDIDATES = ["コンビニA", "スーパーB", "レストランC", "カフェD", "百貨店E"]
_PAYMENT_CANDIDATES = ["現金", "クレジット", "電子マネー", "QRコード"]


class TabFinalEdit(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        root.addWidget(self.table)

        # 入力フォーム
        form_group = QGroupBox("確定値を編集")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(theme.MARGIN)

        self.edit_purchase_date = QDateEdit()
        self.edit_purchase_date.setDisplayFormat("yyyy-MM-dd")
        self.edit_purchase_date.setCalendarPopup(True)
        self.edit_purchase_date.setDate(QDate.currentDate())
        form_layout.addRow("購入日", self.edit_purchase_date)

        self.edit_total = QLineEdit()
        self.edit_total.setPlaceholderText("合計金額（数値）")
        form_layout.addRow("合計金額", self.edit_total)

        store_row = QHBoxLayout()
        self.edit_store = QLineEdit()
        self.edit_store.setPlaceholderText("店名")
        self.store_suggest = QComboBox()
        self.store_suggest.addItem("候補から選択")
        self.store_suggest.addItems(_STORE_CANDIDATES)
        self.store_suggest.currentTextChanged.connect(
            lambda t: self.edit_store.setText(t) if t != "候補から選択" else None
        )
        store_row.addWidget(self.edit_store)
        store_row.addWidget(self.store_suggest)
        form_layout.addRow("店名", store_row)

        payment_row = QHBoxLayout()
        self.edit_payment = QLineEdit()
        self.edit_payment.setPlaceholderText("支払方法")
        self.payment_suggest = QComboBox()
        self.payment_suggest.addItem("候補から選択")
        self.payment_suggest.addItems(_PAYMENT_CANDIDATES)
        self.payment_suggest.currentTextChanged.connect(
            lambda t: self.edit_payment.setText(t) if t != "候補から選択" else None
        )
        payment_row.addWidget(self.edit_payment)
        payment_row.addWidget(self.payment_suggest)
        form_layout.addRow("支払方法", payment_row)

        confirm_btn = QPushButton("確定")
        form_layout.addRow("", confirm_btn)

        root.addWidget(form_group)

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
            btn = QPushButton("選択")
            btn.clicked.connect(lambda checked, r=row: self.table.selectRow(r))
            self.table.setCellWidget(row, len(_HEADERS) - 1, btn)
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

    def _on_selection_changed(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return
        row = self.table.currentRow()
        row_data = _DUMMY_ROWS[row] if row < len(_DUMMY_ROWS) else None
        if row_data is None:
            return
        date = QDate.fromString(row_data[2], "yyyy-MM-dd")
        if date.isValid():
            self.edit_purchase_date.setDate(date)
        self.edit_total.setText(row_data[3])
        self.edit_store.setText(row_data[4])
        self.edit_payment.setText(row_data[5])
