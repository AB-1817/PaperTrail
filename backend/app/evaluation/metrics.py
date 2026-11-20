from __future__ import annotations

import math


def precision_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of top-K results that are relevant."""
    if k <= 0 or not ranked_ids:
        return 0.0
    top_k = ranked_ids[:k]
    relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_retrieved / k


def recall_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of all relevant documents retrieved in top-K."""
    if not relevant_ids or k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_retrieved / len(relevant_ids)


def reciprocal_rank(ranked_ids: list[str], relevant_ids: set[str]) -> float:
    """Reciprocal rank of the first relevant result (1/rank)."""
    for rank, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    ranked_ids: list[str],
    graded_relevance: dict[str, int],
    k: int,
) -> float:
    """
    Normalized Discounted Cumulative Gain at K using graded relevance.
    DCG = sum (2^rel - 1) / log2(rank + 1)
    """
    if k <= 0 or not ranked_ids:
        return 0.0

    top_k = ranked_ids[:k]
    dcg = 0.0
    for rank, doc_id in enumerate(top_k, start=1):
        rel = graded_relevance.get(doc_id, 0)
        dcg += (math.pow(2, rel) - 1.0) / math.log2(rank + 1)

    # Ideal DCG
    ideal_grades = sorted(graded_relevance.values(), reverse=True)[:k]
    idcg = 0.0
    for rank, rel in enumerate(ideal_grades, start=1):
        idcg += (math.pow(2, rel) - 1.0) / math.log2(rank + 1)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def average_precision(ranked_ids: list[str], relevant_ids: set[str]) -> float:
    """Average precision for a single query."""
    if not relevant_ids or not ranked_ids:
        return 0.0

    hit_count = 0
    precision_sum = 0.0
    for rank, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant_ids:
            hit_count += 1
            precision_sum += hit_count / rank

    return precision_sum / len(relevant_ids)


def mean_average_precision(queries: list[tuple[list[str], set[str]]]) -> float:
    """Mean Average Precision across multiple queries."""
    if not queries:
        return 0.0
    return sum(average_precision(ranked, rel) for ranked, rel in queries) / len(queries)


def compute_all_metrics(
    ranked_ids: list[str],
    graded_relevance: dict[str, int],
    k_values: list[int] | None = None,
) -> dict[str, float]:
    """Compute all standard evaluation metrics for the given rankings."""
    if k_values is None:
        k_values = [5, 10, 20]

    relevant_ids = {doc_id for doc_id, grade in graded_relevance.items() if grade >= 1}
    results: dict[str, float] = {}

    for k in k_values:
        results[f"precision@{k}"] = round(precision_at_k(ranked_ids, relevant_ids, k), 4)
        results[f"recall@{k}"] = round(recall_at_k(ranked_ids, relevant_ids, k), 4)
        results[f"ndcg@{k}"] = round(ndcg_at_k(ranked_ids, graded_relevance, k), 4)

    results["mrr"] = round(reciprocal_rank(ranked_ids, relevant_ids), 4)
    results["ap"] = round(average_precision(ranked_ids, relevant_ids), 4)
    return results
