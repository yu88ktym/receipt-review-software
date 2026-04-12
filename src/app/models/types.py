from typing import TypedDict


class ImageMeta(TypedDict, total=False):
    image_id: str
    upload_id: str
    sha256: str
    original_image_url: str
    thumb_image_url: str
    duplicate_of: str | None
    dedup_hit: bool
    status: str
    quality_level: str
    integrity_status: str
    created_at: str
    updated_at: str | None
    rev: int
    # OCR結果・確定情報（ネスト構造）
    ocr_receipt_info: dict | None
    final_receipt: dict | None
    flags: list[str] | None


class IngestImageResponse(TypedDict):
    image_id: str
    upload_id: str


class SetDuplicateResponse(TypedDict):
    image_id: str
    parent_image_id: str


class UnsetDuplicateResponse(TypedDict):
    image_id: str
    parent_image_id: str


class ReverseParentResponse(TypedDict):
    old_parent_id: str
    new_parent_id: str


class ApiMetaResponse(TypedDict):
    version: str
    env: str
