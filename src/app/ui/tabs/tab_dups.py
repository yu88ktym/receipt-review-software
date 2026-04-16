from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QGroupBox, QFormLayout,
    QFrame, QStackedWidget, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from app.config import theme
from app.config.settings_io import load_settings
from app.models.types import ImageMeta
from app.ui.widgets.tile_view import DupsTileView

_HEADERS = ["レシートID", "重複元レシートID", "詳細", "重複解除"]


class TabDups(QWidget):
    detail_requested = Signal(dict)
    list_refresh_needed = Signal()
    view_mode_changed = Signal(bool)  # True = タイル表示, False = テキスト表示

    def __init__(self, service=None, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._api_client = api_client
        self._tile_mode = False
        self._all_items: list[ImageMeta] = []
        # 親→子リスト / 子→親 マッピング（ボタン操作判定用）
        self._parent_children: dict[str, list[str]] = {}
        self._child_parent: dict[str, str] = {}
        self._build_ui()
        self.load_data()

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
        self.dup_tile_view.tile_clicked.connect(self._on_tile_clicked)
        self.dup_tile_view.tile_left_double_clicked.connect(self._on_tile_left_double_clicked)
        self.dup_tile_view.tile_right_double_clicked.connect(self._on_tile_right_double_clicked)
        self._stacked.addWidget(self.dup_tile_view)

        root.addWidget(self._stacked)

        root.addWidget(_divider())

        # 操作フォームを横並びに配置
        forms_row = QHBoxLayout()
        forms_row.setSpacing(theme.MARGIN)

        # 重複設定フォーム
        set_group = QGroupBox("重複設定")
        set_form = QFormLayout(set_group)
        set_form.setSpacing(theme.MARGIN)

        self.dup_target_edit = QLineEdit()
        self.dup_target_edit.setPlaceholderText("例: R-0001")
        set_form.addRow("子画像ID", self.dup_target_edit)

        self.dup_parent_edit = QLineEdit()
        self.dup_parent_edit.setPlaceholderText("親画像ID")
        set_form.addRow("親画像ID", self.dup_parent_edit)

        set_btn = QPushButton("重複を設定")
        set_btn.clicked.connect(self._on_set_duplicate)
        set_form.addRow("", set_btn)

        self.set_msg_label = QLabel()
        self.set_msg_label.setWordWrap(True)
        set_form.addRow("", self.set_msg_label)

        forms_row.addWidget(set_group)

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
        swap_btn.clicked.connect(self._on_reverse_parent)
        swap_form.addRow("", swap_btn)

        self.swap_msg_label = QLabel()
        self.swap_msg_label.setWordWrap(True)
        swap_form.addRow("", self.swap_msg_label)

        forms_row.addWidget(swap_group)

        # 親子解除フォーム
        unset_group = QGroupBox("親子解除")
        unset_form = QFormLayout(unset_group)
        unset_form.setSpacing(theme.MARGIN)

        self.unset_id_edit = QLineEdit()
        self.unset_id_edit.setPlaceholderText("画像ID（親または子）")
        unset_form.addRow("画像ID", self.unset_id_edit)

        unset_btn = QPushButton("親子を解除")
        unset_btn.setProperty("danger", "true")
        unset_btn.clicked.connect(self._on_unset_duplicate)
        unset_form.addRow("", unset_btn)

        self.unset_msg_label = QLabel()
        self.unset_msg_label.setWordWrap(True)
        unset_form.addRow("", self.unset_msg_label)

        forms_row.addWidget(unset_group)

        root.addLayout(forms_row)

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

    # ------------------------------------------------------------------
    # データ取得
    # ------------------------------------------------------------------

    def load_data(self) -> None:
        """全レシートを取得して親子マッピングを構築する。"""
        if self._service is not None:
            try:
                self._all_items = self._service.fetch_list(force_refresh=True)
            except Exception as exc:
                self._show_message(self.set_msg_label, f"データ取得エラー: {exc}", error=True)
                return
        elif self._api_client is not None:
            try:
                self._all_items = self._api_client.list_receipts()
            except Exception as exc:
                self._show_message(self.set_msg_label, f"データ取得エラー: {exc}", error=True)
                return
        self._build_maps()
        self._populate()

    def refresh(self) -> None:
        """一覧を強制再取得する。"""
        if self._service is not None:
            self._service.invalidate_cache()
        self.load_data()

    def _build_maps(self) -> None:
        """_all_items から親子マッピングを再構築する。"""
        self._parent_children = {}
        self._child_parent = {}
        for item in self._all_items:
            dup_of = item.get("duplicate_of")
            if dup_of:
                child_id = str(item["image_id"])
                parent_id = str(dup_of)
                self._child_parent[child_id] = parent_id
                self._parent_children.setdefault(parent_id, []).append(child_id)

    # ------------------------------------------------------------------
    # 表示更新
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        self._populate_table()
        if self._tile_mode:
            self._populate_tiles()

    def _populate_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        item_map = {str(i["image_id"]): i for i in self._all_items}

        for child_id, parent_id in self._child_parent.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, _centered_item(child_id))
            self.table.setItem(row, 1, _centered_item(parent_id))

            detail_btn = QPushButton("詳細")
            child_item = item_map.get(child_id, {"image_id": child_id})
            detail_btn.clicked.connect(
                lambda checked, d=child_item: self.detail_requested.emit(dict(d))
            )
            self.table.setCellWidget(row, 2, detail_btn)

            release_btn = QPushButton("解除")
            release_btn.setProperty("flat", "true")
            release_btn.clicked.connect(
                lambda checked, cid=child_id, pid=parent_id: self._unset_child(cid, pid)
            )
            self.table.setCellWidget(row, 3, release_btn)

        self.table.setSortingEnabled(True)

    def _populate_tiles(self) -> None:
        """DupsTileView に親子グループを渡す。"""
        item_map = {str(i["image_id"]): i for i in self._all_items}
        groups = []
        for parent_id, child_ids in self._parent_children.items():
            parent_item = item_map.get(parent_id, {"image_id": parent_id, "created_at": "—", "status": ""})
            children = [
                item_map.get(cid, {"image_id": cid, "created_at": "—", "status": ""})
                for cid in child_ids
            ]
            groups.append({"parent": parent_item, "children": children})

        settings = load_settings()
        tile_w = settings.get("thumbnail_tile_width", 160)
        tile_h = settings.get("thumbnail_tile_height", 200)
        self.dup_tile_view.set_groups(groups, self._api_client, tile_w, tile_h)

    # ------------------------------------------------------------------
    # タイルクリックハンドラ
    # ------------------------------------------------------------------

    def _on_tile_clicked(self, data: dict) -> None:
        """シングルクリック: 詳細表示。"""
        self.detail_requested.emit(data)

    def _on_tile_left_double_clicked(self, data: dict) -> None:
        """左ダブルクリック: 詳細表示 + 子画像IDをフォームに設定。"""
        image_id = str(data.get("image_id") or "")
        self.dup_target_edit.setText(image_id)
        self.new_parent_edit.setText(image_id)
        self.unset_id_edit.setText(image_id)
        self.detail_requested.emit(data)

    def _on_tile_right_double_clicked(self, data: dict) -> None:
        """右ダブルクリック: 詳細表示 + 親画像IDをフォームに設定。"""
        image_id = str(data.get("image_id") or "")
        self.dup_parent_edit.setText(image_id)
        self.old_parent_edit.setText(image_id)
        self.unset_id_edit.setText(image_id)
        self.detail_requested.emit(data)

    # ------------------------------------------------------------------
    # ボタン操作
    # ------------------------------------------------------------------

    def _on_set_duplicate(self) -> None:
        """重複を設定ボタン押下。"""
        child_id = self.dup_target_edit.text().strip()
        parent_id = self.dup_parent_edit.text().strip()
        if not child_id or not parent_id:
            self._show_message(self.set_msg_label, "子画像IDと親画像IDを入力してください。", error=True)
            return
        if self._api_client is None:
            return
        try:
            self._api_client.set_duplicate(child_id, parent_id)
        except Exception as exc:
            self._show_message(self.set_msg_label, f"設定エラー: {exc}", error=True)
            return
        self._show_message(self.set_msg_label, "重複を設定しました。", error=False)
        self.list_refresh_needed.emit()
        self.refresh()

    def _on_reverse_parent(self) -> None:
        """親子を逆転ボタン押下。"""
        old_parent = self.old_parent_edit.text().strip()
        new_parent = self.new_parent_edit.text().strip()
        if not old_parent or not new_parent:
            self._show_message(self.swap_msg_label, "旧親画像IDと新親画像IDを入力してください。", error=True)
            return
        if self._api_client is None:
            return
        try:
            self._api_client.reverse_parent(old_parent, new_parent)
        except Exception as exc:
            self._show_message(self.swap_msg_label, f"逆転エラー: {exc}", error=True)
            return
        self._show_message(self.swap_msg_label, "親子を逆転しました。", error=False)
        self.list_refresh_needed.emit()
        self.refresh()

    def _on_unset_duplicate(self) -> None:
        """親子を解除ボタン押下。"""
        image_id = self.unset_id_edit.text().strip()
        if not image_id:
            self._show_message(self.unset_msg_label, "画像IDを入力してください。", error=True)
            return
        if self._api_client is None:
            return

        if image_id in self._parent_children:
            # 親として関係を解除
            children = self._parent_children[image_id]
            if len(children) > 1:
                reply = QMessageBox.question(
                    self,
                    "確認",
                    f"複数の関係（{len(children)}件）が削除されます。よろしいですか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            try:
                for child_id in list(children):
                    self._api_client.unset_duplicate(child_id, image_id)
            except Exception as exc:
                self._show_message(self.unset_msg_label, f"解除エラー: {exc}", error=True)
                return
        elif image_id in self._child_parent:
            # 子として関係を解除
            parent_id = self._child_parent[image_id]
            try:
                self._api_client.unset_duplicate(image_id, parent_id)
            except Exception as exc:
                self._show_message(self.unset_msg_label, f"解除エラー: {exc}", error=True)
                return
        else:
            self._show_message(self.unset_msg_label, "指定されたIDは親子関係に存在しません。", error=True)
            return

        self._show_message(self.unset_msg_label, "親子関係を解除しました。", error=False)
        self.list_refresh_needed.emit()
        self.refresh()

    def _unset_child(self, child_id: str, parent_id: str) -> None:
        """テーブルの解除ボタンから直接 unset_duplicate を呼び出す。"""
        if self._api_client is None:
            return
        try:
            self._api_client.unset_duplicate(child_id, parent_id)
        except Exception as exc:
            self._show_message(self.unset_msg_label, f"解除エラー: {exc}", error=True)
            return
        self.list_refresh_needed.emit()
        self.refresh()

    # ------------------------------------------------------------------
    # ユーティリティ
    # ------------------------------------------------------------------

    @staticmethod
    def _show_message(label: QLabel, text: str, *, error: bool = False) -> None:
        label.setText(text)
        color = "#D32F2F" if error else "#388E3C"
        label.setStyleSheet(f"color: {color}; font-size: 9pt;")


def _centered_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return item


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
