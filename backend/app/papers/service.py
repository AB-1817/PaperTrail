from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.normalizer import normalize_doi
from app.papers import repository
from app.papers.schemas import AuthorResponse, PaperListResponse, PaperResponse

logger = structlog.get_logger(__name__)


def _build_response(data: dict[str, Any]) -> PaperResponse:
    authors = [AuthorResponse(**a) for a in data.get("authors", [])]
    return PaperResponse(
        id=str(data["id"]),
        doi=data.get("doi"),
        title=data["title"],
        abstract=data.get("abstract"),
        year=data.get("year"),
        venue=data.get("venue"),
        volume=data.get("volume"),
        issue=data.get("issue"),
        open_access=data.get("open_access", False),
        oa_url=data.get("oa_url"),
        has_abstract=data.get("has_abstract", False),
        has_references=data.get("has_references", False),
        authors=authors,
        topics=data.get("topics", []),
        source_providers=data.get("source_providers", []),
    )


async def _resolve_live_paper(paper_id: str) -> PaperResponse | None:
    """Fetch live metadata from OpenAlex or arXiv."""
    from app.ingestion.live_fetch import _looks_like_arxiv_id, _looks_like_doi
    from app.providers.arxiv import ArXivAdapter
    from app.providers.openalex import OpenAlexAdapter

    value = paper_id.strip()
    if value.lower().startswith("doi:"):
        value = value[4:].strip()

    normalized_paper = None
    if _looks_like_arxiv_id(value):
        clean_aid = value[6:] if value.lower().startswith("arxiv:") else value
        normalized_paper = await ArXivAdapter().get_by_id(clean_aid)

    if normalized_paper is None and _looks_like_doi(value):
        normalized_paper = await OpenAlexAdapter().get_by_doi(value)

    if normalized_paper is None:
        results = await OpenAlexAdapter().search(value, limit=1)
        if _looks_like_doi(value):
            requested = normalize_doi(value)
            normalized_paper = next(
                (
                    result
                    for result in results
                    if result.doi and normalize_doi(result.doi) == requested
                ),
                None,
            )
        elif results:
            normalized_paper = results[0]

    if normalized_paper is None:
        return None

    authors = [
        AuthorResponse(name=a.name, family_name=a.family_name, orcid=a.orcid, position=a.position)
        for a in normalized_paper.authors
    ]
    doc_id = (
        normalize_doi(normalized_paper.doi) or normalized_paper.provider_id or str(uuid.uuid4())
    )
    return PaperResponse(
        id=doc_id,
        doi=normalize_doi(normalized_paper.doi),
        title=normalized_paper.title,
        abstract=normalized_paper.abstract,
        year=normalized_paper.year,
        venue=normalized_paper.venue,
        volume=normalized_paper.volume,
        issue=normalized_paper.issue,
        open_access=normalized_paper.open_access,
        oa_url=normalized_paper.oa_url,
        has_abstract=normalized_paper.has_abstract,
        has_references=normalized_paper.has_references,
        authors=authors,
        topics=normalized_paper.topics[:5],
        source_providers=[normalized_paper.source_provider],
    )


async def get_paper(db: AsyncSession, paper_id: str) -> PaperResponse:
    """
    Look up a paper by UUID, then DOI from the local DB.
    If still not found, live-fetch from OpenAlex/arXiv, persist, and return.
    Returns 404 only if no provider can find it either.
    """
    data = None

    # 1. Try UUID in local DB
    try:
        pid = uuid.UUID(paper_id)
        data = await repository.get_paper_by_id(db, pid)
    except Exception:
        pass

    # 2. Try DOI in local DB
    if not data:
        try:
            data = await repository.get_paper_by_doi(db, paper_id)
        except Exception:
            pass

    if data:
        return _build_response(data)

    # 3. Live-fetch from OpenAlex / arXiv
    live_paper = await _resolve_live_paper(paper_id)
    if live_paper:
        # Try persisting to DB in background if DB is available
        try:
            from app.ingestion.live_fetch import fetch_and_store_by_id

            await fetch_and_store_by_id(db, paper_id)
        except Exception:
            pass
        return live_paper

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Paper '{paper_id}' not found in local library or external providers",
    )


async def list_papers(db: AsyncSession, page: int, per_page: int) -> PaperListResponse:
    try:
        items, total = await repository.list_papers(db, page, per_page)
    except Exception:
        items, total = [], 0

    results: list[PaperResponse] = []
    for item in items:
        authors = [AuthorResponse(**a) for a in item.get("authors", [])]
        results.append(
            PaperResponse(
                id=str(item["id"]),
                doi=item.get("doi"),
                title=item["title"],
                abstract=item.get("abstract"),
                year=item.get("year"),
                venue=item.get("venue"),
                volume=item.get("volume"),
                issue=item.get("issue"),
                open_access=item.get("open_access", False),
                oa_url=item.get("oa_url"),
                has_abstract=item.get("has_abstract", False),
                has_references=item.get("has_references", False),
                authors=authors,
                topics=item.get("topics", []),
                source_providers=item.get("source_providers", []),
            )
        )
    return PaperListResponse(
        data=results,
        meta={"page": page, "per_page": per_page, "total": total},
    )


async def get_references(db: AsyncSession, paper_id: str) -> list[dict[str, Any]]:
    """Resolve paper_id (UUID or DOI) to its references."""
    try:
        pid = uuid.UUID(paper_id)
        return await repository.get_paper_references(db, pid)
    except Exception:
        pass

    try:
        paper = await repository.get_paper_by_doi(db, paper_id)
        if paper:
            pid = uuid.UUID(str(paper["id"]))
            return await repository.get_paper_references(db, pid)
    except Exception:
        pass

    return []
