from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidget

# 画像ステータスごとのデフォルト行背景色（16進数カラーコード）
STATUS_COLORS: dict[str, str] = {
    "INGESTED":            "#FFFFFF",
    "OCR_DONE":            "#E3F2FD",
    "FINAL_UPDATED":       "#E8F5E9",
    "DROPPED":             "#FFEBEE",
    "NOT_RECEIPT_SUSPECT": "#FFF8E1",
    # 旧ステータス互換
    "REVIEWED":            "#E3F2FD",
    "PENDING":             "#FFFFFF",
}


def get_row_color(status: str) -> QColor:
    """ステータス文字列から行背景色を返す。
    未登録ステータスおよび空文字列の場合は白（#FFFFFF）を返す。
    """
    return QColor(STATUS_COLORS.get(status, "#FFFFFF"))


def apply_row_colors(table: QTableWidget, status_col: int) -> None:
    """テーブル全行のうち status_col 列の値に応じて行全体の背景色を設定する。"""
    for row in range(table.rowCount()):
        status_item = table.item(row, status_col)
        status = status_item.text() if status_item else ""
        color = get_row_color(status)
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item is not None:
                item.setBackground(color)
