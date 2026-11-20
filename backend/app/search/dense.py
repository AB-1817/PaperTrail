from __future__ import annotations

import math


def cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def dense_rank(
    query: str,
    documents: list[tuple[str, str]],
    embed,
) -> list[tuple[str, float]]:
    if not documents:
        return []
    vectors = embed([query] + [text for _, text in documents])
    query_vector = vectors[0]
    scored = [
        (doc_id, cosine(query_vector, vectors[index + 1]))
        for index, (doc_id, _) in enumerate(documents)
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored
