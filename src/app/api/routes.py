class ApiRoutes:
    """APIエンドポイントのURL生成を一元管理するクラス。"""

    def __init__(self, base: str) -> None:
        self._base = base.rstrip("/")

    def meta(self) -> str:
        return f"{self._base}/meta"

    def images(self) -> str:
        return f"{self._base}/api/images"

    def image(self, image_id: str) -> str:
        return f"{self._base}/api/images/{image_id}"

    def image_file(self, image_id: str) -> str:
        return f"{self._base}/api/images/{image_id}/file"

    def ingest(self) -> str:
        return f"{self._base}/api/images/ingest"

    def dustbox(self, image_id: str) -> str:
        return f"{self._base}/api/images/{image_id}/dustbox"

    def finalize(self, image_id: str) -> str:
        return f"{self._base}/api/images/{image_id}/finalize"

    def duplicate(self, image_id: str) -> str:
        return f"{self._base}/api/images/{image_id}/duplicate"

    def reverse_parent(self, old_parent_id: str) -> str:
        return f"{self._base}/api/images/{old_parent_id}/reverse-parent"

    def manual_quality(self, image_id: str) -> str:
        return f"{self._base}/api/images/{image_id}/manual-quality"
