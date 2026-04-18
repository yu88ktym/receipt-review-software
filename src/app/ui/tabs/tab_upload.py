from __future__ import annotations

import uuid
from pathlib import Path

import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.ui.ui_utils import extract_api_error


class TabUpload(QWidget):
    """画像アップロードタブ。複数の画像ファイルを選択して一括送信する。

    upload_completed シグナルは送信成功時に発火し、一覧タブのリフレッシュをトリガーする。
    """

    upload_completed = Signal()

    def __init__(self, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._api_client = api_client
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

        self.send_btn = QPushButton("選択した画像を送信")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self._on_send)
        root.addWidget(self.send_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.progress_bar)

        self.result_lbl = QLabel()
        self.result_lbl.setWordWrap(True)
        root.addWidget(self.result_lbl)

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

    def _on_send(self) -> None:
        """選択済みファイルを API に一件ずつ送信する。"""
        if not self._selected_files:
            return

        if self._api_client is None:
            QMessageBox.warning(self, "設定エラー", "APIクライアントが設定されていません。")
            return

        total = len(self._selected_files)
        success_count = 0
        fail_count = 0
        fail_details: list[str] = []

        self.send_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.result_lbl.clear()

        for i, file_path in enumerate(self._selected_files, 1):
            try:
                image_bytes = Path(file_path).read_bytes()
                upload_id = uuid.uuid4().hex
                filename = Path(file_path).name
                self._api_client.ingest_image(image_bytes, upload_id, filename)
                success_count += 1
            except requests.HTTPError as exc:
                fail_count += 1
                error_detail = extract_api_error(exc)
                fail_details.append(f"{Path(file_path).name}: {error_detail}")
            except Exception as exc:
                fail_count += 1
                fail_details.append(f"{Path(file_path).name}: {exc}")

            self.progress_bar.setValue(i)

        self.progress_bar.setVisible(False)
        self.select_btn.setEnabled(True)

        # 結果表示（エラー詳細を含む）
        lines = [f"送信完了: 成功 {success_count} 件、失敗 {fail_count} 件"]
        if fail_details:
            lines.append("失敗詳細:")
            lines.extend(f"  - {detail}" for detail in fail_details)
        self.result_lbl.setText("\n".join(lines))

        # 選択状態をリセット
        self._selected_files = []
        self.file_count_lbl.setText("ファイルが選択されていません")

        if success_count > 0:
            self.upload_completed.emit()
