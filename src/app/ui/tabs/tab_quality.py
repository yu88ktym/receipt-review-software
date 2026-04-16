from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QCheckBox, QHeaderView, QFrame,
    QGroupBox, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.status_colors import apply_row_colors
from app.config.settings_io import load_settings
from app.ui.widgets.tile_view import TileView

_HEADERS = ["画像ID", "サムネイル", "ステータス", "品質", "重複", "ゴミ箱", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 2

_DUMMY_ROWS = [
    ("IMG-001", "—", "INGESTED", "NO_PROBLEM", "なし", "—"),
    ("IMG-002", "—", "OCR_DONE", "LOW", "あり", "—"),
    ("IMG-003", "—", "FINAL_UPDATED", "OCR_LOW", "なし", "—"),
]

# _DUMMY_ROWS のカラムインデックス
_COL_IMAGE_ID = 0
_COL_UPLOAD_DATE = 1
_COL_STATUS = 2


class TabQuality(QWidget):
    detail_requested = Signal(dict)
    view_mode_changed = Signal(bool)  # True = タイル表示, False = テキスト表示

    def __init__(self, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._api_client = api_client
        self._expanded_row: int | None = None
        self._tile_mode = False
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        # 品質レベルフィルター + 切り替えボタン
        filter_row = QHBoxLayout()
        self.view_toggle_btn = QPushButton("サムネイル表示")
        self.view_toggle_btn.setProperty("flat", "true")
        self.view_toggle_btn.clicked.connect(self._toggle_view)
        filter_row.addWidget(self.view_toggle_btn)

        filter_row.addWidget(QLabel("品質レベルフィルター"))
        self.quality_filter = QComboBox()
        self.quality_filter.addItems(["すべて", "UNKNOWN", "NO_PROBLEM", "OCR_LOW", "LOW"])
        filter_row.addWidget(self.quality_filter)
        filter_row.addStretch()
        root.addLayout(filter_row)

        # スタック（テキスト / サムネイル）
        self._stacked = QStackedWidget()

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
        self._stacked.addWidget(self.table)

        self.tile_view = TileView()
        self._stacked.addWidget(self.tile_view)

        root.addWidget(self._stacked)

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
            self._populate_tiles()
        else:
            self._stacked.setCurrentIndex(0)
            self.view_toggle_btn.setText("サムネイル表示")

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
        apply_row_colors(self.table, _STATUS_COL)

    def _populate_tiles(self) -> None:
        """タイルビューをダミーデータで更新する。"""
        tile_data = [
            {"image_id": row[_COL_IMAGE_ID], "created_at": row[_COL_UPLOAD_DATE], "status": row[_COL_STATUS]}
            for row in _DUMMY_ROWS
        ]
        settings = load_settings()
        tile_w = settings.get("thumbnail_tile_width", 160)
        tile_h = settings.get("thumbnail_tile_height", 200)
        self.tile_view.set_items(tile_data, self._api_client, tile_w, tile_h)

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
