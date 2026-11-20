from __future__ import annotations

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running"},
    "running": {"completed", "partial_failure", "failed"},
}


def transition(current: str, new: str) -> str:
    if new not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Illegal ingestion transition {current} -> {new}")
    return new


def final_status(*, papers_inserted: int, papers_updated: int, errors: list[str]) -> str:
    if errors and papers_inserted == 0 and papers_updated == 0:
        return "failed"
    if errors:
        return "partial_failure"
    return "completed"
