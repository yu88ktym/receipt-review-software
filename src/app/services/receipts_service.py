from __future__ import annotations

from app.api.client import ApiClient
from app.models.types import ImageMeta


class ReceiptsService:
    """レシート一覧の取得・フィルタリング・キャッシュを管理するサービス層。

    Streamlit の session_state の代わりにインスタンス変数でキャッシュを保持する。
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client
        self._cache: list[ImageMeta] | None = None
        self._etag: str = ""

    # ------------------------------------------------------------------
    # 公開インターフェース
    # ------------------------------------------------------------------

    def fetch_list(
        self,
        *,
        status: str | None = None,
        quality_level: str | None = None,
        keyword: str | None = None,
        since: str | None = None,
        until: str | None = None,
        exclude_duplicates: bool = False,
        force_refresh: bool = False,
    ) -> list[ImageMeta]:
        """フィルタ条件に応じたレシート一覧を返す。

        force_refresh が True またはキャッシュが空の場合にAPIから再取得する。
        """
        if force_refresh or self._cache is None:
            items, new_etag = self._client.list_receipts_thick(self._etag)
            if items:
                self._cache = items
                self._etag = new_etag
            elif self._cache is None:
                self._cache = []

        return self._apply_filters(
            self._cache,
            status=status,
            quality_level=quality_level,
            keyword=keyword,
            since=since,
            until=until,
            exclude_duplicates=exclude_duplicates,
        )

    def get_receipt(self, image_id: str) -> ImageMeta | None:
        """キャッシュから単一レシートを返す。キャッシュになければAPIから取得する。"""
        if self._cache is not None:
            for item in self._cache:
                if item.get("image_id") == image_id:
                    return item
        try:
            return self._client.get_image(image_id)
        except Exception:
            return None

    def invalidate_cache(self) -> None:
        """キャッシュをクリアして次回の fetch_list で強制再取得させる。"""
        self._cache = None
        self._etag = ""

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_filters(
        items: list[ImageMeta],
        *,
        status: str | None,
        quality_level: str | None,
        keyword: str | None,
        since: str | None,
        until: str | None,
        exclude_duplicates: bool,
    ) -> list[ImageMeta]:
        result = items
        if status:
            result = [r for r in result if r.get("status") == status]
        if quality_level:
            result = [r for r in result if r.get("quality_level") == quality_level]
        if keyword:
            kw = keyword.lower()
            result = [
                r for r in result
                if kw in (r.get("image_id") or "").lower()
                or kw in (_receipt_store_name(r) or "").lower()
            ]
        if since:
            result = [
                r for r in result
                if (_receipt_created_at(r) or "") >= since
            ]
        if until:
            result = [
                r for r in result
                if (_receipt_created_at(r) or "") <= until
            ]
        if exclude_duplicates:
            result = [r for r in result if not r.get("dedup_hit", False)]
        return result


def _receipt_store_name(meta: ImageMeta) -> str:
    """final_receipt → ocr_receipt_info の順で店名を返す。"""
    final: dict = meta.get("final_receipt") or {}
    ocr: dict = meta.get("ocr_receipt_info") or {}
    return final.get("store_name") or ocr.get("store_name") or meta.get("store_name") or ""


def _receipt_created_at(meta: ImageMeta) -> str:
    """created_at を返し、旧データでは upload_date にフォールバックする。"""
    return meta.get("created_at") or meta.get("upload_date") or ""
