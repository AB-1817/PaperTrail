from __future__ import annotations

from app.search.bm25 import tokenize


def lexical_rerank(query: str, texts: list[str]) -> list[float]:
    """Overlap reranker used when the cross-encoder weights are not loaded.

    Scores are lexical overlap in [0, 1]. Callers must record the model id
    as ``lexical-overlap`` so this is not reported as BGE reranker output.
    """
    query_terms = set(tokenize(query))
    if not query_terms:
        return [0.0 for _ in texts]
    scores: list[float] = []
    for text in texts:
        overlap = len(query_terms & set(tokenize(text)))
        scores.append(overlap / len(query_terms))
    return scores
