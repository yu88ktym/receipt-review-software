from __future__ import annotations

import copy
import uuid

from app.models.types import (
    ApiMetaResponse,
    ImageMeta,
    IngestImageResponse,
    ReverseParentResponse,
    SetDuplicateResponse,
    UnsetDuplicateResponse,
)
from app.api.mock_data import DUMMY_IMAGES, DUMMY_META


class MockApiClient:
    """ApiClient と同一インターフェースを持つインメモリ実装。

    USE_MOCK=true のとき実際のAPIサーバへ接続せずに動作確認ができる。
    """

    def __init__(self) -> None:
        self._images: list[ImageMeta] = [copy.deepcopy(img) for img in DUMMY_IMAGES]
        self._meta: ApiMetaResponse = copy.deepcopy(DUMMY_META)
        self._etag: str = "initial-etag"

    # ------------------------------------------------------------------
    # メタ情報
    # ------------------------------------------------------------------

    def get_meta(self) -> ApiMetaResponse:
        return copy.deepcopy(self._meta)

    # ------------------------------------------------------------------
    # 一覧取得
    # ------------------------------------------------------------------

    def list_receipts(self) -> list[ImageMeta]:
        return copy.deepcopy(self._images)

    def list_receipts_thick(
        self, etag: str = ""
    ) -> tuple[list[ImageMeta], str]:
        if etag == self._etag:
            return [], etag
        return copy.deepcopy(self._images), self._etag

    # ------------------------------------------------------------------
    # 単一画像
    # ------------------------------------------------------------------

    def get_image(self, image_id: str) -> ImageMeta:
        for img in self._images:
            if img["image_id"] == image_id:
                return copy.deepcopy(img)
        raise KeyError(f"image_id={image_id!r} not found")

    def get_image_file(self, image_id: str, variant: str) -> bytes:
        # モック用に空のバイト列を返す
        return b""

    # ------------------------------------------------------------------
    # 登録・更新
    # ------------------------------------------------------------------

    def ingest_image(
        self, image_bytes: bytes, upload_id: str
    ) -> IngestImageResponse:
        new_id = f"R-{uuid.uuid4().hex[:6].upper()}"
        img: ImageMeta = {
            "image_id": new_id,
            "upload_date": "",
            "purchase_date": None,
            "total_amount": None,
            "store_name": None,
            "payment_method": None,
            "status": "INGESTED",
            "quality_level": "UNKNOWN",
            "consistency_status": "NO_APPROACH",
            "is_duplicate": False,
            "parent_image_id": None,
            "etag": None,
        }
        self._images.append(img)
        self._etag = uuid.uuid4().hex
        return {"image_id": new_id, "upload_id": upload_id}

    def move_to_dustbox(self, image_id: str) -> None:
        self._update_status(image_id, "DROPPED")

    def restore_from_dustbox(self, image_id: str) -> None:
        self._update_status(image_id, "INGESTED")

    def finalize_receipt(self, image_id: str, body: dict) -> ImageMeta:
        img = self._find(image_id)
        img.update(body)
        img["status"] = "FINAL_UPDATED"
        return copy.deepcopy(img)

    def revise_final_receipt(self, image_id: str, body: dict) -> ImageMeta:
        img = self._find(image_id)
        img.update(body)
        return copy.deepcopy(img)

    def set_duplicate(
        self, image_id: str, parent_id: str
    ) -> SetDuplicateResponse:
        img = self._find(image_id)
        img["is_duplicate"] = True
        img["parent_image_id"] = parent_id
        return {"image_id": image_id, "parent_image_id": parent_id}

    def unset_duplicate(
        self, image_id: str, parent_id: str
    ) -> UnsetDuplicateResponse:
        img = self._find(image_id)
        img["is_duplicate"] = False
        img["parent_image_id"] = None
        return {"image_id": image_id, "parent_image_id": parent_id}

    def reverse_parent(
        self, old_parent_id: str, new_parent_id: str
    ) -> ReverseParentResponse:
        return {"old_parent_id": old_parent_id, "new_parent_id": new_parent_id}

    def update_manual_quality(
        self,
        image_id: str,
        is_receipt: bool,
        is_text_legible: bool,
    ) -> ImageMeta:
        img = self._find(image_id)
        img["quality_level"] = "NO_PROBLEM" if is_receipt and is_text_legible else "LOW"
        return copy.deepcopy(img)

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _find(self, image_id: str) -> ImageMeta:
        for img in self._images:
            if img["image_id"] == image_id:
                return img
        raise KeyError(f"image_id={image_id!r} not found")

    def _update_status(self, image_id: str, status: str) -> None:
        img = self._find(image_id)
        img["status"] = status
        self._etag = uuid.uuid4().hex
