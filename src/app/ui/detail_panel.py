from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from app.config import theme


class DetailPanel(QWidget):
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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
            ("receipt_id", "レシートID"),
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
            lbl.setFixedWidth(110)
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
        layout.addWidget(self.original_btn)

        layout.addWidget(_divider())

        # ゴミ箱操作
        trash_heading = QLabel("ゴミ箱操作")
        layout.addWidget(trash_heading)

        trash_row = QHBoxLayout()
        self.trash_btn = QPushButton("ゴミ箱へ移動")
        self.trash_btn.setProperty("danger", "true")
        self.restore_btn = QPushButton("復元")
        self.restore_btn.setProperty("flat", "true")
        trash_row.addWidget(self.trash_btn)
        trash_row.addWidget(self.restore_btn)
        layout.addLayout(trash_row)

        layout.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

    def load(self, data: dict) -> None:
        """
        dataのキーは field_defs の key に対応する。
        image_pixmap キーが存在すれば QPixmap として画像を表示する。
        """
        for key, lbl in self.fields.items():
            lbl.setText(str(data.get(key, "—")))
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


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
