from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.status_colors import apply_row_colors
from app.config.settings_io import load_settings
from app.models.types import ImageMeta
from app.ui.ui_utils import image_meta_to_row
from app.ui.widgets.tile_view import TileView

_HEADERS = ["レシートID", "アップロード日", "購入日", "合計金額", "店名", "支払方法", "ステータス/重要", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 6
_PAGE_SIZE = 50

_FETCH_FILTER_KEYS = ("status", "quality_level", "keyword", "since", "until", "exclude_duplicates")


class TabList(QWidget):
    """一覧タブ。ReceiptsService を通じて取得した実データをテーブルに表示する。

    テキスト表示（テーブル）とサムネイル表示（タイルビュー）を切り替え可能。
    """

    detail_requested = Signal(dict)
    view_mode_changed = Signal(bool)  # True = タイル表示, False = テキスト表示

    def __init__(self, service=None, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._api_client = api_client
        self._page = 1
        self._all_items: list[ImageMeta] = []
        self._filters: dict = {}
        self._tile_mode = False
        self._build_ui()
        if self._service is not None:
            self.load_data()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        # ツールバー（切り替えボタン + 更新ボタン）
        toolbar = QHBoxLayout()

        self.view_toggle_btn = QPushButton("サムネイル表示")
        self.view_toggle_btn.setProperty("flat", "true")
        self.view_toggle_btn.clicked.connect(self._toggle_view)
        toolbar.addWidget(self.view_toggle_btn)

        toolbar.addStretch()

        self.refresh_btn = QPushButton("更新")
        self.refresh_btn.clicked.connect(self._on_refresh)
        toolbar.addWidget(self.refresh_btn)

        root.addLayout(toolbar)

        # スタック（テキスト表示 / サムネイル表示）
        self._stacked = QStackedWidget()

        # インデックス 0: テーブル
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
        self._stacked.addWidget(self.table)

        # インデックス 1: タイルビュー
        self.tile_view = TileView()
        self.tile_view.item_clicked.connect(lambda d: self.detail_requested.emit(d))
        self._stacked.addWidget(self.tile_view)

        root.addWidget(self._stacked)

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
    # 表示切り替え
    # ------------------------------------------------------------------

    def _toggle_view(self) -> None:
        self.set_tile_mode(not self._tile_mode)
        self.view_mode_changed.emit(self._tile_mode)

    def set_tile_mode(self, tile_mode: bool) -> None:
        """タイル表示モードを直接指定する（シグナル発火なし）。タブ間同期に使用。"""
        if self._tile_mode == tile_mode:
            return
        self._tile_mode = tile_mode
        if tile_mode:
            self._stacked.setCurrentIndex(1)
            self.view_toggle_btn.setText("テキスト表示")
            self._populate_tiles(self._current_page_items())
        else:
            self._stacked.setCurrentIndex(0)
            self.view_toggle_btn.setText("サムネイル表示")

    # ------------------------------------------------------------------
    # データ取得
    # ------------------------------------------------------------------

    def load_data(self, filters: dict | None = None, *, force_refresh: bool = False) -> None:
        """サービス層からデータを取得してテーブルを更新する。

        filters にサイドバーからのフィルタ辞書を渡すと保存して次回以降も使用する。
        """
        if filters is not None:
            self._filters = filters
        if self._service is None:
            return
        fetch_params = {k: v for k, v in self._filters.items() if k in _FETCH_FILTER_KEYS}
        try:
            self._all_items = self._service.fetch_list(
                force_refresh=force_refresh,
                **fetch_params,
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

    def _on_refresh(self) -> None:
        """更新ボタン押下時にキャッシュをクリアして再読み込みする。"""
        self.refresh()

    # ------------------------------------------------------------------
    # 表示更新
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        """現在ページのデータをアクティブなビューに描画する。"""
        page_items = self._current_page_items()
        self._populate_table(page_items)
        if self._tile_mode:
            self._populate_tiles(page_items)
        self._update_pager()

    def _populate_table(self, page_items: list[ImageMeta]) -> None:
        """テーブルビューを更新する。"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

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

    def _populate_tiles(self, page_items: list[ImageMeta]) -> None:
        """タイルビューを更新する。"""
        tile_data = [
            {
                "image_id": meta.get("image_id", "—"),
                "created_at": meta.get("created_at", "—"),
                "status": meta.get("status", ""),
            }
            for meta in page_items
        ]
        settings = load_settings()
        tile_w = settings.get("thumbnail_tile_width", 160)
        tile_h = settings.get("thumbnail_tile_height", 200)
        self.tile_view.set_items(tile_data, self._api_client, tile_w, tile_h)

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
