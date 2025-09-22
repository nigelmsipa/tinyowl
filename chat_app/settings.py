from __future__ import annotations

import json
from typing import Any, Dict

from .config import SETTINGS_FILE_PATH


def load_settings() -> Dict[str, Any]:
    try:
        if SETTINGS_FILE_PATH.exists():
            return json.loads(SETTINGS_FILE_PATH.read_text())
    except Exception:
        pass
    return {}


def save_settings(data: Dict[str, Any]) -> None:
    try:
        SETTINGS_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE_PATH.write_text(json.dumps(data, indent=2))
    except Exception:
        # Non-fatal; ignore persistence errors
        pass

