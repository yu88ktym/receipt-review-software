from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QTabWidget, QSplitter,
)
from PySide6.QtCore import Qt

from app.config import theme
from app.ui.sidebar import Sidebar
from app.ui.detail_panel import DetailPanel
from app.ui.tabs.tab_list import TabList
from app.ui.tabs.tab_final_edit import TabFinalEdit
from app.ui.tabs.tab_quality import TabQuality
from app.ui.tabs.tab_dups import TabDups
from app.ui.tabs.tab_autocomplete import TabAutocomplete
from app.ui.tabs.tab_export_csv import TabExportCsv
from app.ui.tabs.tab_upload import TabUpload
from app.ui.tabs.tab_settings import TabSettings


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Receipt Review Software")
        self.setMinimumSize(1800, 1000)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 左サイドバー
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        # 中央タブ + 右パネルをスプリッターで分割
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # 中央タブ
        self.tabs = QTabWidget()
        self._tab_list = TabList()
        self._tab_final_edit = TabFinalEdit()
        self._tab_quality = TabQuality()
        self._tab_dups = TabDups()
        self._tab_autocomplete = TabAutocomplete()
        self._tab_export_csv = TabExportCsv()
        self._tab_upload = TabUpload()
        self._tab_settings = TabSettings()

        self.tabs.addTab(self._tab_list, "一覧")
        self.tabs.addTab(self._tab_final_edit, "確定値編集")
        self.tabs.addTab(self._tab_quality, "品質確認")
        self.tabs.addTab(self._tab_dups, "Dups")
        self.tabs.addTab(self._tab_autocomplete, "自動補完設定")
        self.tabs.addTab(self._tab_export_csv, "CSVエクスポート")
        self.tabs.addTab(self._tab_upload, "画像アップロード")
        self.tabs.addTab(self._tab_settings, "設定")

        # 右詳細パネル
        self.detail_panel = DetailPanel()
        self.detail_panel.closed.connect(self._on_detail_closed)

        splitter.addWidget(self.tabs)
        splitter.addWidget(self.detail_panel)

        # 詳細パネルの初期幅を画面全体の DETAIL_PANEL_WIDTH_PERCENT% に設定
        splitter.setSizes([1000 - theme.DETAIL_PANEL_WIDTH_PERCENT * 10,
                           theme.DETAIL_PANEL_WIDTH_PERCENT * 10])

        root.addWidget(splitter, stretch=1)

        # シグナル接続
        self._tab_list.detail_requested.connect(self._show_detail)
        self._tab_quality.detail_requested.connect(self._show_detail)

    def _show_detail(self, data: dict) -> None:
        self.detail_panel.load(data)
        self.detail_panel.setVisible(True)

    def _on_detail_closed(self) -> None:
        self.detail_panel.setVisible(False)
