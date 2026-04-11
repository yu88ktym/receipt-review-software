from typing import TypedDict


class ImageMeta(TypedDict, total=False):
    image_id: str
    upload_date: str
    purchase_date: str
    total_amount: int | None
    store_name: str | None
    payment_method: str | None
    status: str
    quality_level: str
    consistency_status: str
    is_duplicate: bool
    parent_image_id: str | None
    etag: str | None


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
