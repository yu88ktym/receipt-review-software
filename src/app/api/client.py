from __future__ import annotations

import requests

from app.api.routes import ApiRoutes
from app.models.types import (
    ApiMetaResponse,
    ImageMeta,
    IngestImageResponse,
    ReverseParentResponse,
    SetDuplicateResponse,
    UnsetDuplicateResponse,
)

_ETAG_NONE = ""


class ApiClient:
    """APIサーバとのHTTP通信を担うクライアント。"""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._routes = ApiRoutes(base_url)
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": api_key})
        # サムネイル等の画像バイナリをセッション中にキャッシュする
        self._image_cache: dict[tuple[str, str], bytes] = {}

    # ------------------------------------------------------------------
    # メタ情報
    # ------------------------------------------------------------------

    def get_meta(self) -> ApiMetaResponse:
        resp = self._session.get(self._routes.meta())
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # 一覧取得
    # ------------------------------------------------------------------

    def list_receipts(self) -> list[ImageMeta]:
        resp = self._session.get(self._routes.images())
        resp.raise_for_status()
        return resp.json()

    def list_receipts_thick(
        self, etag: str = _ETAG_NONE
    ) -> tuple[list[ImageMeta], str]:
        """ETag を用いた条件付き一覧取得。

        Returns:
            (items, new_etag) のタプル。
            サーバが 304 を返した場合は ([], etag) を返す。
        """
        headers: dict[str, str] = {}
        if etag:
            headers["If-None-Match"] = etag
        resp = self._session.get(self._routes.images(), headers=headers)
        if resp.status_code == 304:
            return [], etag
        resp.raise_for_status()
        new_etag = resp.headers.get("ETag", _ETAG_NONE)
        data = resp.json()
        # APIレスポンスが {"items": [...]} 形式の場合は items を取り出す
        if isinstance(data, dict) and "items" in data:
            return data["items"], new_etag
        return data, new_etag

    # ------------------------------------------------------------------
    # 単一画像
    # ------------------------------------------------------------------

    def get_image(self, image_id: str) -> ImageMeta:
        resp = self._session.get(self._routes.image(image_id))
        resp.raise_for_status()
        return resp.json()

    def get_image_file(self, image_id: str, variant: str = "thumb") -> bytes:
        """画像バイナリを取得する。variant は "original" / "thumb" 等。

        同一 (image_id, variant) の結果はインメモリキャッシュから返す。
        """
        key = (image_id, variant)
        if key in self._image_cache:
            return self._image_cache[key]
        resp = self._session.get(
            self._routes.image_file(image_id),
            params={"variant": variant},
        )
        resp.raise_for_status()
        data = resp.content
        self._image_cache[key] = data
        return data

    # ------------------------------------------------------------------
    # 登録・更新
    # ------------------------------------------------------------------

    def ingest_image(
        self, image_bytes: bytes, upload_id: str
    ) -> IngestImageResponse:
        resp = self._session.post(
            self._routes.ingest(),
            files={"file": image_bytes},
            data={"upload_id": upload_id},
        )
        resp.raise_for_status()
        return resp.json()

    def move_to_dustbox(self, image_id: str) -> None:
        resp = self._session.post(self._routes.dustbox(image_id))
        resp.raise_for_status()

    def restore_from_dustbox(self, image_id: str) -> None:
        resp = self._session.delete(self._routes.dustbox(image_id))
        resp.raise_for_status()

    def finalize_receipt(self, image_id: str, body: dict) -> ImageMeta:
        resp = self._session.post(self._routes.finalize(image_id), json=body)
        resp.raise_for_status()
        return resp.json()

    def revise_final_receipt(self, image_id: str, body: dict) -> ImageMeta:
        resp = self._session.put(self._routes.finalize(image_id), json=body)
        resp.raise_for_status()
        return resp.json()

    def set_duplicate(
        self, image_id: str, parent_id: str
    ) -> SetDuplicateResponse:
        resp = self._session.post(
            self._routes.duplicate(image_id), json={"parent_image_id": parent_id}
        )
        resp.raise_for_status()
        return resp.json()

    def unset_duplicate(
        self, image_id: str, parent_id: str
    ) -> UnsetDuplicateResponse:
        resp = self._session.delete(
            self._routes.duplicate(image_id),
            json={"parent_image_id": parent_id},
        )
        resp.raise_for_status()
        return resp.json()

    def reverse_parent(
        self, old_parent_id: str, new_parent_id: str
    ) -> ReverseParentResponse:
        resp = self._session.post(
            self._routes.reverse_parent(),
            json={"old_parent_id": old_parent_id, "new_parent_id": new_parent_id},
        )
        resp.raise_for_status()
        return resp.json()

    def update_manual_quality(
        self,
        image_id: str,
        is_receipt: bool,
        is_text_legible: bool,
    ) -> ImageMeta:
        resp = self._session.post(
            self._routes.manual_quality(image_id),
            json={"is_receipt": is_receipt, "is_text_legible": is_text_legible},
        )
        resp.raise_for_status()
        return resp.json()
