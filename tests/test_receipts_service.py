import pytest

from app.services.receipts_service import ReceiptsService
from tests.mocks.mock_api_client import MockApiClient


@pytest.fixture
def mock_client() -> MockApiClient:
    return MockApiClient()


@pytest.fixture
def service(mock_client: MockApiClient) -> ReceiptsService:
    return ReceiptsService(mock_client)  # type: ignore[arg-type]


# -----------------------------------------------------------------------
# fetch_list — 基本取得
# -----------------------------------------------------------------------

def test_fetch_list_returns_all(service: ReceiptsService) -> None:
    items = service.fetch_list()
    assert len(items) == 5


def test_fetch_list_caches_result(service: ReceiptsService, mock_client: MockApiClient) -> None:
    service.fetch_list()
    # 2回目は ETag が一致するためモックが空リストを返し、キャッシュが再利用される
    items = service.fetch_list()
    assert len(items) == 5


# -----------------------------------------------------------------------
# fetch_list — フィルタ: ステータス
# -----------------------------------------------------------------------

def test_fetch_list_filter_status(service: ReceiptsService) -> None:
    items = service.fetch_list(status="FINAL_UPDATED")
    assert all(i["status"] == "FINAL_UPDATED" for i in items)
    assert len(items) == 1


def test_fetch_list_filter_status_no_match(service: ReceiptsService) -> None:
    items = service.fetch_list(status="NOT_RECEIPT_SUSPECT")
    assert items == []


# -----------------------------------------------------------------------
# fetch_list — フィルタ: 品質レベル
# -----------------------------------------------------------------------

def test_fetch_list_filter_quality(service: ReceiptsService) -> None:
    items = service.fetch_list(quality_level="HIGH")
    assert all(i["quality_level"] == "HIGH" for i in items)


# -----------------------------------------------------------------------
# fetch_list — フィルタ: キーワード（店名）
# -----------------------------------------------------------------------

def test_fetch_list_filter_keyword_store(service: ReceiptsService) -> None:
    items = service.fetch_list(keyword="コンビニ")
    assert len(items) == 1
    assert items[0]["store_name"] == "コンビニA"


def test_fetch_list_filter_keyword_image_id(service: ReceiptsService) -> None:
    items = service.fetch_list(keyword="r-0003")
    assert len(items) == 1
    assert items[0]["image_id"] == "R-0003"


# -----------------------------------------------------------------------
# fetch_list — フィルタ: 日付範囲
# -----------------------------------------------------------------------

def test_fetch_list_filter_since(service: ReceiptsService) -> None:
    items = service.fetch_list(since="2024-01-18")
    assert all(i["upload_date"] >= "2024-01-18" for i in items)


def test_fetch_list_filter_until(service: ReceiptsService) -> None:
    items = service.fetch_list(until="2024-01-16")
    assert all(i["upload_date"] <= "2024-01-16" for i in items)


def test_fetch_list_filter_date_range(service: ReceiptsService) -> None:
    items = service.fetch_list(since="2024-01-16", until="2024-01-17")
    assert len(items) == 2


# -----------------------------------------------------------------------
# fetch_list — フィルタ: 重複除外
# -----------------------------------------------------------------------

def test_fetch_list_exclude_duplicates(service: ReceiptsService) -> None:
    items = service.fetch_list(exclude_duplicates=True)
    assert all(not i.get("is_duplicate", False) for i in items)


# -----------------------------------------------------------------------
# fetch_list — force_refresh
# -----------------------------------------------------------------------

def test_fetch_list_force_refresh(service: ReceiptsService, mock_client: MockApiClient) -> None:
    service.fetch_list()
    # 強制リフレッシュ時は ETag をリセットして再取得する
    service.invalidate_cache()
    items = service.fetch_list(force_refresh=True)
    assert len(items) == 5


# -----------------------------------------------------------------------
# get_receipt
# -----------------------------------------------------------------------

def test_get_receipt_found_in_cache(service: ReceiptsService) -> None:
    service.fetch_list()
    item = service.get_receipt("R-0001")
    assert item is not None
    assert item["image_id"] == "R-0001"


def test_get_receipt_from_api_if_no_cache(mock_client: MockApiClient) -> None:
    # キャッシュ未ロードの状態
    svc = ReceiptsService(mock_client)  # type: ignore[arg-type]
    item = svc.get_receipt("R-0002")
    assert item is not None
    assert item["image_id"] == "R-0002"


def test_get_receipt_not_found(service: ReceiptsService) -> None:
    item = service.get_receipt("NONEXISTENT")
    assert item is None


# -----------------------------------------------------------------------
# invalidate_cache
# -----------------------------------------------------------------------

def test_invalidate_cache_forces_reload(service: ReceiptsService) -> None:
    service.fetch_list()
    service.invalidate_cache()
    # キャッシュクリア後は再取得する
    items = service.fetch_list()
    assert len(items) == 5
