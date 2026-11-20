from __future__ import annotations

from app.search.bm25 import tokenize
from app.search.types import PaperDoc


def explain_result(
    query: str,
    paper: PaperDoc,
    *,
    bm25_score: float | None,
    dense_score: float | None,
    rerank_score: float | None,
) -> dict[str, object]:
    text = f"{paper.title} {paper.abstract or ''}"
    matched = [term for term in dict.fromkeys(tokenize(query)) if term in set(tokenize(text))]
    details: list[str] = []
    if matched:
        details.append("Matched terms: " + ", ".join(matched[:8]))
    if dense_score is not None:
        details.append(f"Semantic similarity {dense_score:.3f}")
    if bm25_score is not None:
        details.append(f"BM25 score {bm25_score:.3f}")
    if rerank_score is not None:
        details.append(f"Reranker score {rerank_score:.3f}")
    if paper.topics:
        details.append("Topics: " + ", ".join(paper.topics[:5]))
    return {
        "matched_terms": matched,
        "bm25_score": bm25_score,
        "dense_score": dense_score,
        "rerank_score": rerank_score,
        "details": details,
    }