from __future__ import annotations

import copy
import uuid

from app.models.types import (
    ApiMetaResponse,
    ImageMeta,
    IngestImageResponse,
    ReverseParentResponse,
    SetDuplicateResponse,
    UnsetDuplicateResponse,
)

_DUMMY_IMAGES: list[ImageMeta] = [
    {
        "image_id": "R-0001",
        "created_at": "2024-01-15",
        "status": "FINAL_UPDATED",
        "quality_level": "NO_PROBLEM",
        "integrity_status": "OK",
        "dedup_hit": False,
        "duplicate_of": None,
        "original_image_url": "gs://bucket/R-0001/original.jpg",
        "thumb_image_url": "gs://bucket/R-0001/thumb.jpg",
        "final_receipt": {
            "purchased_at": "2024-01-14",
            "total_amount": 3200,
            "store_name": "コンビニA",
            "payment_method": "現金",
        },
        "ocr_receipt_info": None,
    },
    {
        "image_id": "R-0002",
        "created_at": "2024-01-16",
        "status": "OCR_DONE",
        "quality_level": "OCR_LOW",
        "integrity_status": "NO_APPROACH",
        "dedup_hit": False,
        "duplicate_of": None,
        "original_image_url": "gs://bucket/R-0002/original.jpg",
        "thumb_image_url": "gs://bucket/R-0002/thumb.jpg",
        "ocr_receipt_info": {
            "purchased_at": "2024-01-15",
            "total_amount": 1500,
            "store_name": "スーパーB",
            "payment_method": "クレジット",
        },
        "final_receipt": None,
    },
    {
        "image_id": "R-0003",
        "created_at": "2024-01-17",
        "status": "INGESTED",
        "quality_level": "LOW",
        "integrity_status": "NO_APPROACH",
        "dedup_hit": False,
        "duplicate_of": None,
        "original_image_url": "gs://bucket/R-0003/original.jpg",
        "thumb_image_url": "gs://bucket/R-0003/thumb.jpg",
        "ocr_receipt_info": {
            "purchased_at": "2024-01-16",
            "total_amount": 8400,
            "store_name": "レストランC",
            "payment_method": "電子マネー",
        },
        "final_receipt": None,
    },
    {
        "image_id": "R-0004",
        "created_at": "2024-01-18",
        "status": "OCR_FAILED",
        "quality_level": "UNKNOWN",
        "integrity_status": "NO_APPROACH",
        "dedup_hit": True,
        "duplicate_of": "R-0003",
        "original_image_url": "gs://bucket/R-0004/original.jpg",
        "thumb_image_url": "gs://bucket/R-0004/thumb.jpg",
        "ocr_receipt_info": {
            "purchased_at": "2024-01-17",
            "total_amount": 640,
            "store_name": "カフェD",
            "payment_method": "現金",
        },
        "final_receipt": None,
    },
    {
        "image_id": "R-0005",
        "created_at": "2024-01-19",
        "status": "DROPPED",
        "quality_level": "NO_PROBLEM",
        "integrity_status": "OK",
        "dedup_hit": False,
        "duplicate_of": None,
        "original_image_url": "gs://bucket/R-0005/original.jpg",
        "thumb_image_url": "gs://bucket/R-0005/thumb.jpg",
        "final_receipt": {
            "purchased_at": "2024-01-18",
            "total_amount": 12000,
            "store_name": "百貨店E",
            "payment_method": "クレジット",
        },
        "ocr_receipt_info": None,
    },
    {
        "image_id": "R-0006",
        "created_at": "2024-01-20",
        "status": "FINAL_UPDATED_CHILD",
        "quality_level": "NO_PROBLEM",
        "integrity_status": "IGNORED",
        "dedup_hit": False,
        "duplicate_of": None,
        "original_image_url": "gs://bucket/R-0006/original.jpg",
        "thumb_image_url": "gs://bucket/R-0006/thumb.jpg",
        "final_receipt": {
            "purchased_at": "2024-01-19",
            "total_amount": 5500,
            "store_name": "薬局F",
            "payment_method": "電子マネー",
        },
        "ocr_receipt_info": None,
    },
]

