from __future__ import annotations

from app.search.hybrid_fusion import rrf_fuse


def test_rrf_fuse_single_list():
    ranking = [["paper1", "paper2", "paper3"]]
    fused = rrf_fuse(ranking, k=60)
    assert len(fused) == 3
    assert fused[0][0] == "paper1"
    assert fused[1][0] == "paper2"
    assert fused[2][0] == "paper3"


def test_rrf_fuse_two_lists():
    list1 = ["p1", "p2", "p3"]
    list2 = ["p2", "p1", "p4"]
    fused = rrf_fuse([list1, list2], k=60)
    top_ids = [item[0] for item in fused]
    assert "p1" in top_ids[:2]
    assert "p2" in top_ids[:2]
    assert len(fused) == 4


def test_rrf_fuse_empty():
    assert rrf_fuse([]) == []
