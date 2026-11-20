from __future__ import annotations

import pytest

from app.search.query_preprocessor import preprocess


def test_preprocess_basic_query():
    pq = preprocess("Transformer attention networks")
    assert pq.text == "transformer attention networks"
    assert not pq.fields


def test_preprocess_author_field():
    pq = preprocess("author:Vaswani transformer")
    assert "vaswani" in pq.fields.get("author", "").lower()
    assert pq.text == "transformer"


def test_preprocess_doi_field():
    pq = preprocess("doi:10.1145/3065386")
    assert pq.fields.get("doi") == "10.1145/3065386"


def test_preprocess_too_short():
    with pytest.raises(ValueError, match="at least 2"):
        preprocess("a")