_DUMMY_META: ApiMetaResponse = {
    "version": "0.1.0-mock",
    "env": "mock",
}


class MockApiClient:
    """ApiClientと同一インターフェースを持つインメモリ実装（本番モック用）。

    USE_MOCK=true のときに使用される。実際のAPIサーバへ接続しない。
    """

    def __init__(self) -> None:
        self._images: list[ImageMeta] = [copy.deepcopy(img) for img in _DUMMY_IMAGES]
        self._meta: ApiMetaResponse = copy.deepcopy(_DUMMY_META)
        self._etag: str = "initial-etag"

    # ------------------------------------------------------------------
    # メタ情報
    # ------------------------------------------------------------------

    def get_meta(self) -> ApiMetaResponse:
        return copy.deepcopy(self._meta)

    # ------------------------------------------------------------------
    # 一覧取得
    # ------------------------------------------------------------------

    def list_receipts(self) -> list[ImageMeta]:
        return copy.deepcopy(self._images)

    def list_receipts_thick(self, etag: str = "") -> tuple[list[ImageMeta], str]:
        if etag == self._etag:
            return [], etag
        return copy.deepcopy(self._images), self._etag

    # ------------------------------------------------------------------
    # 単一画像
    # ------------------------------------------------------------------

    def get_image(self, image_id: str) -> ImageMeta:
        for img in self._images:
            if img["image_id"] == image_id:
                return copy.deepcopy(img)
        raise KeyError(f"image_id={image_id!r} not found")

    def get_image_file(self, image_id: str, variant: str) -> bytes:
        return b""

    # ------------------------------------------------------------------
    # 登録・更新
    # ------------------------------------------------------------------

    def ingest_image(self, image_bytes: bytes, upload_id: str, filename: str = "upload.jpg") -> IngestImageResponse:
        new_id = f"R-{uuid.uuid4().hex[:6].upper()}"
        img: ImageMeta = {
            "image_id": new_id,
            "created_at": "",
            "status": "INGESTED",
            "quality_level": "UNKNOWN",
            "integrity_status": "NO_APPROACH",
            "dedup_hit": False,
            "duplicate_of": None,
            "ocr_receipt_info": None,
            "final_receipt": None,
        }
        self._images.append(img)
        self._etag = uuid.uuid4().hex
        return {"image_id": new_id, "upload_id": upload_id}

    def move_to_dustbox(self, image_id: str) -> None:
        self._update_status(image_id, "DROPPED")

    def restore_from_dustbox(self, image_id: str) -> None:
        self._update_status(image_id, "INGESTED")

    def finalize_receipt(self, image_id: str, body: dict) -> ImageMeta:
        img = self._find(image_id)
        img["final_receipt"] = body
        img["status"] = "FINAL_UPDATED"
        return copy.deepcopy(img)

    def revise_final_receipt(self, image_id: str, body: dict) -> ImageMeta:
        img = self._find(image_id)
        if img.get("final_receipt"):
            img["final_receipt"].update(body)
        else:
            img["final_receipt"] = body
        return copy.deepcopy(img)

    def set_duplicate(self, image_id: str, parent_id: str) -> SetDuplicateResponse:
        img = self._find(image_id)
        img["dedup_hit"] = True
        img["duplicate_of"] = parent_id
        return {"image_id": image_id, "parent_image_id": parent_id}

    def unset_duplicate(self, image_id: str, parent_id: str) -> UnsetDuplicateResponse:
        img = self._find(image_id)
        img["dedup_hit"] = False
        img["duplicate_of"] = None
        return {"image_id": image_id, "parent_image_id": parent_id}

    def reverse_parent(self, old_parent_id: str, new_parent_id: str) -> ReverseParentResponse:
        return {"old_parent_id": old_parent_id, "new_parent_id": new_parent_id}

    def update_manual_quality(
        self, image_id: str, is_receipt: bool, is_text_legible: bool
    ) -> ImageMeta:
        img = self._find(image_id)
        img["quality_level"] = "NO_PROBLEM" if is_receipt and is_text_legible else "LOW"
        return copy.deepcopy(img)

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _find(self, image_id: str) -> ImageMeta:
        for img in self._images:
            if img["image_id"] == image_id:
                return img
        raise KeyError(f"image_id={image_id!r} not found")

    def _update_status(self, image_id: str, status: str) -> None:
        img = self._find(image_id)
        img["status"] = status
        self._etag = uuid.uuid4().hex
