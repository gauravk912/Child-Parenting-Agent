import json
from math import sqrt
from pathlib import Path
from typing import Dict, List, Any

from app.core.config import settings


def _vector_store_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    path = project_root / settings.local_vector_store_file
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_vector_store() -> List[Dict[str, Any]]:
    path = _vector_store_path()
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_vector_store(records: List[Dict[str, Any]]) -> None:
    path = _vector_store_path()
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def append_vector_records(records_to_add: List[Dict[str, Any]]) -> None:
    existing = load_vector_store()
    existing.extend(records_to_add)
    save_vector_store(existing)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def search_vector_store(
    query_embedding: List[float],
    child_id: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    records = load_vector_store()
    filtered = [r for r in records if r.get("child_id") == child_id]

    scored = []
    for record in filtered:
        score = _cosine_similarity(query_embedding, record.get("embedding", []))
        scored.append({**record, "score": round(score, 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]