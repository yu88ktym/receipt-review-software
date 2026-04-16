"""サムネイルタイルウィジェット。一覧のサムネイル表示で各レシートを表すカード。"""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from app.config.status_colors import get_row_color

_DEFAULT_TILE_W = 160
_DEFAULT_TILE_H = 200


class ReceiptTileWidget(QFrame):
    """単一レシートのサムネイルタイル。

    クリック時に clicked シグナルに data dict を渡す。
    api_client が None の場合は画像なし表示のみ。
    """

    clicked = Signal(dict)

    def __init__(
        self,
        data: dict,
        api_client=None,
        tile_w: int = _DEFAULT_TILE_W,
        tile_h: int = _DEFAULT_TILE_H,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._data = data
        self._api_client = api_client
        self._tile_w = tile_w
        self._tile_h = tile_h
        self.setFixedSize(tile_w, tile_h)
        self._build_ui(tile_w, tile_h)
        self._apply_status_color()
        self._load_image()

    # ------------------------------------------------------------------
    # UI 構築
    # ------------------------------------------------------------------

    def _build_ui(self, tile_w: int, tile_h: int) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # 画像エリア（テキストラベル分を除いた高さ）
        img_h = max(tile_h - 56, 20)
        self.image_lbl = QLabel()
        self.image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_lbl.setFixedHeight(img_h)
        self.image_lbl.setText("画像なし")
        self.image_lbl.setStyleSheet("background: #F5F5F5; border: none;")
        layout.addWidget(self.image_lbl)

        image_id = (
            self._data.get("image_id")
            or self._data.get("receipt_id")
            or "—"
        )
        id_lbl = QLabel(str(image_id))
        id_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_lbl.setWordWrap(True)
        id_lbl.setStyleSheet("font-size: 8pt; background: transparent;")
        layout.addWidget(id_lbl)

        upload_date = (
            self._data.get("created_at")
            or self._data.get("upload_date")
            or "—"
        )
        date_str = str(upload_date)
        # yyyy-mm-dd 形式に切り詰め
        if "T" in date_str:
            date_str = date_str[:10]
        date_lbl = QLabel(date_str)
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_lbl.setStyleSheet("font-size: 8pt; background: transparent;")
        layout.addWidget(date_lbl)

    # ------------------------------------------------------------------
    # ステータス色
    # ------------------------------------------------------------------

    def _apply_status_color(self) -> None:
        status = str(self._data.get("status") or "")
        color = get_row_color(status)
        border = color.darker(130)
        self.setStyleSheet(
            f"ReceiptTileWidget {{"
            f"  background-color: {color.name()};"
            f"  border: 2px solid {border.name()};"
            f"  border-radius: 4px;"
            f"}}"
        )

    # ------------------------------------------------------------------
    # 画像読み込み
    # ------------------------------------------------------------------

    def _load_image(self) -> None:
        if self._api_client is None:
            return
        image_id = (
            self._data.get("image_id")
            or self._data.get("receipt_id")
            or ""
        )
        if not image_id or image_id == "—":
            return
        try:
            image_bytes = self._api_client.get_image_file(image_id, "thumb")
        except Exception:
            return
        if not image_bytes:
            return
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        if pixmap.isNull():
            return
        w = self._tile_w - 8
        h = max(self._tile_h - 56, 20)
        scaled = pixmap.scaled(
            w,
            h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_lbl.setText("")
        self.image_lbl.setPixmap(scaled)

    # ------------------------------------------------------------------
    # マウスイベント
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._data)
