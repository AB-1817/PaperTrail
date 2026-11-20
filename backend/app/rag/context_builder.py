from __future__ import annotations

from typing import Any

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "you are now",
    "system:",
    "assistant:",
    "new instructions:",
    "forget everything",
]


def scan_for_injection(text: str) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in INJECTION_PATTERNS)


def build_context(chunks: list[dict[str, Any]], token_budget: int = 8000) -> str:
    """
    Build structured context block with [CITATION:chunk_id] markers.
    Filters out any suspicious chunks that fail prompt injection checks.
    """
    context_blocks: list[str] = []
    total_tokens = 0

    for chunk in chunks:
        chunk_text = chunk.get("text", "")
        if scan_for_injection(chunk_text):
            continue

        cid = chunk.get("id")
        est_tokens = chunk.get("token_count", int(len(chunk_text.split()) / 0.75))

        if total_tokens + est_tokens > token_budget:
            break

        context_blocks.append(f"[CITATION:{cid}]\n{chunk_text}\n[/CITATION]")
        total_tokens += est_tokens

    return "\n\n".join(context_blocks)
