"""タイルビューウィジェット。

TileView       – グリッドレイアウトでタイルを並べるスクロール可能なビュー。
DupsTileView   – Dups タブ専用。親タイルを左列、子タイルを右列に配置し
                 接続線を描画する。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QScrollArea, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QPen, QColor

from app.ui.widgets.thumbnail_tile import ReceiptTileWidget

_DEFAULT_TILE_W = 160
_DEFAULT_TILE_H = 200
_TILE_GAP = 8
_CONNECTOR_W = 40  # 接続線エリアの幅


# ===========================================================================
# TileView
# ===========================================================================

class TileView(QScrollArea):
    """グリッド状にタイルを並べるスクロールビュー（一覧・確定値編集・品質確認用）。

    set_items() でデータを渡すと列数を自動計算してタイルを配置する。
    ウィンドウリサイズ時には列数を再計算して再配置する。
    """

    item_clicked = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(_TILE_GAP)
        self._grid.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.setWidget(self._container)

        self._items: list[dict] = []
        self._api_client = None
        self._tile_w = _DEFAULT_TILE_W
        self._tile_h = _DEFAULT_TILE_H
        self._last_cols = 0

    # ------------------------------------------------------------------
    # 公開インターフェース
    # ------------------------------------------------------------------

    def set_items(
        self,
        items: list[dict],
        api_client=None,
        tile_w: int = _DEFAULT_TILE_W,
        tile_h: int = _DEFAULT_TILE_H,
    ) -> None:
        """表示データを更新してタイルを再配置する。"""
        self._items = items
        self._api_client = api_client
        self._tile_w = tile_w
        self._tile_h = tile_h
        self._last_cols = 0  # 強制再描画
        self._repopulate()

    # ------------------------------------------------------------------
    # 内部ロジック
    # ------------------------------------------------------------------

    def _repopulate(self) -> None:
        available_w = self.viewport().width()
        cols = max(1, available_w // (self._tile_w + _TILE_GAP))
        if cols == self._last_cols:
            return
        self._last_cols = cols

        # 既存タイルを削除
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, data in enumerate(self._items):
            row, col = divmod(i, cols)
            tile = ReceiptTileWidget(
                data, self._api_client, self._tile_w, self._tile_h
            )
            tile.clicked.connect(self.item_clicked.emit)
            self._grid.addWidget(tile, row, col)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._repopulate()


# ===========================================================================
# DupsTileView
# ===========================================================================

class DupsTileView(QScrollArea):
    """Dups タブ用のタイルビュー。

    左列に親タイル、右列に子タイルを配置し、QPainter で接続線を描画する。

    set_groups() でグループリストを渡す。
    グループ形式: {"parent": dict, "children": list[dict]}
    親なし（standalone）のグループは children が空リスト。
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._container = _DupsTileContainer()
        self.setWidget(self._container)

    def set_groups(
        self,
        groups: list[dict],
        api_client=None,
        tile_w: int = _DEFAULT_TILE_W,
        tile_h: int = _DEFAULT_TILE_H,
    ) -> None:
        """グループデータを渡してタイルを配置する。"""
        self._container.set_groups(groups, api_client, tile_w, tile_h)


# ---------------------------------------------------------------------------
# DupsTileView の内部コンテナ
# ---------------------------------------------------------------------------

class _DupsTileContainer(QWidget):
    """親・子タイルを QGridLayout で配置し、接続線を paintEvent で描画する。

    グリッドのカラム構成:
      col 0 – 親タイル（複数行をスパン可）
      col 1 – 接続線描画エリア（幅 _CONNECTOR_W）
      col 2 – 子タイル（1 行 1 タイル）
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setSpacing(_TILE_GAP)
        self._grid.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._connections: list[tuple[QWidget, list[QWidget]]] = []

    def set_groups(
        self,
        groups: list[dict],
        api_client,
        tile_w: int,
        tile_h: int,
    ) -> None:
        # 既存ウィジェットを削除
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._connections = []

        # 接続線エリアの列幅を固定
        self._grid.setColumnMinimumWidth(1, _CONNECTOR_W)

        grid_row = 0
        for group in groups:
            parent_data = group["parent"]
            children_data = group.get("children", [])
            row_span = max(1, len(children_data))

            parent_tile = ReceiptTileWidget(parent_data, api_client, tile_w, tile_h)
            self._grid.addWidget(parent_tile, grid_row, 0, row_span, 1)

            child_tiles: list[QWidget] = []
            for i, child_data in enumerate(children_data):
                child_tile = ReceiptTileWidget(child_data, api_client, tile_w, tile_h)
                self._grid.addWidget(child_tile, grid_row + i, 2, 1, 1)
                child_tiles.append(child_tile)

            if child_tiles:
                self._connections.append((parent_tile, child_tiles))

            # 子なし（standalone）の場合、右列は空欄の spacer ラベル
            if not child_tiles:
                spacer = QLabel()
                spacer.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )
                self._grid.addWidget(spacer, grid_row, 2)

            grid_row += row_span

        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._connections:
            return

        painter = QPainter(self)
        pen = QPen(QColor("#888888"), 2)
        painter.setPen(pen)

        for parent_tile, child_tiles in self._connections:
            # 親タイルの右中央
            p_right = parent_tile.mapTo(
                self, QPoint(parent_tile.width(), parent_tile.height() // 2)
            )

            # 接続線の折り返し X（コネクタ列の中央）
            mid_x = p_right.x() + _CONNECTOR_W // 2

            # 子タイルの左中央 Y を収集
            child_centers_y: list[int] = [
                child.mapTo(self, QPoint(0, child.height() // 2)).y()
                for child in child_tiles
            ]
            child_left_x = child_tiles[0].mapTo(self, QPoint(0, 0)).x()

            # 親 → 折り返し X（水平線）
            painter.drawLine(p_right.x(), p_right.y(), mid_x, p_right.y())

            if len(child_tiles) == 1:
                # 子が 1 つなら直接水平線
                cy = child_centers_y[0]
                painter.drawLine(mid_x, p_right.y(), mid_x, cy)
                painter.drawLine(mid_x, cy, child_left_x, cy)
            else:
                # 子が複数なら垂直線 + 各子への水平線
                first_cy = child_centers_y[0]
                last_cy = child_centers_y[-1]
                painter.drawLine(mid_x, p_right.y(), mid_x, first_cy)
                painter.drawLine(mid_x, first_cy, mid_x, last_cy)
                for cy in child_centers_y:
                    painter.drawLine(mid_x, cy, child_left_x, cy)

        painter.end()
