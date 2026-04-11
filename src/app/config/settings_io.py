"""設定の永続化（読み込み・書き込み）。PySide6 に依存しない。"""
from __future__ import annotations

import json
from pathlib import Path

# settings.json の保存先（プロジェクトルートに配置）
_SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "settings.json"


def load_settings() -> dict:
    """settings.json を読み込んで辞書を返す。ファイルがなければ空の辞書を返す。"""
    if _SETTINGS_PATH.exists():
        try:
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(data: dict) -> None:
    """設定を settings.json に書き込む。"""
    _SETTINGS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
