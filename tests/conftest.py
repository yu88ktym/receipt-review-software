import pytest
import requests_mock as req_mock_module

from app.api.client import ApiClient
from app.config.env import API_BASE, API_KEY


@pytest.fixture
def api_client() -> ApiClient:
    """テスト用 ApiClient インスタンスを返す。"""
    return ApiClient(API_BASE, API_KEY)


@pytest.fixture
def requests_mock():
    """requests_mock アダプタのフィクスチャ。"""
    with req_mock_module.Mocker() as m:
        yield m
