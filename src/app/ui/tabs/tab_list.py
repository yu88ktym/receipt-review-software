from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.status_colors import apply_row_colors
from app.models.types import ImageMeta
from app.ui.ui_utils import image_meta_to_row

_HEADERS = ["レシートID", "アップロード日", "購入日", "合計金額", "店名", "支払方法", "ステータス/重要", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 6

_DEFAULT_PAGE_SIZE = 50


class TabList(QWidget):
    """一覧タブ。ReceiptsService を通じて取得した実データをテーブルに表示する。"""

    detail_requested = Signal(dict)

    def __init__(self, service=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._page = 1
        self._page_size = _DEFAULT_PAGE_SIZE
        self._all_items: list[ImageMeta] = []
        self._current_filters: dict = {}
        self._build_ui()
        if self._service is not None:
            self.load_data()

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

    # ------------------------------------------------------------------
    # 公開インターフェース
    # ------------------------------------------------------------------

    def load_data(self, filters: dict | None = None) -> None:
        """フィルタ条件でサービスからデータを取得してテーブルを再描画する。"""
        if filters is not None:
            self._current_filters = filters
            self._page_size = filters.get("page_size", _DEFAULT_PAGE_SIZE)

        if self._service is None:
            return

        try:
            self._all_items = self._service.fetch_list(
                status=self._current_filters.get("status"),
                quality_level=self._current_filters.get("quality_level"),
                keyword=self._current_filters.get("keyword"),
                since=self._current_filters.get("since"),
                until=self._current_filters.get("until"),
                exclude_duplicates=self._current_filters.get("exclude_duplicates", False),
            )
        except Exception as exc:
            QMessageBox.warning(self, "通信エラー", f"データの取得に失敗しました。\n{exc}")
            return

        self._page = 1
        self._populate()

    def refresh(self) -> None:
        """キャッシュをクリアしてデータを再取得する。"""
        if self._service is not None:
            self._service.invalidate_cache()
        self.load_data()

    # ------------------------------------------------------------------
    # 内部処理
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
            # クロージャにより item の参照を確定させる
            detail_btn.clicked.connect(lambda checked, d=item: self._on_detail(d))
            self.table.setCellWidget(row, len(_HEADERS) - 1, detail_btn)

        apply_row_colors(self.table, _STATUS_COL)
        self.table.setSortingEnabled(True)
        self._update_pager()

    def _current_page_items(self) -> list[ImageMeta]:
        """現在のページに表示するアイテムのサブリストを返す。
        ページサイズやフィルタ条件の変更に応じて、_all_items から適切な範囲を切り出す。
        args:
            なし（必要に応じて self._page や self._page_size、self._all_items を参照する）
        returns:
            list[ImageMeta]: 現在のページに表示するアイテムのリスト
        start, end: ページ番号とページサイズに基づいて、_all_items から切り出す範囲を計算する。
        例: ページサイズが 50 のとき、ページ 1 はインデックス 0-49、ページ 2 はインデックス 50-99、ページ 3 はインデックス 100-149 となる。
        """
        start = (self._page - 1) * self._page_size
        end = start + self._page_size if len(self._all_items) >= start + self._page_size else len(self._all_items) - 1
        print(start, end, self._page_size, len(self._all_items), type(self._all_items))
        return self._all_items[start:end]

    def _total_pages(self) -> int:
        if not self._all_items:
            return 1
        return math.ceil(len(self._all_items) / self._page_size)

    def _on_detail(self, item: ImageMeta) -> None:
        self.detail_requested.emit(dict(item))

    def _prev_page(self) -> None:
        if self._page > 1:
            self._page -= 1
            self._populate()

    def _next_page(self) -> None:
        if self._page < self._total_pages():
            self._page += 1
            self._populate()

    def _update_pager(self) -> None:
        total = self._total_pages()
        self.page_label.setText(f"ページ {self._page} / {total}")
        self.prev_btn.setEnabled(self._page > 1)
        self.next_btn.setEnabled(self._page < total)
