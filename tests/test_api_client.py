import pytest
import requests

from app.api.client import ApiClient
from app.config.env import API_BASE, API_KEY
from app.api.routes import ApiRoutes


_ROUTES = ApiRoutes(API_BASE)


# -----------------------------------------------------------------------
# get_meta
# -----------------------------------------------------------------------

def test_get_meta_success(api_client: ApiClient, requests_mock) -> None:
    requests_mock.get(_ROUTES.meta(), json={"version": "1.0.0", "env": "test"})
    result = api_client.get_meta()
    assert result["version"] == "1.0.0"
    assert result["env"] == "test"


def test_get_meta_server_error(api_client: ApiClient, requests_mock) -> None:
    requests_mock.get(_ROUTES.meta(), status_code=500)
    with pytest.raises(requests.HTTPError):
        api_client.get_meta()


# -----------------------------------------------------------------------
# list_receipts
# -----------------------------------------------------------------------

def test_list_receipts_success(api_client: ApiClient, requests_mock) -> None:
    payload = [
        {"image_id": "R-0001", "status": "INGESTED"},
        {"image_id": "R-0002", "status": "FINAL_UPDATED"},
    ]
    requests_mock.get(_ROUTES.images(), json=payload)
    items = api_client.list_receipts()
    assert len(items) == 2
    assert items[0]["image_id"] == "R-0001"


def test_list_receipts_empty(api_client: ApiClient, requests_mock) -> None:
    requests_mock.get(_ROUTES.images(), json=[])
    items = api_client.list_receipts()
    assert items == []


# -----------------------------------------------------------------------
# list_receipts_thick（ETag）
# -----------------------------------------------------------------------

def test_list_receipts_thick_no_etag(api_client: ApiClient, requests_mock) -> None:
    payload = [{"image_id": "R-0001", "status": "INGESTED"}]
    requests_mock.get(
        _ROUTES.images(),
        json=payload,
        headers={"ETag": "etag-v1"},
    )
    items, new_etag = api_client.list_receipts_thick()
    assert len(items) == 1
    assert new_etag == "etag-v1"


def test_list_receipts_thick_304(api_client: ApiClient, requests_mock) -> None:
    requests_mock.get(_ROUTES.images(), status_code=304)
    items, returned_etag = api_client.list_receipts_thick(etag="etag-v1")
    assert items == []
    assert returned_etag == "etag-v1"


# -----------------------------------------------------------------------
# get_image
# -----------------------------------------------------------------------

def test_get_image_success(api_client: ApiClient, requests_mock) -> None:
    image_id = "R-0001"
    requests_mock.get(
        _ROUTES.image(image_id),
        json={"image_id": image_id, "status": "FINAL_UPDATED"},
    )
    result = api_client.get_image(image_id)
    assert result["image_id"] == image_id


def test_get_image_not_found(api_client: ApiClient, requests_mock) -> None:
    requests_mock.get(_ROUTES.image("MISSING"), status_code=404)
    with pytest.raises(requests.HTTPError):
        api_client.get_image("MISSING")


# -----------------------------------------------------------------------
# get_image_file
# -----------------------------------------------------------------------

def test_get_image_file_success(api_client: ApiClient, requests_mock) -> None:
    image_id = "R-0001"
    adapter = requests_mock.get(
        _ROUTES.image_file(image_id),
        content=b"\xff\xd8\xff",
    )
    data = api_client.get_image_file(image_id, "original")
    assert data == b"\xff\xd8\xff"
    assert adapter.last_request.qs == {"variant": ["original"]}


# -----------------------------------------------------------------------
# ingest_image
# -----------------------------------------------------------------------

def test_ingest_image_success(api_client: ApiClient, requests_mock) -> None:
    requests_mock.post(
        _ROUTES.ingest(),
        json={"image_id": "R-NEW", "upload_id": "UP-001"},
        status_code=201,
    )
    result = api_client.ingest_image(b"fakebytes", "UP-001")
    assert result["image_id"] == "R-NEW"


# -----------------------------------------------------------------------
# move_to_dustbox / restore_from_dustbox
# -----------------------------------------------------------------------

def test_move_to_dustbox(api_client: ApiClient, requests_mock) -> None:
    requests_mock.post(_ROUTES.dustbox("R-0001"), status_code=204)
    api_client.move_to_dustbox("R-0001")  # 例外なし


def test_restore_from_dustbox(api_client: ApiClient, requests_mock) -> None:
    requests_mock.delete(_ROUTES.dustbox("R-0001"), status_code=204)
    api_client.restore_from_dustbox("R-0001")  # 例外なし


# -----------------------------------------------------------------------
# finalize_receipt / revise_final_receipt
# -----------------------------------------------------------------------

def test_finalize_receipt(api_client: ApiClient, requests_mock) -> None:
    image_id = "R-0001"
    body = {"store_name": "コンビニA", "total_amount": 3200}
    requests_mock.post(
        _ROUTES.finalize(image_id),
        json={"image_id": image_id, "status": "FINAL_UPDATED", **body},
    )
    result = api_client.finalize_receipt(image_id, body)
    assert result["status"] == "FINAL_UPDATED"


def test_revise_final_receipt(api_client: ApiClient, requests_mock) -> None:
    image_id = "R-0001"
    body = {"total_amount": 4000}
    requests_mock.put(
        _ROUTES.finalize(image_id),
        json={"image_id": image_id, "status": "FINAL_UPDATED", **body},
    )
    result = api_client.revise_final_receipt(image_id, body)
    assert result["total_amount"] == 4000


# -----------------------------------------------------------------------
# set_duplicate / unset_duplicate
# -----------------------------------------------------------------------

def test_set_duplicate(api_client: ApiClient, requests_mock) -> None:
    requests_mock.post(
        _ROUTES.duplicate("R-0002"),
        json={"image_id": "R-0002", "parent_image_id": "R-0001"},
    )
    result = api_client.set_duplicate("R-0002", "R-0001")
    assert result["parent_image_id"] == "R-0001"


def test_unset_duplicate(api_client: ApiClient, requests_mock) -> None:
    requests_mock.delete(
        _ROUTES.duplicate("R-0002"),
        json={"image_id": "R-0002", "parent_image_id": "R-0001"},
    )
    result = api_client.unset_duplicate("R-0002", "R-0001")
    assert result["image_id"] == "R-0002"


# -----------------------------------------------------------------------
# reverse_parent
# -----------------------------------------------------------------------

def test_reverse_parent(api_client: ApiClient, requests_mock) -> None:
    requests_mock.post(
        _ROUTES.reverse_parent(),
        json={"old_parent_id": "R-0001", "new_parent_id": "R-0002"},
    )
    result = api_client.reverse_parent("R-0001", "R-0002")
    assert result["new_parent_id"] == "R-0002"


# -----------------------------------------------------------------------
# update_manual_quality
# -----------------------------------------------------------------------

def test_update_manual_quality(api_client: ApiClient, requests_mock) -> None:
    image_id = "R-0001"
    requests_mock.post(
        _ROUTES.manual_quality(image_id),
        json={"image_id": image_id, "quality_level": "HIGH"},
    )
    result = api_client.update_manual_quality(image_id, True, True)
    assert result["quality_level"] == "HIGH"
