from PySide6.QtGui import QColor

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
    """ステータス文字列から行背景色を返す。未登録ステータスは白を返す。"""
    return QColor(STATUS_COLORS.get(status, "#FFFFFF"))
