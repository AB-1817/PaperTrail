from __future__ import annotations

import pytest

from app.papers import service
from app.papers.schemas import AuthorResponse, PaperResponse


@pytest.mark.asyncio
async def test_unknown_paper_resolves_live_result_not_seed(monkeypatch):
    expected = PaperResponse(
        id="10.1234/live-example",
        doi="10.1234/live-example",
        title="Live Paper",
        abstract="Real provider metadata",
        year=2026,
        venue="Live Venue",
        open_access=True,
        oa_url="https://arxiv.org/pdf/2601.00001",
        has_abstract=True,
        has_references=False,
        authors=[AuthorResponse(name="Live Author", position=1)],
        topics=["Testing"],
        source_providers=["openalex"],
    )

    async def resolve_live(paper_id: str):
        assert paper_id == "10.1234/live-example"
        return expected

    monkeypatch.setattr(service, "_resolve_live_paper", resolve_live)

    class NoDatabase:
        pass

    result = await service.get_paper(NoDatabase(), "10.1234/live-example")
    assert result.id == "10.1234/live-example"
    assert result.title == "Live Paper"
    assert result.oa_url == "https://arxiv.org/pdf/2601.00001"
