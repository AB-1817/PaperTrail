from __future__ import annotations

from app.evaluation.metrics import (
    average_precision,
    compute_all_metrics,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_precision_at_k():
    ranked = ["p1", "p2", "p3", "p4", "p5"]
    rel = {"p1", "p3"}
    assert precision_at_k(ranked, rel, k=2) == 0.5
    assert precision_at_k(ranked, rel, k=5) == 0.4


def test_recall_at_k():
    ranked = ["p1", "p2", "p3", "p4", "p5"]
    rel = {"p1", "p3", "p9"}
    assert round(recall_at_k(ranked, rel, k=3), 2) == round(2 / 3, 2)


def test_reciprocal_rank():
    assert reciprocal_rank(["p1", "p2"], {"p1"}) == 1.0
    assert reciprocal_rank(["p2", "p1"], {"p1"}) == 0.5
    assert reciprocal_rank(["p2", "p3"], {"p1"}) == 0.0


def test_ndcg_at_k_perfect():
    ranked = ["p1", "p2", "p3"]
    graded = {"p1": 2, "p2": 1, "p3": 0}
    assert ndcg_at_k(ranked, graded, k=3) == 1.0


def test_compute_all():
    ranked = ["p1", "p2", "p3", "p4", "p5"]
    graded = {"p1": 2, "p3": 1}
    res = compute_all_metrics(ranked, graded, k_values=[5])
    assert "precision@5" in res
    assert "ndcg@5" in res
    assert "mrr" in res
