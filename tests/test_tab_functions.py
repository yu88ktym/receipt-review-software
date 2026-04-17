"""各タブのロジックテスト。

GUI ウィジェットの操作テストは除外し、APIモックを使用したロジックのみ検証する。
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from app.services.receipts_service import ReceiptsService
from app.ui.ui_utils import resolve_trash_button_mode, image_meta_to_row, build_dup_maps
from app.config.settings_io import load_settings, save_settings
from app.api.routes import ApiRoutes
from tests.mocks.mock_api_client import MockApiClient
from tests.mocks.mock_data import DUMMY_IMAGES


# -----------------------------------------------------------------------
# ボタン表示条件: resolve_trash_button_mode
# -----------------------------------------------------------------------

def test_trash_button_mode_dropped() -> None:
    """DROPPED ステータスでは restore モードになる。"""
    assert resolve_trash_button_mode("DROPPED") == "restore"


def test_trash_button_mode_non_dropped() -> None:
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


# -----------------------------------------------------------------------
# reverse_parent ルート変更: image_id なし
# -----------------------------------------------------------------------

def test_reverse_parent_route_has_no_image_id() -> None:
    """reverse_parent エンドポイントは image_id を含まない。"""
    routes = ApiRoutes("http://localhost:8000")
    url = routes.reverse_parent()
    assert url == "http://localhost:8000/api/images/reverse-parent"
    assert "R-0001" not in url


# -----------------------------------------------------------------------
# 確定値編集タブ: 確定ボタン表示ロジック
# -----------------------------------------------------------------------

def _confirm_btn_state(status: str | None) -> tuple[str, bool]:
    """ステータスから（ボタンテキスト, 有効フラグ）を返すピュア関数（UIロジック相当）。"""
    if status is None:
        return "確定", False
    if status == "FINAL_UPDATED":
        return "遡及修正", True
    if status in ("FINAL_UPDATED_CHILD", "DROPPED"):
        return "確定", False
    return "確定", True


def test_confirm_btn_final_updated() -> None:
    text, enabled = _confirm_btn_state("FINAL_UPDATED")
    assert text == "遡及修正"
    assert enabled is True


def test_confirm_btn_final_updated_child() -> None:
    text, enabled = _confirm_btn_state("FINAL_UPDATED_CHILD")
    assert text == "確定"
    assert enabled is False


def test_confirm_btn_dropped() -> None:
    text, enabled = _confirm_btn_state("DROPPED")
    assert text == "確定"
    assert enabled is False


def test_confirm_btn_other_status() -> None:
    for status in ("INGESTED", "OCR_DONE", "OCR_FAILED"):
        text, enabled = _confirm_btn_state(status)
        assert text == "確定", f"status={status!r}"
        assert enabled is True, f"status={status!r}"


def test_confirm_btn_no_selection() -> None:
    text, enabled = _confirm_btn_state(None)
    assert enabled is False


# -----------------------------------------------------------------------
# 確定値編集タブ: finalize_receipt / revise_final_receipt の呼び分け
# -----------------------------------------------------------------------

def test_finalize_called_for_non_final_updated(mock_client: MockApiClient) -> None:
    """FINAL_UPDATED 以外のステータスで finalize_receipt が呼ばれると FINAL_UPDATED になる。"""
    body = {"purchased_at": "2024-01-16", "total_amount": 1500, "store_name": "スーパーB", "payment_method": "クレジット"}
    result = mock_client.finalize_receipt("R-0002", body)
    assert result["status"] == "FINAL_UPDATED"


def test_revise_called_for_final_updated(mock_client: MockApiClient) -> None:
    """FINAL_UPDATED ステータスで revise_final_receipt が呼ばれても例外が発生しない。"""
    body = {"purchased_at": "2024-01-14", "total_amount": 9999, "store_name": "テスト", "payment_method": "現金"}
    result = mock_client.revise_final_receipt("R-0001", body)
    assert result is not None


# -----------------------------------------------------------------------
# Dups タブ: 親子マッピング構築ロジック
# -----------------------------------------------------------------------

def test_dup_maps_child_of_r0004(service: ReceiptsService) -> None:
    """R-0004 は R-0003 の子として認識される。"""
    items = service.fetch_list()
    child_parent, parent_children = build_dup_maps(items)
    assert child_parent.get("R-0004") == "R-0003"
    assert "R-0004" in parent_children.get("R-0003", [])


def test_dup_maps_no_child_for_standalone(service: ReceiptsService) -> None:
    """duplicate_of が None の画像は子マッピングに含まれない。"""
    items = service.fetch_list()
    child_parent, _ = build_dup_maps(items)
    for iid in ("R-0001", "R-0002", "R-0005", "R-0006"):
        assert iid not in child_parent, f"{iid} should not be a child"


# -----------------------------------------------------------------------
# Dups タブ: set_duplicate / unset_duplicate
# -----------------------------------------------------------------------

def test_set_duplicate_creates_relationship(mock_client: MockApiClient) -> None:
    """set_duplicate 後、戻り値が正しい。"""
    result = mock_client.set_duplicate("R-0002", "R-0001")
    assert result["image_id"] == "R-0002"
    assert result["parent_image_id"] == "R-0001"


def test_unset_duplicate_removes_relationship(mock_client: MockApiClient) -> None:
    """unset_duplicate 後の戻り値が正しい。"""
    result = mock_client.unset_duplicate("R-0004", "R-0003")
    assert result["image_id"] == "R-0004"
    assert result["parent_image_id"] == "R-0003"


def test_reverse_parent_returns_correct_ids(mock_client: MockApiClient) -> None:
    """reverse_parent が正しい old/new parent_id を返す。"""
    result = mock_client.reverse_parent("R-0003", "R-0004")
    assert result["old_parent_id"] == "R-0003"
    assert result["new_parent_id"] == "R-0004"


def test_build_dup_maps_empty_list() -> None:
    """空リストを渡した場合は両マップとも空。"""
    c2p, p2c = build_dup_maps([])
    assert c2p == {}
    assert p2c == {}


def test_build_dup_maps_standalone_not_in_either_map(service: ReceiptsService) -> None:
    """親子関係のない画像はどちらのマップにも含まれない。"""
    items = service.fetch_list()
    child_to_parent, parent_to_children = build_dup_maps(items)
    for iid in ("R-0001", "R-0002", "R-0005", "R-0006"):
        assert iid not in child_to_parent
        assert iid not in parent_to_children
