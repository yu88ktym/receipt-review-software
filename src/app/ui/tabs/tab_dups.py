from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QGroupBox, QFormLayout,
    QFrame, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.settings_io import load_settings
from app.ui.widgets.tile_view import DupsTileView

_HEADERS = ["レシートID", "重複元レシートID", "詳細", "重複解除"]

_DUMMY_DUPS = [
    ("R-0002", "R-0001"),
    ("R-0004", "R-0001"),
]


class TabDups(QWidget):
    view_mode_changed = Signal(bool)  # True = タイル表示, False = テキスト表示

    def __init__(self, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._api_client = api_client
        self._tile_mode = False
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        # ツールバー（切り替えボタン）
        toolbar = QHBoxLayout()
        dup_label = QLabel("重複候補一覧")
        dup_label.setProperty("heading", "true")
        toolbar.addWidget(dup_label)
        toolbar.addStretch()
        self.view_toggle_btn = QPushButton("サムネイル表示")
        self.view_toggle_btn.setProperty("flat", "true")
        self.view_toggle_btn.clicked.connect(self._toggle_view)
        toolbar.addWidget(self.view_toggle_btn)
        root.addLayout(toolbar)

        # スタック（テキスト / サムネイル）
        self._stacked = QStackedWidget()

        self.table = QTableWidget(0, len(_HEADERS))
        self.table.setHorizontalHeaderLabels(_HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 70)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self._stacked.addWidget(self.table)

        self.dup_tile_view = DupsTileView()
        self._stacked.addWidget(self.dup_tile_view)

        root.addWidget(self._stacked)

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
        for row_data in _DUMMY_DUPS:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            detail_btn = QPushButton("詳細")
            self.table.setCellWidget(row, 2, detail_btn)

            release_btn = QPushButton("解除")
            release_btn.setProperty("flat", "true")
            self.table.setCellWidget(row, 3, release_btn)
        self.table.setSortingEnabled(True)

    def _populate_tiles(self) -> None:
        """DupsTileView に親子グループを渡す。"""
        # 親IDごとに子をグルーピング
        parent_children: dict[str, list[str]] = {}
        for child_id, parent_id in _DUMMY_DUPS:
            parent_children.setdefault(parent_id, []).append(child_id)

        groups = [
            {
                "parent": {"image_id": pid, "created_at": "—", "status": ""},
                "children": [
                    {"image_id": cid, "created_at": "—", "status": ""}
                    for cid in cids
                ],
            }
            for pid, cids in parent_children.items()
        ]

        settings = load_settings()
        tile_w = settings.get("thumbnail_tile_width", 160)
        tile_h = settings.get("thumbnail_tile_height", 200)
        self.dup_tile_view.set_groups(groups, self._api_client, tile_w, tile_h)


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
