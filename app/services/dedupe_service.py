from typing import Any, Callable, Iterable, List, Optional


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def dedupe_strings(items: Iterable[str], max_items: Optional[int] = None) -> List[str]:
    seen = set()
    result = []

    for item in items:
        if not item:
            continue
        key = normalize_text(item)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)

        if max_items is not None and len(result) >= max_items:
            break

    return result


def dedupe_dicts(
    items: Iterable[dict],
    key_fn: Callable[[dict], Any],
    max_items: Optional[int] = None,
) -> List[dict]:
    seen = set()
    result = []

    for item in items:
        key = key_fn(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)

        if max_items is not None and len(result) >= max_items:
            break

    return result