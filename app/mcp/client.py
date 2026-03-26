import json
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


def _load_server_registry() -> Dict[str, Any]:
    path = Path(__file__).resolve().parent / "servers.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_registered_server(name: str) -> Dict[str, Any]:
    registry = _load_server_registry()
    return registry.get(name, {})


def is_server_enabled(name: str) -> bool:
    server = get_registered_server(name)
    return bool(server.get("enabled", False))