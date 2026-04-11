"""UI ロジックのユーティリティ関数。PySide6 に依存しない純粋な Python のみを使用する。"""
from __future__ import annotations

from app.models.types import ImageMeta


def resolve_trash_button_mode(status: str) -> str:
    """画像ステータスからゴミ箱操作ボタンの表示モードを決定する。

    Returns:
        "restore" — ステータスが DROPPED の場合（復元ボタンのみ表示）
        "trash"   — それ以外（ゴミ箱へ移動ボタンのみ表示）
    """
    return "restore" if status == "DROPPED" else "trash"


def format_amount(value: int | None) -> str:
    """金額を表示用文字列に変換する。None の場合は "—" を返す。"""
    if value is None:
        return "—"
    return f"¥{value:,}"


def image_meta_to_row(item: ImageMeta) -> tuple[str, ...]:
    """ImageMeta をテーブル表示用のタプルに変換する。"""
    return (
        item.get("image_id") or "—",
        item.get("upload_date") or "—",
        item.get("purchase_date") or "—",
        format_amount(item.get("total_amount")),
        item.get("store_name") or "—",
        item.get("payment_method") or "—",
        item.get("status") or "—",
    )
