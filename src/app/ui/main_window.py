from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QTabWidget, QSplitter, QApplication,
)
from PySide6.QtCore import Qt

from app.config import theme
from app.config import status_colors
from app.config.env import API_BASE, API_KEY, USE_MOCK
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
from app.services.receipts_service import ReceiptsService


def _build_api_client():
    """USE_MOCKフラグに応じてAPIクライアントを生成する。"""
    if USE_MOCK:
        from app.api.mock_client import MockApiClient
        return MockApiClient()
    from app.api.client import ApiClient
    return ApiClient(API_BASE, API_KEY)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Receipt Review Software")
        self.setMinimumSize(1800, 1000)
        self._api_client = _build_api_client()
        self._service = ReceiptsService(self._api_client)  # type: ignore[arg-type]
        self._build_ui()
        self._connect_signals()

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
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)

        # 中央タブ
        self.tabs = QTabWidget()
        self._tab_list = TabList(service=self._service, api_client=self._api_client)
        self._tab_final_edit = TabFinalEdit(service=self._service, api_client=self._api_client)
        self._tab_quality = TabQuality(api_client=self._api_client)
        self._tab_dups = TabDups(service=self._service, api_client=self._api_client)
        self._tab_autocomplete = TabAutocomplete()
        self._tab_export_csv = TabExportCsv()
        self._tab_upload = TabUpload(api_client=self._api_client)
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
        self.detail_panel = DetailPanel(api_client=self._api_client)
        self.detail_panel.closed.connect(self._on_detail_closed)

        self._splitter.addWidget(self.tabs)
        self._splitter.addWidget(self.detail_panel)

        # 詳細パネルの初期幅を画面全体の DETAIL_PANEL_WIDTH_PERCENT% に設定
        self._apply_splitter_sizes(theme.DETAIL_PANEL_WIDTH_PERCENT)

        root.addWidget(self._splitter, stretch=1)

    def _connect_signals(self) -> None:
        """コンポーネント間のシグナルをすべてここで接続する。"""
        # 詳細パネルの表示要求
        self._tab_list.detail_requested.connect(self._show_detail)
        self._tab_quality.detail_requested.connect(self._show_detail)
        self._tab_final_edit.detail_requested.connect(self._show_detail)
        self._tab_dups.detail_requested.connect(self._show_detail)

        # サイドバー: 更新ボタン → 一覧リフレッシュ
        self.sidebar.refresh_btn.clicked.connect(self._tab_list.refresh)

        # サイドバー: フィルタ変更 → 一覧更新
        self.sidebar.filter_changed.connect(self._tab_list.load_data)

        # 詳細パネル: ゴミ箱操作完了 → 一覧リフレッシュ
        self.detail_panel.list_refresh_needed.connect(self._tab_list.refresh)

        # 確定値編集・Dups: 操作完了 → 一覧リフレッシュ
        self._tab_final_edit.list_refresh_needed.connect(self._tab_list.refresh)
        self._tab_dups.list_refresh_needed.connect(self._tab_list.refresh)

        # アップロード完了 → 一覧リフレッシュ
        self._tab_upload.upload_completed.connect(self._tab_list.refresh)

        # 設定保存 → 画面全体リフレッシュ
        self._tab_settings.settings_saved.connect(self._on_settings_saved)

        # 表示モード同期（一方のタブで切り替えると他のタブにも反映）
        _view_mode_tabs = [
            self._tab_list, self._tab_final_edit, self._tab_quality, self._tab_dups,
        ]
        for tab in _view_mode_tabs:
            tab.view_mode_changed.connect(self._on_view_mode_changed)

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _show_detail(self, data: dict) -> None:
        self.detail_panel.load(data)
        self.detail_panel.setVisible(True)

    def _on_detail_closed(self) -> None:
        self.detail_panel.close_image_viewer()
        self.detail_panel.setVisible(False)

    def _on_settings_saved(self, settings: dict) -> None:
        """保存された設定をアプリ全体に即時反映する。"""
        # ステータス色を更新
        if "status_colors" in settings:
            status_colors.STATUS_COLORS.update(settings["status_colors"])

        # 詳細サイドバー幅を更新
        if "detail_panel_width_percent" in settings:
            pct = settings["detail_panel_width_percent"]
            self._apply_splitter_sizes(pct)

        # スタイルシートを再適用（フォントや色の変更を反映）
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.STYLESHEET)

    def _apply_splitter_sizes(self, detail_pct: int) -> None:
        """スプリッターの幅比率を設定する。"""
        total = 1000
        detail = total * detail_pct // 100
        self._splitter.setSizes([total - detail, detail])

    def _on_view_mode_changed(self, tile_mode: bool) -> None:
        """いずれかのタブで表示モードが切り替えられたとき、他のタブにも伝播する。"""
        for tab in (self._tab_list, self._tab_final_edit, self._tab_quality, self._tab_dups):
            tab.set_tile_mode(tile_mode)
