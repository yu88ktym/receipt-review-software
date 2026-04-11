from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QSpinBox, QSlider, QLineEdit, QCheckBox, QGroupBox, QColorDialog,
    QFrame, QScrollArea, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from app.config import theme
from app.config import status_colors
from app.config.settings_io import load_settings, save_settings


class TabSettings(QWidget):
    """設定タブ。各種パラメータを GUI で編集し settings.json に保存する。

    settings_saved シグナルには保存後の設定辞書が渡される。
    MainWindow はこのシグナルを受け取り画面全体の再適用処理を行う。
    """

    settings_saved = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._accent_color = QColor(theme.COLOR_ACCENT)
        self._status_colors: dict[str, QColor] = {
            k: QColor(v) for k, v in status_colors.STATUS_COLORS.items()
        }
        self._status_color_btns: dict[str, QPushButton] = {}
        self._build_ui()
        self._load_saved_settings()

    def _build_ui(self) -> None:
        # スクロール可能にして設定項目が増えても見切れないようにする
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(theme.PADDING, theme.PADDING, theme.PADDING, theme.PADDING)
        root.setSpacing(theme.MARGIN)

        cols = QHBoxLayout()
        cols.setSpacing(theme.PADDING)
        cols.addWidget(self._build_ui_settings(), stretch=1)
        cols.addWidget(self._build_network_settings(), stretch=1)
        root.addLayout(cols)

        root.addWidget(_divider())

        root.addWidget(self._build_border_settings())
        root.addWidget(_divider())
        root.addWidget(self._build_column_width_settings())
        root.addWidget(_divider())
        root.addWidget(self._build_status_color_settings())

        root.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        root.addWidget(self.save_btn)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_ui_settings(self) -> QGroupBox:
        group = QGroupBox("UI設定")
        layout = QGridLayout(group)
        layout.setSpacing(theme.MARGIN)
        row = 0

        layout.addWidget(QLabel("一覧の初期ページサイズ"), row, 0)
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(1, 500)
        self.page_size_spin.setValue(50)
        layout.addWidget(self.page_size_spin, row, 1)
        row += 1

        layout.addWidget(QLabel("詳細サイドバー幅 (%)"), row, 0)
        slider_row = QHBoxLayout()
        self.sidebar_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.sidebar_width_slider.setRange(10, 50)
        self.sidebar_width_slider.setValue(theme.DETAIL_PANEL_WIDTH_PERCENT)
        self.sidebar_width_lbl = QLabel(f"{theme.DETAIL_PANEL_WIDTH_PERCENT}%")
        self.sidebar_width_lbl.setFixedWidth(36)
        self.sidebar_width_slider.valueChanged.connect(
            lambda v: self.sidebar_width_lbl.setText(f"{v}%")
        )
        slider_row.addWidget(self.sidebar_width_slider)
        slider_row.addWidget(self.sidebar_width_lbl)
        slider_widget = QWidget()
        slider_widget.setLayout(slider_row)
        layout.addWidget(slider_widget, row, 1)
        row += 1

        layout.addWidget(QLabel("日付フォーマット"), row, 0)
        self.date_format_edit = QLineEdit("yyyy-MM-dd")
        layout.addWidget(self.date_format_edit, row, 1)
        row += 1

        layout.addWidget(QLabel("金額フォーマット"), row, 0)
        self.amount_format_edit = QLineEdit("¥{:,.0f}")
        layout.addWidget(self.amount_format_edit, row, 1)
        row += 1

        layout.addWidget(QLabel("重要チップ色"), row, 0)
        self.accent_color_btn = QPushButton()
        self._update_accent_btn()
        self.accent_color_btn.clicked.connect(self._pick_accent_color)
        layout.addWidget(self.accent_color_btn, row, 1)
        row += 1

        self.thumbnail_chk = QCheckBox("サムネイル表示")
        self.thumbnail_chk.setChecked(True)
        layout.addWidget(self.thumbnail_chk, row, 0, 1, 2)

        return group

    def _build_network_settings(self) -> QGroupBox:
        group = QGroupBox("通信設定")
        layout = QGridLayout(group)
        layout.setSpacing(theme.MARGIN)
        row = 0

        layout.addWidget(QLabel("差分ページサイズ"), row, 0)
        self.diff_page_size_spin = QSpinBox()
        self.diff_page_size_spin.setRange(1, 500)
        self.diff_page_size_spin.setValue(20)
        layout.addWidget(self.diff_page_size_spin, row, 1)
        row += 1

        layout.addWidget(QLabel("自動更新間隔 (秒)"), row, 0)
        self.auto_interval_spin = QSpinBox()
        self.auto_interval_spin.setRange(0, 3600)
        self.auto_interval_spin.setValue(0)
        self.auto_interval_spin.setSpecialValueText("無効")
        layout.addWidget(self.auto_interval_spin, row, 1)

        layout.setRowStretch(layout.rowCount(), 1)
        return group

    def _build_border_settings(self) -> QGroupBox:
        group = QGroupBox("罫線設定")
        layout = QGridLayout(group)
        layout.setSpacing(theme.MARGIN)

        layout.addWidget(QLabel("グリッド表示"), 0, 0)
        self.grid_chk = QCheckBox()
        self.grid_chk.setChecked(True)
        layout.addWidget(self.grid_chk, 0, 1)

        return group

    def _build_column_width_settings(self) -> QGroupBox:
        group = QGroupBox("カラム幅設定")
        layout = QGridLayout(group)
        layout.setSpacing(theme.MARGIN)

        col_defs = [
            ("レシートID", 100),
            ("アップロード日", 110),
            ("購入日", 100),
            ("合計金額", 90),
            ("店名", 150),
            ("支払方法", 100),
        ]
        self.col_width_spins: dict[str, QSpinBox] = {}
        for i, (name, default) in enumerate(col_defs):
            layout.addWidget(QLabel(name), i, 0)
            spin = QSpinBox()
            spin.setRange(50, 400)
            spin.setValue(default)
            layout.addWidget(spin, i, 1)
            self.col_width_spins[name] = spin

        return group

    def _build_status_color_settings(self) -> QGroupBox:
        group = QGroupBox("画像ステータス色設定")
        layout = QGridLayout(group)
        layout.setSpacing(theme.MARGIN)

        for i, status in enumerate(status_colors.STATUS_COLORS):
            layout.addWidget(QLabel(status), i, 0)
            btn = QPushButton()
            self._status_color_btns[status] = btn
            self._update_status_color_btn(status)
            btn.clicked.connect(lambda checked, s=status: self._pick_status_color(s))
            layout.addWidget(btn, i, 1)

        return group

    # ------------------------------------------------------------------
    # 色選択
    # ------------------------------------------------------------------

    def _pick_status_color(self, status: str) -> None:
        current = self._status_colors.get(status, QColor("#FFFFFF"))
        color = QColorDialog.getColor(current, self, f"{status} の色を選択")
        if color.isValid():
            self._status_colors[status] = color
            self._update_status_color_btn(status)

    def _update_status_color_btn(self, status: str) -> None:
        color = self._status_colors.get(status, QColor("#FFFFFF"))
        btn = self._status_color_btns[status]
        btn.setText(color.name())
        text_color = "#000000" if color.lightness() > 128 else "#FFFFFF"
        btn.setStyleSheet(
            f"background-color: {color.name()}; color: {text_color};"
        )

    def _pick_accent_color(self) -> None:
        color = QColorDialog.getColor(self._accent_color, self, "チップ色を選択")
        if color.isValid():
            self._accent_color = color
            self._update_accent_btn()

    def _update_accent_btn(self) -> None:
        self.accent_color_btn.setText(self._accent_color.name())
        self.accent_color_btn.setStyleSheet(
            f"background-color: {self._accent_color.name()}; color: #FFFFFF;"
        )

    # ------------------------------------------------------------------
    # 設定の保存・読み込み
    # ------------------------------------------------------------------

    def get_current_settings(self) -> dict:
        """現在の GUI 状態から設定辞書を生成する。"""
        return {
            "page_size": self.page_size_spin.value(),
            "detail_panel_width_percent": self.sidebar_width_slider.value(),
            "date_format": self.date_format_edit.text(),
            "amount_format": self.amount_format_edit.text(),
            "accent_color": self._accent_color.name(),
            "thumbnail_enabled": self.thumbnail_chk.isChecked(),
            "diff_page_size": self.diff_page_size_spin.value(),
            "auto_interval": self.auto_interval_spin.value(),
            "grid_visible": self.grid_chk.isChecked(),
            "column_widths": {k: v.value() for k, v in self.col_width_spins.items()},
            "status_colors": {k: v.name() for k, v in self._status_colors.items()},
        }

    def _on_save(self) -> None:
        settings = self.get_current_settings()
        try:
            save_settings(settings)
        except Exception as exc:
            QMessageBox.warning(self, "保存エラー", f"設定の保存に失敗しました。\n{exc}")
            return
        self.settings_saved.emit(settings)

    def _load_saved_settings(self) -> None:
        """起動時に settings.json から値を読み込んで GUI に反映する。"""
        data = load_settings()
        if not data:
            return

        if "page_size" in data:
            self.page_size_spin.setValue(data["page_size"])
        if "detail_panel_width_percent" in data:
            self.sidebar_width_slider.setValue(data["detail_panel_width_percent"])
        if "date_format" in data:
            self.date_format_edit.setText(data["date_format"])
        if "amount_format" in data:
            self.amount_format_edit.setText(data["amount_format"])
        if "accent_color" in data:
            self._accent_color = QColor(data["accent_color"])
            self._update_accent_btn()
        if "thumbnail_enabled" in data:
            self.thumbnail_chk.setChecked(data["thumbnail_enabled"])
        if "diff_page_size" in data:
            self.diff_page_size_spin.setValue(data["diff_page_size"])
        if "auto_interval" in data:
            self.auto_interval_spin.setValue(data["auto_interval"])
        if "grid_visible" in data:
            self.grid_chk.setChecked(data["grid_visible"])
        if "column_widths" in data:
            for name, value in data["column_widths"].items():
                if name in self.col_width_spins:
                    self.col_width_spins[name].setValue(value)
        if "status_colors" in data:
            for s, hex_color in data["status_colors"].items():
                color = QColor(hex_color)
                if color.isValid():
                    self._status_colors[s] = color
                    if s in self._status_color_btns:
                        self._update_status_color_btn(s)


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
