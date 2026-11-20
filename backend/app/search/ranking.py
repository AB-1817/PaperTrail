from __future__ import annotations

from collections.abc import Callable

from app.search.bm25 import bm25_rank
from app.search.dense import dense_rank
from app.search.filters import FilterSpec, apply_filters
from app.search.hybrid_fusion import rrf_fuse
from app.search.result_explainer import explain_result
from app.search.types import PaperDoc, RankedPaper

STRATEGIES = ("bm25_only", "dense_only", "hybrid_rrf", "hybrid_rerank")
EmbedFn = Callable[[list[str]], list[list[float]]]
RerankFn = Callable[[str, list[str]], list[float]]


def document_text(paper: PaperDoc) -> str:
    return f"{paper.title}\n{paper.abstract or ''}".strip()


def rank_papers(
    strategy: str,
    query: str,
    papers: list[PaperDoc],
    embedder: EmbedFn,
    reranker: RerankFn,
    *,
    filters: FilterSpec | None = None,
    k1: float = 1.2,
    b: float = 0.75,
    dense_override: list[str] | None = None,
) -> list[RankedPaper]:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy}")
    # Filters run before any ranking so discarded papers never take a slot.
    pool = apply_filters(papers, filters) if filters is not None else list(papers)
    by_id = {paper.id: paper for paper in pool}
    pairs = [(paper.id, document_text(paper)) for paper in pool]

    lexical = bm25_rank(query, pairs, k1=k1, b=b) if strategy != "dense_only" else []
    if strategy == "bm25_only":
        semantic: list[tuple[str, float]] = []
    elif dense_override is not None:
        semantic = [
            (doc_id, 1.0 / rank)
            for rank, doc_id in enumerate(dense_override, start=1)
            if doc_id in by_id
        ]
    else:
        semantic = dense_rank(query, pairs, embedder)

    lexical_scores = dict(lexical)
    semantic_scores = dict(semantic)
    fused_scores: dict[str, float] = {}
    rerank_scores: dict[str, float] = {}

    if strategy == "bm25_only":
        ordered = [doc_id for doc_id, _ in lexical]
    elif strategy == "dense_only":
        ordered = [doc_id for doc_id, _ in semantic]
    else:
        fused = rrf_fuse(
            [
                [doc_id for doc_id, _ in lexical],
                [doc_id for doc_id, _ in semantic],
            ]
        )
        fused_scores = dict(fused)
        ordered = [doc_id for doc_id, _ in fused]
        if strategy == "hybrid_rerank" and ordered:
            head = ordered[:50]
            scores = reranker(query, [document_text(by_id[doc_id]) for doc_id in head])
            paired = sorted(
                zip(head, scores, strict=True),
                key=lambda item: (-item[1], item[0]),
            )
            rerank_scores = {doc_id: score for doc_id, score in paired}
            ordered = [doc_id for doc_id, _ in paired]

    ranked: list[RankedPaper] = []
    for doc_id in ordered:
        paper = by_id[doc_id]
        bm25_score = lexical_scores.get(doc_id)
        dense_score = semantic_scores.get(doc_id)
        rerank_score = rerank_scores.get(doc_id)
        if rerank_score is not None:
            score = rerank_score
        elif strategy == "dense_only":
            score = dense_score or 0.0
        elif strategy == "bm25_only":
            score = bm25_score or 0.0
        else:
            score = fused_scores.get(doc_id, 0.0)
        ranked.append(
            RankedPaper(
                paper=paper,
                score=float(score),
                bm25_score=bm25_score,
                dense_score=dense_score,
                rerank_score=rerank_score,
                explanation=explain_result(
                    query,
                    paper,
                    bm25_score=bm25_score,
                    dense_score=dense_score,
                    rerank_score=rerank_score,
                ),
            )
        )
    return ranked


def paginate(items: list[RankedPaper], page: int, per_page: int) -> tuple[list[RankedPaper], int]:
    start = (page - 1) * per_page
    return items[start : start + per_page], len(items)
