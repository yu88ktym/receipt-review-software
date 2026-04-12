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


def image_meta_to_row(meta: ImageMeta) -> tuple[str, ...]:
    """ImageMetaを一覧テーブル行（7列）に変換する。

    新形式（final/ocrネスト）を優先しつつ、旧形式（フラット）にもフォールバックする。
    """
    image_id = meta.get("image_id") or "—"
    created_at = meta.get("created_at") or meta.get("upload_date") or "—"

    final: dict = meta.get("final_receipt") or {}
    ocr: dict = meta.get("ocr_receipt_info") or {}

    purchase_date = (
        final.get("purchased_at")
        or ocr.get("purchased_at")
        or meta.get("purchase_date")
        or "—"
    )
    if "total_amount" in meta:
        total_amount = meta.get("total_amount")
    else:
        total_amount = (
            final["total_amount"] if "total_amount" in final and final["total_amount"] is not None
            else ocr.get("total_amount")
        )
    store_name = final.get("store_name") or ocr.get("store_name") or meta.get("store_name") or "—"
    payment_method = (
        final.get("payment_method")
        or ocr.get("payment_method")
        or meta.get("payment_method")
        or "—"
    )
    status = meta.get("status") or "—"

    amount_str = format_amount(total_amount)

    return (image_id, created_at, purchase_date, amount_str, store_name, payment_method, status)
