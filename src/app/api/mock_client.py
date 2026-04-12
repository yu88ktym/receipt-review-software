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
            "quality_level": "UNSET",
            "consistency_status": "UNSET",
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
        img["quality_level"] = "HIGH" if is_receipt and is_text_legible else "LOW"
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
