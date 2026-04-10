from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QGroupBox, QFormLayout,
    QFrame,
)
from PySide6.QtCore import Qt
from app.config import theme

_HEADERS = ["レシートID", "重複元レシートID", "関係識別コード", "詳細", "解除"]

_DUMMY_DUPS = [
    ("R-0002", "R-0001", "EXACT"),
    ("R-0004", "R-0001", "SIMILAR"),
]


class TabDups(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        dup_label = QLabel("重複候補一覧")
        dup_label.setProperty("heading", "true")
        root.addWidget(dup_label)

        self.table = QTableWidget(0, len(_HEADERS))
        self.table.setHorizontalHeaderLabels(_HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 70)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        root.addWidget(_divider())

        # 重複設定フォーム
        set_group = QGroupBox("重複設定")
        set_form = QFormLayout(set_group)
        set_form.setSpacing(theme.MARGIN)

        self.dup_target_edit = QLineEdit()
        self.dup_target_edit.setPlaceholderText("対象画像ID")
        set_form.addRow("対象画像ID", self.dup_target_edit)

        self.dup_parent_edit = QLineEdit()
        self.dup_parent_edit.setPlaceholderText("親画像ID")
        set_form.addRow("親画像ID", self.dup_parent_edit)

        set_btn = QPushButton("重複を設定")
        set_form.addRow("", set_btn)

        root.addWidget(set_group)

        # 親子逆転フォーム
        swap_group = QGroupBox("親子逆転")
        swap_form = QFormLayout(swap_group)
        swap_form.setSpacing(theme.MARGIN)

        self.old_parent_edit = QLineEdit()
        self.old_parent_edit.setPlaceholderText("旧親画像ID")
        swap_form.addRow("旧親画像ID", self.old_parent_edit)

        self.new_parent_edit = QLineEdit()
        self.new_parent_edit.setPlaceholderText("新親画像ID")
        swap_form.addRow("新親画像ID", self.new_parent_edit)

        swap_btn = QPushButton("親子を逆転")
        swap_form.addRow("", swap_btn)

        root.addWidget(swap_group)

    def _populate(self) -> None:
        self.table.setRowCount(0)
        for row_data in _DUMMY_DUPS:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            detail_btn = QPushButton("詳細")
            self.table.setCellWidget(row, 3, detail_btn)

            release_btn = QPushButton("解除")
            release_btn.setProperty("flat", "true")
            self.table.setCellWidget(row, 4, release_btn)


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
