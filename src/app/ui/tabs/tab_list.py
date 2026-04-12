from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QLineEdit, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.status_colors import apply_row_colors
from app.models.types import ImageMeta
from app.ui.ui_utils import image_meta_to_row

_HEADERS = ["レシートID", "アップロード日", "購入日", "合計金額", "店名", "支払方法", "ステータス/重要", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 6
_PAGE_SIZE = 50

_STATUS_OPTIONS = [
    ("すべて", None),
    ("INGESTED", "INGESTED"),
    ("OCR_DONE", "OCR_DONE"),
    ("FINAL_UPDATED", "FINAL_UPDATED"),
    ("DROPPED", "DROPPED"),
]


class TabList(QWidget):
    """一覧タブ。ReceiptsService を通じて取得した実データをテーブルに表示する。"""

    detail_requested = Signal(dict)

    def __init__(self, service=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._page = 1
        self._all_items: list[ImageMeta] = []
        self._build_ui()
        if self._service is not None:
            self.load_data()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        # フィルタ／更新バー
        filter_bar = QHBoxLayout()

        status_lbl = QLabel("ステータス：")
        self.status_combo = QComboBox()
        for label, _ in _STATUS_OPTIONS:
            self.status_combo.addItem(label)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)

        keyword_lbl = QLabel("検索：")
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("ID / 店名")
        self.keyword_edit.setFixedWidth(200)
        self.keyword_edit.textChanged.connect(self._on_filter_changed)

        self.refresh_btn = QPushButton("更新")
        self.refresh_btn.clicked.connect(self._on_refresh)

        filter_bar.addWidget(status_lbl)
        filter_bar.addWidget(self.status_combo)
        filter_bar.addSpacing(theme.MARGIN)
        filter_bar.addWidget(keyword_lbl)
        filter_bar.addWidget(self.keyword_edit)
        filter_bar.addStretch()
        filter_bar.addWidget(self.refresh_btn)
        root.addLayout(filter_bar)

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

    # ------------------------------------------------------------------
    # データ取得
    # ------------------------------------------------------------------

    def load_data(self, force_refresh: bool = False) -> None:
        """サービス層からデータを取得してテーブルを更新する。"""
        if self._service is None:
            return
        status = _STATUS_OPTIONS[self.status_combo.currentIndex()][1]
        keyword = self.keyword_edit.text().strip() or None
        try:
            self._all_items = self._service.fetch_list(
                status=status,
                keyword=keyword,
                force_refresh=force_refresh,
            )
        except Exception as exc:
            QMessageBox.warning(self, "通信エラー", f"データの取得に失敗しました。\n{exc}")
            return
        self._page = 1
        self._populate()

    def refresh(self) -> None:
        """一覧を強制再取得する（外部からも呼び出し可能）。"""
        if self._service is not None:
            self._service.invalidate_cache()
        self.load_data(force_refresh=True)

    def _on_filter_changed(self) -> None:
        """フィルタ条件（ステータス/キーワード）変更時に一覧を再読み込みする。"""
        self._page = 1
        self.load_data()

    def _on_refresh(self) -> None:
        """更新ボタン押下時にキャッシュをクリアして再読み込みする。"""
        self.refresh()

    # ------------------------------------------------------------------
    # 表示更新
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        """現在ページのデータをテーブルに描画する。"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        page_items = self._current_page_items()
        for item in page_items:
            row_data = image_meta_to_row(item)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, cell)
            detail_btn = QPushButton("詳細")
            detail_btn.clicked.connect(lambda checked, d=item: self._on_detail(d))
            self.table.setCellWidget(row, len(_HEADERS) - 1, detail_btn)
        apply_row_colors(self.table, _STATUS_COL)
        self.table.setSortingEnabled(True)
        self._update_pager()

    def _current_page_items(self) -> list[ImageMeta]:
        """現在のページに表示するアイテムのサブリストを返す。"""
        start = (self._page - 1) * _PAGE_SIZE
        if start >= len(self._all_items):
            return []
        end = min(start + _PAGE_SIZE, len(self._all_items))
        return self._all_items[start:end]

    def _on_detail(self, item: ImageMeta) -> None:
        self.detail_requested.emit(dict(item))

    def _prev_page(self) -> None:
        if self._page > 1:
            self._page -= 1
            self._populate()

    def _next_page(self) -> None:
        if self._page < self._num_pages:
            self._page += 1
            self._populate()

    def _update_pager(self) -> None:
        total = len(self._all_items)
        self._num_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
        self.page_label.setText(f"ページ {self._page} / {self._num_pages}")
        self.prev_btn.setEnabled(self._page > 1)
        self.next_btn.setEnabled(self._page < self._num_pages)
