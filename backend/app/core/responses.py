from __future__ import annotations

from typing import Any


def envelope(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta, "error": None}


def page_meta(page: int, per_page: int, total: int, request_id: str) -> dict[str, Any]:
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "request_id": request_id,
    }
