from __future__ import annotations

from app.models.types import ImageMeta


def image_meta_to_row(meta: ImageMeta) -> tuple[str, ...]:
    """ImageMetaを一覧テーブル行（7列）に変換する。

    final_receipt を優先し、なければ ocr_receipt_info から値を取り出す。
    """
    image_id = meta.get("image_id", "—")
    created_at = meta.get("created_at", "—")

    final: dict = meta.get("final_receipt") or {}
    ocr: dict = meta.get("ocr_receipt_info") or {}

    purchase_date = final.get("purchased_at") or ocr.get("purchased_at") or "—"
    total_amount = (
        final["total_amount"] if "total_amount" in final and final["total_amount"] is not None
        else ocr.get("total_amount")
    )
    store_name = final.get("store_name") or ocr.get("store_name") or "—"
    payment_method = final.get("payment_method") or ocr.get("payment_method") or "—"
    status = meta.get("status", "—")

    amount_str = f"¥{total_amount:,}" if total_amount is not None else "—"

    return (image_id, created_at, purchase_date, amount_str, store_name, payment_method, status)
