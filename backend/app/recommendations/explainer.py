from __future__ import annotations

from typing import Any


def build_explanation(
    primary_reason: str,
    details: list[str],
    component_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    return {
        "primary_reason": primary_reason,
        "details": details,
        "component_scores": component_scores or {},
    }
