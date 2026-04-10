from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QGroupBox, QFrame,
)
from PySide6.QtCore import Qt
from app.config import theme

_STORE_HEADERS = ["表記ゆれ", "正規化後", "削除"]
_PAYMENT_HEADERS = ["表記ゆれ", "正規化後", "削除"]


def _remove_row_by_widget(table: QTableWidget, widget: QPushButton, col: int) -> None:
    """ボタン参照から現在の行インデックスを動的に解決して削除する。"""
    for row in range(table.rowCount()):
        if table.cellWidget(row, col) is widget:
            table.removeRow(row)
            return

_DUMMY_STORE_MAP = [
    ("コンビニA店", "コンビニA"),
    ("コンビニＡ", "コンビニA"),
    ("スーパーＢ", "スーパーB"),
]
_DUMMY_PAYMENT_MAP = [
    ("クレジットカード", "クレジット"),
    ("電子マネー（Suica）", "電子マネー"),
]


class TabAutocomplete(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        root.addWidget(self._build_section("店名", _STORE_HEADERS, _DUMMY_STORE_MAP))
        root.addWidget(_divider())
        root.addWidget(self._build_section("支払方法", _PAYMENT_HEADERS, _DUMMY_PAYMENT_MAP))
        root.addStretch()

    def _build_section(self, title: str, headers: list[str], rows: list[tuple]) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setSpacing(theme.MARGIN)

        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(len(headers) - 1, 70)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)

        del_col = len(headers) - 1
        for row_data in rows:
            row = table.rowCount()
            table.insertRow(row)
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col, item)
            del_btn = QPushButton("削除")
            del_btn.setProperty("danger", "true")
            del_btn.clicked.connect(
                lambda checked, b=del_btn, t=table, c=del_col: _remove_row_by_widget(t, b, c)
            )
            table.setCellWidget(row, del_col, del_btn)

        layout.addWidget(table)

        # 追加フォーム
        add_row = QHBoxLayout()
        variant_edit = QLineEdit()
        variant_edit.setPlaceholderText("表記ゆれ")
        normalized_edit = QLineEdit()
        normalized_edit.setPlaceholderText("正規化後")
        add_btn = QPushButton("登録")

        def _add(t=table, v=variant_edit, n=normalized_edit):
            if not v.text().strip() or not n.text().strip():
                return
            r = t.rowCount()
            t.insertRow(r)
            for c, val in enumerate([v.text().strip(), n.text().strip()]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                t.setItem(r, c, item)
            btn = QPushButton("削除")
            btn.setProperty("danger", "true")
            btn.clicked.connect(
                lambda checked, b=btn, tbl=t, c=len(headers) - 1: _remove_row_by_widget(tbl, b, c)
            )
            t.setCellWidget(r, len(headers) - 1, btn)
            v.clear()
            n.clear()

        add_btn.clicked.connect(_add)

        add_row.addWidget(variant_edit)
        add_row.addWidget(normalized_edit)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        return group


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
