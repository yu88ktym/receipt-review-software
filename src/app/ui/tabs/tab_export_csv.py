from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QFileDialog,
)
from PySide6.QtCore import Qt
from app.config import theme

_PREVIEW_HEADERS = ["レシートID", "購入日", "合計金額", "店名", "支払方法", "ステータス"]

_DUMMY_ROWS = [
    ("R-0001", "2024-01-14", "3200", "コンビニA", "現金", "FINAL_UPDATED"),
    ("R-0005", "2024-01-18", "12000", "百貨店E", "クレジット", "FINAL_UPDATED"),
]


class TabExportCsv(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._populate_preview()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        desc_lbl = QLabel("CSVエクスポート（FINAL_UPDATEDのみ・重複除外・全件）")
        desc_lbl.setProperty("heading", "true")
        root.addWidget(desc_lbl)

        col_desc = QLabel(
            "出力列: レシートID / 購入日 / 合計金額 / 店名 / 支払方法 / ステータス"
        )
        col_desc.setWordWrap(True)
        root.addWidget(col_desc)

        create_btn = QPushButton("CSVを作成する")
        create_btn.clicked.connect(self._on_create)
        root.addWidget(create_btn)

        preview_lbl = QLabel("プレビュー")
        root.addWidget(preview_lbl)

        self.preview_table = QTableWidget(0, len(_PREVIEW_HEADERS))
        self.preview_table.setHorizontalHeaderLabels(_PREVIEW_HEADERS)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        root.addWidget(self.preview_table)

        self.download_btn = QPushButton("CSVをダウンロード")
        self.download_btn.clicked.connect(self._on_download)
        root.addWidget(self.download_btn)

    def _populate_preview(self) -> None:
        self.preview_table.setRowCount(0)
        for row_data in _DUMMY_ROWS:
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_table.setItem(row, col, item)

    def _on_create(self) -> None:
        self._populate_preview()

    def _on_download(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "CSVを保存", "export.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        headers = _PREVIEW_HEADERS
        lines = [",".join(headers)]
        for row in range(self.preview_table.rowCount()):
            cols = [
                (self.preview_table.item(row, col) or QTableWidgetItem("")).text()
                for col in range(self.preview_table.columnCount())
            ]
            lines.append(",".join(cols))
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(lines))
