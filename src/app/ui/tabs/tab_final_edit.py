from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDateEdit, QComboBox, QHeaderView,
    QFrame, QFormLayout, QGroupBox, QStackedWidget, QMessageBox,
)
from PySide6.QtCore import Qt, QDate, Signal
import requests
from app.config import theme
from app.config.status_colors import apply_row_colors
from app.config.settings_io import load_settings
from app.models.types import ImageMeta
from app.ui.ui_utils import image_meta_to_row, build_dup_maps, extract_api_error
from app.ui.widgets.tile_view import TileView

_HEADERS = ["レシートID", "アップロード日", "購入日", "合計金額", "店名", "支払方法", "ステータス", "親子", "操作"]

# ステータス値が格納される列インデックス
_STATUS_COL = 6
_DUP_COL = 7
_ACTION_COL = 8

_STORE_CANDIDATES = ["コンビニA", "スーパーB", "レストランC", "カフェD", "百貨店E"]
_PAYMENT_CANDIDATES = ["現金", "クレジット", "電子マネー", "QRコード"]


class TabFinalEdit(QWidget):
    detail_requested = Signal(dict)
    list_refresh_needed = Signal()
    view_mode_changed = Signal(bool)  # True = タイル表示, False = テキスト表示

    def __init__(self, service=None, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._api_client = api_client
        self._tile_mode = False
        self._all_items: list[ImageMeta] = []
        self._current_item: ImageMeta | None = None
        self._child_to_parent: dict[str, str] = {}
        self._parent_to_children: dict[str, list[str]] = {}
        self._build_ui()
        self.load_data()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        # ツールバー（切り替えボタン）
        toolbar = QHBoxLayout()
        self.view_toggle_btn = QPushButton("サムネイル表示")
        self.view_toggle_btn.setProperty("flat", "true")
        self.view_toggle_btn.clicked.connect(self._toggle_view)
        toolbar.addWidget(self.view_toggle_btn)
        toolbar.addStretch()
        root.addLayout(toolbar)

        # スタック（テキスト / サムネイル）
        self._stacked = QStackedWidget()

        self.table = QTableWidget(0, len(_HEADERS))
        self.table.setHorizontalHeaderLabels(_HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(_DUP_COL, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(_ACTION_COL, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(_DUP_COL, 90)
        self.table.setColumnWidth(_ACTION_COL, 80)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self._stacked.addWidget(self.table)

        # タイルビュー（インデックス 1）
        self.tile_view = TileView()
        self.tile_view.item_clicked.connect(self._on_tile_clicked)
        self._stacked.addWidget(self.tile_view)

        root.addWidget(self._stacked)

        # 入力フォーム
        form_group = QGroupBox("確定値を編集")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(theme.MARGIN)

        self.edit_purchase_date = QDateEdit()
        self.edit_purchase_date.setDisplayFormat("yyyy-MM-dd")
        self.edit_purchase_date.setCalendarPopup(True)
        self.edit_purchase_date.setDate(QDate.currentDate())
        form_layout.addRow("購入日", self.edit_purchase_date)

        self.edit_total = QLineEdit()
        self.edit_total.setPlaceholderText("合計金額（数値）")
        form_layout.addRow("合計金額", self.edit_total)

        store_row = QHBoxLayout()
        self.edit_store = QLineEdit()
        self.edit_store.setPlaceholderText("店名")
        self.store_suggest = QComboBox()
        self.store_suggest.addItem("候補から選択")
        self.store_suggest.addItems(_STORE_CANDIDATES)
        self.store_suggest.currentTextChanged.connect(
            lambda t: self.edit_store.setText(t) if t != "候補から選択" else None
        )
        store_row.addWidget(self.edit_store)
        store_row.addWidget(self.store_suggest)
        form_layout.addRow("店名", store_row)

        payment_row = QHBoxLayout()
        self.edit_payment = QLineEdit()
        self.edit_payment.setPlaceholderText("支払方法")
        self.payment_suggest = QComboBox()
        self.payment_suggest.addItem("候補から選択")
        self.payment_suggest.addItems(_PAYMENT_CANDIDATES)
        self.payment_suggest.currentTextChanged.connect(
            lambda t: self.edit_payment.setText(t) if t != "候補から選択" else None
        )
        payment_row.addWidget(self.edit_payment)
        payment_row.addWidget(self.payment_suggest)
        form_layout.addRow("支払方法", payment_row)

        self.confirm_btn = QPushButton("確定")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._on_confirm)
        form_layout.addRow("", self.confirm_btn)

        self.msg_label = QLabel()
        self.msg_label.setWordWrap(True)
        form_layout.addRow("", self.msg_label)

        root.addWidget(form_group)

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
        """サービスまたはAPIクライアントからデータを取得してテーブルを更新する。"""
        if self._service is not None:
            try:
                self._all_items = self._service.fetch_list(force_refresh=True)
            except Exception as exc:
                self._show_message(f"データ取得エラー: {exc}", error=True)
                return
        elif self._api_client is not None:
            try:
                self._all_items = self._api_client.list_receipts()
            except Exception as exc:
                self._show_message(f"データ取得エラー: {exc}", error=True)
                return
        self._populate()

    def refresh(self) -> None:
        """一覧を強制再取得する（外部からも呼び出し可能）。"""
        if self._service is not None:
            self._service.invalidate_cache()
        self.load_data()

    # ------------------------------------------------------------------
    # 表示更新
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        self._child_to_parent, self._parent_to_children = build_dup_maps(self._all_items)
        self._populate_table()
        if self._tile_mode:
            self._populate_tiles()

    def _populate_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for item in self._all_items:
            row_data = image_meta_to_row(item)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, cell)
            dup_cell = QTableWidgetItem(_dup_role_label(item, self._child_to_parent, self._parent_to_children))
            dup_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, _DUP_COL, dup_cell)
            detail_btn = QPushButton("詳細")
            detail_btn.clicked.connect(lambda checked, d=item: self.detail_requested.emit(d))
            self.table.setCellWidget(row, _ACTION_COL, detail_btn)
        apply_row_colors(self.table, _STATUS_COL)
        self.table.setSortingEnabled(True)

    def _populate_tiles(self) -> None:
        """タイルビューをデータで更新する。"""
        tile_data = [
            {
                "image_id": item.get("image_id", "—"),
                "created_at": item.get("created_at", "—"),
                "status": item.get("status", ""),
                "dup_role": _dup_role_key(item, self._child_to_parent, self._parent_to_children),
            }
            for item in self._all_items
        ]
        settings = load_settings()
        tile_w = settings.get("thumbnail_tile_width", 160)
        tile_h = settings.get("thumbnail_tile_height", 200)
        self.tile_view.set_items(tile_data, self._api_client, tile_w, tile_h)

    # ------------------------------------------------------------------
    # 選択・フォーム連携
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            self._current_item = None
            self._update_confirm_btn(None)
            return
        row = self.table.currentRow()
        image_id_cell = self.table.item(row, 0)
        if image_id_cell is None:
            return
        image_id = image_id_cell.text()
        item = next((i for i in self._all_items if i.get("image_id") == image_id), None)
        self._current_item = item
        if item is None:
            return
        self._populate_form(item)
        self._update_confirm_btn(str(item.get("status") or ""))

    def _on_tile_clicked(self, data: dict) -> None:
        """タイルクリック時: 詳細表示 + フォーム更新。"""
        image_id = data.get("image_id", "")
        item = next((i for i in self._all_items if i.get("image_id") == image_id), None)
        self._current_item = item
        if item is not None:
            self._populate_form(item)
            self._update_confirm_btn(str(item.get("status") or ""))
        self.detail_requested.emit(data)

    def _populate_form(self, item: ImageMeta) -> None:
        """ImageMeta からフォームに値を設定する。"""
        final: dict = item.get("final_receipt") or {}
        ocr: dict = item.get("ocr_receipt_info") or {}

        purchase_date = (
            final.get("purchased_at")
            or ocr.get("purchased_at")
            or item.get("purchase_date")
            or ""
        )
        if purchase_date:
            date = QDate.fromString(str(purchase_date), "yyyy-MM-dd")
            if date.isValid():
                self.edit_purchase_date.setDate(date)

        total = final.get("total_amount") if final.get("total_amount") is not None else ocr.get("total_amount")
        self.edit_total.setText(str(total) if total is not None else "")

        store = final.get("store_name") or ocr.get("store_name") or item.get("store_name") or ""
        self.edit_store.setText(str(store))

        payment = (
            final.get("payment_method")
            or ocr.get("payment_method")
            or item.get("payment_method")
            or ""
        )
        self.edit_payment.setText(str(payment))

    def _update_confirm_btn(self, status: str | None) -> None:
        """ステータスに応じて確定ボタンのテキスト・スタイル・活性状態を更新する。"""
        if status is None:
            self.confirm_btn.setText("確定")
            self.confirm_btn.setEnabled(False)
            self.confirm_btn.setStyleSheet("")
        elif status == "FINAL_UPDATED":
            self.confirm_btn.setText("遡及修正")
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setStyleSheet(
                "QPushButton { background-color: #D32F2F; color: #FFFFFF; border-radius: 4px; }"
                "QPushButton:hover { background-color: #B71C1C; }"
            )
        elif status in ("FINAL_UPDATED_CHILD", "DROPPED"):
            self.confirm_btn.setText("確定")
            self.confirm_btn.setEnabled(False)
            self.confirm_btn.setStyleSheet(
                "QPushButton { background-color: #9E9E9E; color: #FFFFFF; border-radius: 4px; }"
            )
        else:
            self.confirm_btn.setText("確定")
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setStyleSheet("")

    # ------------------------------------------------------------------
    # 確定・遡及修正
    # ------------------------------------------------------------------

    def _on_confirm(self) -> None:
        """確定ボタン押下時の処理。"""
        if self._current_item is None or self._api_client is None:
            return
        image_id = str(self._current_item.get("image_id") or "")
        status = str(self._current_item.get("status") or "")
        if not image_id:
            return

        purchase_date = self.edit_purchase_date.date().toString("yyyy-MM-dd")
        total_text = self.edit_total.text().strip()
        store = self.edit_store.text().strip()
        payment = self.edit_payment.text().strip()

        if not total_text:
            self._show_message("合計金額を入力してください。", error=True)
            return
        try:
            total_amount = int(total_text)
        except ValueError:
            self._show_message("合計金額は整数値を入力してください。", error=True)
            return

        body = {
            "purchased_at": purchase_date,
            "total_amount": total_amount,
            "store_name": store,
            "payment_method": payment,
        }

        try:
            if status == "FINAL_UPDATED":
                self._api_client.revise_final_receipt(image_id, body)
            else:
                self._api_client.finalize_receipt(image_id, body)
        except requests.HTTPError as exc:
            self._show_api_error(exc)
            return
        except Exception as exc:
            self._show_message(f"送信エラー: {exc}", error=True)
            return

        self._show_message("送信しました。", error=False)
        self.list_refresh_needed.emit()
        self.refresh()

    def _show_message(self, text: str, *, error: bool = False) -> None:
        self.msg_label.setText(text)
        color = "#D32F2F" if error else "#388E3C"
        self.msg_label.setStyleSheet(f"color: {color}; font-size: 9pt;")

    def _show_api_error(self, exc: requests.HTTPError) -> None:
        """HTTPErrorからAPIエラー詳細を抽出してメッセージラベルに表示する。"""
        detail = extract_api_error(exc)
        self._show_message(f"送信エラー\n{detail}", error=True)


# ---------------------------------------------------------------------------
# 親子ロール表示ヘルパー
# ---------------------------------------------------------------------------

def _dup_role_key(
    item: ImageMeta,
    child_to_parent: dict[str, str],
    parent_to_children: dict[str, list[str]],
) -> str | None:
    """タイルに付与する dup_role キー（"parent" / "child" / None）を返す。"""
    iid = str(item.get("image_id") or "")
    if iid in parent_to_children:
        return "parent"
    if iid in child_to_parent:
        return "child"
    return None


def _dup_role_label(
    item: ImageMeta,
    child_to_parent: dict[str, str],
    parent_to_children: dict[str, list[str]],
) -> str:
    """テーブルの「親子」セルに表示するラベル文字列を返す。"""
    iid = str(item.get("image_id") or "")
    if iid in parent_to_children:
        n = len(parent_to_children[iid])
        return f"👑 親（子{n}枚）"
    if iid in child_to_parent:
        return f"🔗 子"
    return "—"
