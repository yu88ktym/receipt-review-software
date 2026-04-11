from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from app.config import theme
from app.ui.ui_utils import resolve_trash_button_mode


class DetailPanel(QWidget):
    """詳細パネル。選択されたレシートの詳細情報・画像・操作ボタンを表示する。"""

    closed = Signal()
    list_refresh_needed = Signal()

    def __init__(self, api_client=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._api_client = api_client
        self._current_image_id: str | None = None
        self._build_ui()

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
            ("upload_date", "アップロード日"),
            ("purchase_date", "購入日"),
            ("total_amount", "合計金額"),
            ("store_name", "店名"),
            ("payment_method", "支払方法"),
            ("status", "ステータス"),
            ("quality_level", "品質レベル"),
            ("consistency_status", "整合性ステータス"),
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
        self.image_label.setFixedHeight(200)
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

        # ステータスに応じて一方のみ表示する（load() で切り替え）
        self.trash_btn = QPushButton("🗑️ ゴミ箱へ移動")
        self.trash_btn.setProperty("danger", "true")
        self.trash_btn.clicked.connect(self._on_move_to_trash)
        layout.addWidget(self.trash_btn)

        self.restore_btn = QPushButton("♻️ ゴミ箱から復元")
        self.restore_btn.setProperty("flat", "true")
        self.restore_btn.clicked.connect(self._on_restore)
        layout.addWidget(self.restore_btn)

        layout.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

    # ------------------------------------------------------------------
    # 公開インターフェース
    # ------------------------------------------------------------------

    def load(self, data: dict) -> None:
        """レシートデータを受け取り詳細パネルに表示する。

        data のキーは field_defs の key に対応する。
        image_pixmap キーが存在すれば QPixmap として画像を表示する。
        """
        self._current_image_id = data.get("image_id")

        for key, lbl in self.fields.items():
            value = data.get(key)
            lbl.setText("—" if value is None else str(value))

        # 画像
        pixmap: QPixmap | None = data.get("image_pixmap")
        if pixmap and not pixmap.isNull():
            self.image_label.setPixmap(
                pixmap.scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.image_label.setText("画像なし")
            self.image_label.setPixmap(QPixmap())

        # ゴミ箱操作ボタンの表示切り替え
        status = str(data.get("status") or "")
        mode = resolve_trash_button_mode(status)
        self.trash_btn.setVisible(mode == "trash")
        self.restore_btn.setVisible(mode == "restore")

    # ------------------------------------------------------------------
    # ボタンハンドラ
    # ------------------------------------------------------------------

    def _on_show_original(self) -> None:
        """原本画像を API から取得して表示する。"""
        if self._current_image_id is None or self._api_client is None:
            return
        try:
            image_bytes = self._api_client.get_image_file(self._current_image_id, "original")
        except Exception as exc:
            QMessageBox.warning(self, "通信エラー", f"画像の取得に失敗しました。\n{exc}")
            return

        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        if pixmap.isNull():
            QMessageBox.information(self, "画像", "画像データを読み込めませんでした。")
            return

        self.image_label.setPixmap(
            pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

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
