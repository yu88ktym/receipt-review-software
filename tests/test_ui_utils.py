import pytest

from app.ui.ui_utils import image_meta_to_row
from app.models.types import ImageMeta


def _make_meta(**kwargs) -> ImageMeta:
    base: ImageMeta = {
        "image_id": "R-TEST",
        "created_at": "2024-03-01",
        "status": "INGESTED",
        "quality_level": "HIGH",
        "integrity_status": "OK",
    }
    base.update(kwargs)  # type: ignore[typeddict-item]
    return base


# -----------------------------------------------------------------------
# image_meta_to_row
# -----------------------------------------------------------------------

def test_row_uses_final_receipt_when_available() -> None:
    meta = _make_meta(
        final_receipt={
            "purchased_at": "2024-03-01",
            "total_amount": 1000,
            "store_name": "テスト店",
            "payment_method": "現金",
        },
        ocr_receipt_info={
            "purchased_at": "2024-02-28",
            "total_amount": 999,
            "store_name": "OCR店",
            "payment_method": "クレジット",
        },
    )
    row = image_meta_to_row(meta)
    assert row[0] == "R-TEST"           # image_id
    assert row[1] == "2024-03-01"       # created_at
    assert row[2] == "2024-03-01"       # purchased_at from final_receipt
    assert row[3] == "¥1,000"           # total_amount from final_receipt
    assert row[4] == "テスト店"          # store_name from final_receipt
    assert row[5] == "現金"              # payment_method from final_receipt
    assert row[6] == "INGESTED"         # status


def test_row_falls_back_to_ocr_when_no_final() -> None:
    meta = _make_meta(
        final_receipt=None,
        ocr_receipt_info={
            "purchased_at": "2024-02-28",
            "total_amount": 500,
            "store_name": "OCR店",
            "payment_method": "電子マネー",
        },
    )
    row = image_meta_to_row(meta)
    assert row[2] == "2024-02-28"
    assert row[3] == "¥500"
    assert row[4] == "OCR店"
    assert row[5] == "電子マネー"


def test_row_shows_dash_when_no_receipt_info() -> None:
    meta = _make_meta(final_receipt=None, ocr_receipt_info=None)
    row = image_meta_to_row(meta)
    assert row[2] == "—"    # purchased_at
    assert row[3] == "—"    # total_amount
    assert row[4] == "—"    # store_name
    assert row[5] == "—"    # payment_method


def test_row_formats_amount_with_comma() -> None:
    meta = _make_meta(
        final_receipt={"total_amount": 12345, "purchased_at": "2024-01-01",
                       "store_name": "店", "payment_method": "現金"}
    )
    row = image_meta_to_row(meta)
    assert row[3] == "¥12,345"


def test_row_missing_image_id_shows_dash() -> None:
    meta: ImageMeta = {"status": "INGESTED"}
    row = image_meta_to_row(meta)
    assert row[0] == "—"    # image_id
    assert row[1] == "—"    # created_at
    assert row[2] == "—"    # purchased_at
    assert row[3] == "—"    # total_amount
    assert row[4] == "—"    # store_name
    assert row[5] == "—"    # payment_method


def test_row_zero_amount_displays_correctly() -> None:
    """金額が0円の場合でも「—」にならず「¥0」と表示されること。"""
    meta = _make_meta(
        final_receipt={"total_amount": 0, "purchased_at": "2024-01-01",
                       "store_name": "店", "payment_method": "現金"},
        ocr_receipt_info={"total_amount": 999, "store_name": "OCR店"},
    )
    row = image_meta_to_row(meta)
    assert row[3] == "¥0"
