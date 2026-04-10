from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
)
from PySide6.QtCore import Qt
from app.config import theme


class TabUpload(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_files: list[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        select_row = QHBoxLayout()
        self.select_btn = QPushButton("ファイルを選択")
        self.select_btn.setProperty("flat", "true")
        self.select_btn.clicked.connect(self._on_select)
        self.file_count_lbl = QLabel("ファイルが選択されていません")
        self.file_count_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        select_row.addWidget(self.select_btn)
        select_row.addWidget(self.file_count_lbl)
        select_row.addStretch()
        root.addLayout(select_row)

        self.send_btn = QPushButton("送信")
        self.send_btn.setEnabled(False)
        root.addWidget(self.send_btn)

        root.addSpacing(theme.MARGIN * 2)

        history_lbl = QLabel("送信履歴")
        history_lbl.setProperty("heading", "true")
        root.addWidget(history_lbl)

        root.addStretch()

    def _on_select(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "画像を選択", "", "画像ファイル (*.jpg *.jpeg *.png *.webp *.heic)"
        )
        self._selected_files = files
        if files:
            self.file_count_lbl.setText(f"{len(files)} ファイル選択済み")
            self.send_btn.setEnabled(True)
        else:
            self.file_count_lbl.setText("ファイルが選択されていません")
            self.send_btn.setEnabled(False)
