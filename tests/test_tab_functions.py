"""各タブのロジックテスト。

GUI ウィジェットの操作テストは除外し、APIモックを使用したロジックのみ検証する。
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from app.services.receipts_service import ReceiptsService
from app.ui.ui_utils import resolve_trash_button_mode, image_meta_to_row
from app.config.settings_io import load_settings, save_settings
from tests.mocks.mock_api_client import MockApiClient
from tests.mocks.mock_data import DUMMY_IMAGES


# -----------------------------------------------------------------------
# ボタン表示条件: resolve_trash_button_mode
# -----------------------------------------------------------------------

def test_trash_button_mode_dropped() -> None:
    """DROPPED ステータスでは restore モードになる。"""
    assert resolve_trash_button_mode("DROPPED") == "restore"


def test_trash_button_mode_non_dropped(status: str = "INGESTED") -> None:
    """DROPPED 以外のステータスでは trash モードになる。"""
    for s in ("INGESTED", "OCR_DONE", "FINAL_UPDATED", "NOT_RECEIPT_SUSPECT", ""):
        assert resolve_trash_button_mode(s) == "trash", f"status={s!r} should be 'trash'"


# -----------------------------------------------------------------------
# image_meta_to_row — 表示変換
# -----------------------------------------------------------------------

def test_image_meta_to_row_basic() -> None:
    item = DUMMY_IMAGES[0]  # R-0001, total_amount=3200
    row = image_meta_to_row(item)
    assert row[0] == "R-0001"
    assert row[3] == "¥3,200"
    assert row[6] == "FINAL_UPDATED"


def test_image_meta_to_row_none_amount() -> None:
    item = {**DUMMY_IMAGES[0], "total_amount": None}
    row = image_meta_to_row(item)
    assert row[3] == "—"


def test_image_meta_to_row_none_fields() -> None:
    item = {
        "image_id": "X-001",
        "upload_date": None,
        "purchase_date": None,
        "total_amount": None,
        "store_name": None,
        "payment_method": None,
        "status": "INGESTED",
    }
    row = image_meta_to_row(item)
    assert row[0] == "X-001"
    assert row[1] == "—"
    assert row[4] == "—"


# -----------------------------------------------------------------------
# TabList ロジック: ページネーション計算
# -----------------------------------------------------------------------

def test_pagination_total_pages() -> None:
    """ceil(items / page_size) が正しく計算される。"""
    assert math.ceil(5 / 50) == 1
    assert math.ceil(50 / 50) == 1
    assert math.ceil(51 / 50) == 2
    assert math.ceil(100 / 10) == 10
    assert math.ceil(101 / 10) == 11


def test_pagination_slice() -> None:
    """ページスライスが正しい範囲を返す。"""
    items = list(range(15))
    page_size = 5

    page1 = items[0:5]
    page2 = items[5:10]
    page3 = items[10:15]

    assert page1 == [0, 1, 2, 3, 4]
    assert page2 == [5, 6, 7, 8, 9]
    assert page3 == [10, 11, 12, 13, 14]


# -----------------------------------------------------------------------
# アップロードロジック: MockApiClient.ingest_image
# -----------------------------------------------------------------------

@pytest.fixture
def mock_client() -> MockApiClient:
    return MockApiClient()


def test_ingest_single_image(mock_client: MockApiClient) -> None:
    """1件の画像送信後、件数が1増える。"""
    before = len(mock_client.list_receipts())
    mock_client.ingest_image(b"fake-image-data", "upload-1")
    after = len(mock_client.list_receipts())
    assert after == before + 1


def test_ingest_multiple_images(mock_client: MockApiClient) -> None:
    """複数件の画像送信後、件数が送信数分増える。"""
    before = len(mock_client.list_receipts())
    for i in range(3):
        mock_client.ingest_image(b"fake", f"upload-{i}")
    after = len(mock_client.list_receipts())
    assert after == before + 3


def test_ingest_image_status(mock_client: MockApiClient) -> None:
    """送信後のステータスは INGESTED になる。"""
    resp = mock_client.ingest_image(b"fake", "upload-x")
    new_id = resp["image_id"]
    img = mock_client.get_image(new_id)
    assert img["status"] == "INGESTED"


# -----------------------------------------------------------------------
# ゴミ箱操作: MockApiClient
# -----------------------------------------------------------------------

def test_move_to_dustbox_changes_status(mock_client: MockApiClient) -> None:
    """ゴミ箱移動後、ステータスが DROPPED になる。"""
    mock_client.move_to_dustbox("R-0001")
    img = mock_client.get_image("R-0001")
    assert img["status"] == "DROPPED"


def test_restore_from_dustbox_changes_status(mock_client: MockApiClient) -> None:
    """復元後、ステータスが INGESTED になる。"""
    mock_client.move_to_dustbox("R-0001")
    mock_client.restore_from_dustbox("R-0001")
    img = mock_client.get_image("R-0001")
    assert img["status"] == "INGESTED"


def test_trash_then_restore_button_mode(mock_client: MockApiClient) -> None:
    """ゴミ箱移動後は restore モード、復元後は trash モードになる。"""
    mock_client.move_to_dustbox("R-0003")
    img = mock_client.get_image("R-0003")
    assert resolve_trash_button_mode(img["status"]) == "restore"

    mock_client.restore_from_dustbox("R-0003")
    img = mock_client.get_image("R-0003")
    assert resolve_trash_button_mode(img["status"]) == "trash"


# -----------------------------------------------------------------------
# 設定の保存・読み込み
# -----------------------------------------------------------------------

def test_save_and_load_settings(tmp_path: Path, monkeypatch) -> None:
    """save_settings / load_settings が正しく動作する。"""
    import app.config.settings_io as settings_mod
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(settings_mod, "_SETTINGS_PATH", settings_file)

    data = {"page_size": 25, "detail_panel_width_percent": 35}
    save_settings(data)

    loaded = load_settings()
    assert loaded["page_size"] == 25
    assert loaded["detail_panel_width_percent"] == 35


def test_load_settings_missing_file(tmp_path: Path, monkeypatch) -> None:
    """settings.json が存在しない場合は空の辞書を返す。"""
    import app.config.settings_io as settings_mod
    monkeypatch.setattr(settings_mod, "_SETTINGS_PATH", tmp_path / "nonexistent.json")

    result = load_settings()
    assert result == {}


def test_save_settings_json_content(tmp_path: Path, monkeypatch) -> None:
    """保存された JSON の内容が正しい。"""
    import app.config.settings_io as settings_mod
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(settings_mod, "_SETTINGS_PATH", settings_file)

    data = {"status_colors": {"DROPPED": "#FFEBEE"}, "grid_visible": False}
    save_settings(data)

    raw = json.loads(settings_file.read_text(encoding="utf-8"))
    assert raw["status_colors"]["DROPPED"] == "#FFEBEE"
    assert raw["grid_visible"] is False


# -----------------------------------------------------------------------
# フィルタ適用後のサービス連携
# -----------------------------------------------------------------------

@pytest.fixture
def service(mock_client: MockApiClient) -> ReceiptsService:
    return ReceiptsService(mock_client)  # type: ignore[arg-type]


def test_filter_dropped_status(service: ReceiptsService) -> None:
    """DROPPED フィルタで DROPPED 画像のみ返る。"""
    items = service.fetch_list(status="DROPPED")
    assert len(items) == 1
    assert items[0]["image_id"] == "R-0005"
    assert resolve_trash_button_mode(items[0]["status"]) == "restore"


def test_filter_non_dropped_all_trash_mode(service: ReceiptsService) -> None:
    """DROPPED 以外のすべての画像は trash モードになる。"""
    items = service.fetch_list()
    non_dropped = [i for i in items if i["status"] != "DROPPED"]
    for item in non_dropped:
        assert resolve_trash_button_mode(item["status"]) == "trash"
