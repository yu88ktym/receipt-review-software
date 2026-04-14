from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from app.config import theme
from app.ui.ui_utils import resolve_trash_button_mode
from app.ui.image_viewer import ImageViewer


class DetailPanel(QWidget):
    """詳細パネル。選択されたレシートの詳細情報・画像・操作ボタンを表示する。"""

    closed = Signal()
    trash_requested = Signal(str)    # image_id
    restore_requested = Signal(str)  # image_id
    list_refresh_needed = Signal()

    def __init__(self, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_image_id: str | None = None
        self._api_client = api_client
        self._image_viewers: list[ImageViewer] = []
        self._thumb_pixmap: QPixmap | None = None
        self._build_ui()
        self.closed.connect(self._close_image_viewers)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        layout.setSpacing(theme.MARGIN)

        # ヘッダー行（タイトル + 閉じるボタン）
        header_row = QHBoxLayout()
        title_lbl = QLabel("詳細")
        title_lbl.setProperty("heading", "true")
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        self.close_btn = QPushButton("× 閉じる")
        self.close_btn.setProperty("flat", "true")
        self.close_btn.clicked.connect(self.closed.emit)
        header_row.addWidget(self.close_btn)
        layout.addLayout(header_row)

        layout.addWidget(_divider())

        # 基本情報フィールド
        self.fields: dict[str, QLabel] = {}
        field_defs = [
            ("image_id", "レシートID"),
            ("created_at", "アップロード日"),
            ("purchased_at", "購入日"),
            ("total_amount", "合計金額"),
            ("store_name", "店名"),
            ("payment_method", "支払方法"),
            ("status", "ステータス"),
            ("quality_level", "品質レベル"),
            ("integrity_status", "整合性ステータス"),
        ]
        for key, label_text in field_defs:
            row = QHBoxLayout()
            lbl = QLabel(f"{label_text}：")
            lbl.setFixedWidth(120)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            value_lbl = QLabel("—")
            value_lbl.setWordWrap(True)
            value_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row.addWidget(lbl)
            row.addWidget(value_lbl)
            layout.addLayout(row)
            self.fields[key] = value_lbl

        layout.addWidget(_divider())

        # 画像表示エリア
        img_heading = QLabel("画像")
        img_heading.setProperty("heading", "true")
        layout.addWidget(img_heading)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.image_label.setMinimumHeight(50)
        self.image_label.setStyleSheet(f"border: 1px solid {theme.COLOR_DIVIDER}; background: #F5F5F5;")
        self.image_label.setText("画像なし")
        layout.addWidget(self.image_label)

        self.original_btn = QPushButton("原本を表示")
        self.original_btn.setProperty("flat", "true")
        self.original_btn.clicked.connect(self._on_show_original)
        layout.addWidget(self.original_btn)

        layout.addWidget(_divider())

        # ゴミ箱操作
        trash_heading = QLabel("ゴミ箱操作")
        layout.addWidget(trash_heading)

        trash_row = QHBoxLayout()

        # ステータスに応じて一方のみ表示する（load() で切り替え）
        self.trash_btn = QPushButton("🗑️ ゴミ箱へ移動")
        self.trash_btn.setProperty("danger", "true")
        self.trash_btn.clicked.connect(self._on_move_to_trash)
        self.restore_btn = QPushButton("復元")
        self.restore_btn.setProperty("flat", "true")
        self.restore_btn.clicked.connect(self._on_restore)
        trash_row.addWidget(self.trash_btn)
        trash_row.addWidget(self.restore_btn)
        layout.addLayout(trash_row)

        layout.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

    # ------------------------------------------------------------------
    # 公開インターフェース
    # ------------------------------------------------------------------

    def load(self, data: dict) -> None:
        """
        ImageMeta（dict）を受け取り詳細パネルを更新する。
        フラット・ネスト両形式に対応する。
        """
        final: dict = data.get("final_receipt") or {}
        ocr: dict = data.get("ocr_receipt_info") or {}

        # image_id / created_at はトップレベル
        self._current_image_id = str(data.get("image_id", ""))
        self.fields["image_id"].setText(self._current_image_id or "—")
        self.fields["created_at"].setText(str(data.get("created_at", "—")))

        # 購入情報は final_receipt → ocr_receipt_info の順で参照
        self.fields["purchased_at"].setText(
            str(final.get("purchased_at") or ocr.get("purchased_at") or "—")
        )
        total = (
            final["total_amount"] if "total_amount" in final and final["total_amount"] is not None
            else ocr.get("total_amount")
        )
        self.fields["total_amount"].setText(f"¥{total:,}" if total is not None else "—")
        self.fields["store_name"].setText(
            str(final.get("store_name") or ocr.get("store_name") or "—")
        )
        self.fields["payment_method"].setText(
            str(final.get("payment_method") or ocr.get("payment_method") or "—")
        )

        status = str(data.get("status") or "")
        self.fields["status"].setText(status or "—")
        self.fields["quality_level"].setText(str(data.get("quality_level", "—")))
        self.fields["integrity_status"].setText(str(data.get("integrity_status", "—")))

        # ゴミ箱/復元ボタンをステータスに応じて切り替え
        mode = resolve_trash_button_mode(status)
        self.trash_btn.setVisible(mode == "trash")
        self.restore_btn.setVisible(mode == "restore")

        # サムネイルを読み込む
        self._load_image("thumb")

    # ------------------------------------------------------------------
    # ボタンハンドラ
    # ------------------------------------------------------------------

    def _load_image(self, variant: str) -> None:
        """指定バリアントの画像をAPIから取得して image_label に表示する。"""
        if not self._current_image_id or self._api_client is None:
            self._thumb_pixmap = None
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("画像なし")
            return
        try:
            image_bytes = self._api_client.get_image_file(self._current_image_id, variant)
        except Exception:
            self._thumb_pixmap = None
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("画像が見つかりません。")
            return

        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        if pixmap.isNull():
            self._thumb_pixmap = None
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("画像が見つかりません。")
            return

        self.image_label.setText("")
        self._thumb_pixmap = pixmap
        self._apply_thumb_pixmap()

    def _apply_thumb_pixmap(self) -> None:
        """保存済みサムネイルを現在のラベル幅に合わせて再描画する。"""
        if self._thumb_pixmap is None or self._thumb_pixmap.isNull():
            return
        available_width = self.image_label.width()
        if available_width > 0:
            scaled = self._thumb_pixmap.scaledToWidth(
                available_width,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setFixedHeight(scaled.height())
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setPixmap(self._thumb_pixmap)

    def resizeEvent(self, event) -> None:
        """パネルサイズ変更時にサムネイルを再スケールする。"""
        super().resizeEvent(event)
        self._apply_thumb_pixmap()

    def _on_show_original(self) -> None:
        """原本画像を新しい別ウィンドウで表示する。"""
        if self._current_image_id is None or self._api_client is None:
            return
        try:
            image_bytes = self._api_client.get_image_file(self._current_image_id, "original")
        except Exception as exc:
            QMessageBox.warning(self, "画像取得エラー", f"画像の取得に失敗しました。\n{exc}")
            return

        viewer = ImageViewer(image_id=self._current_image_id)
        viewer.load_image(image_bytes)
        viewer.viewer_closed.connect(self._on_viewer_closed)
        self._image_viewers.append(viewer)
        viewer.show()
        viewer.raise_()
        viewer.activateWindow()

    def _on_viewer_closed(self, viewer: ImageViewer) -> None:
        """ビューアが閉じられたときにリストから除去する。"""
        try:
            self._image_viewers.remove(viewer)
        except ValueError:
            pass

    def _close_image_viewers(self) -> None:
        """すべての ImageViewer ウィンドウを閉じる。"""
        for viewer in list(self._image_viewers):
            viewer.close()
        self._image_viewers.clear()

    def close_image_viewer(self) -> None:
        """外部から ImageViewer ウィンドウを閉じる（main_window から呼び出す用）。"""
        self._close_image_viewers()

    def _on_move_to_trash(self) -> None:
        """ゴミ箱へ移動し、一覧の更新を要求する。"""
        if self._current_image_id is None or self._api_client is None:
            return
        try:
            self._api_client.move_to_dustbox(self._current_image_id)
        except Exception as exc:
            QMessageBox.warning(self, "通信エラー", f"ゴミ箱への移動に失敗しました。\n{exc}")
            return

        # ステータス更新を反映
        self.fields["status"].setText("DROPPED")
        self.trash_btn.setVisible(False)
        self.restore_btn.setVisible(True)
        self.list_refresh_needed.emit()

    def _on_restore(self) -> None:
        """ゴミ箱から復元し、一覧の更新を要求する。"""
        if self._current_image_id is None or self._api_client is None:
            return
        try:
            self._api_client.restore_from_dustbox(self._current_image_id)
        except Exception as exc:
            QMessageBox.warning(self, "通信エラー", f"復元に失敗しました。\n{exc}")
            return

        # ステータス更新を反映（INGESTED に戻す）
        self.fields["status"].setText("INGESTED")
        self.restore_btn.setVisible(False)
        self.trash_btn.setVisible(True)
        self.list_refresh_needed.emit()


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
