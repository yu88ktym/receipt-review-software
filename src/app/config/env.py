import os
from pathlib import Path

from dotenv import load_dotenv

# src/app/.env が存在すれば読み込む（存在しない場合はスキップ）
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=True)

# API接続設定（.env が存在しない場合はデフォルト値を使用）
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "local-api-key-sample")

# USE_MOCK=true のとき MockApiClient を使用する
USE_MOCK: bool = os.getenv("USE_MOCK", "false").lower() == "true"
