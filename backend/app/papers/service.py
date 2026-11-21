from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.papers import repository
from app.papers.schemas import AuthorResponse, PaperListResponse, PaperResponse


async def get_paper(db: AsyncSession, paper_id: str) -> PaperResponse:
    data = None
    try:
        pid = uuid.UUID(paper_id)
        data = await repository.get_paper_by_id(db, pid)
    except Exception:
        pass

    if not data:
        # Check SEED_PAPERS
        from app.search.seed_corpus import SEED_PAPERS
        for sp in SEED_PAPERS:
            if sp.id == paper_id or sp.doi == paper_id:
                return PaperResponse(
                    id=sp.id,
                    doi=sp.doi,
                    title=sp.title,
                    abstract=sp.abstract,
                    year=sp.year,
                    venue=sp.venue,
                    volume=None,
                    issue=None,
                    open_access=sp.open_access,
                    oa_url=f"https://doi.org/{sp.doi}" if sp.doi else None,
                    has_abstract=bool(sp.abstract),
                    has_references=False,
                    authors=[AuthorResponse(name=a, position=idx + 1) for idx, a in enumerate(sp.authors)],
                    topics=sp.topics,
                    source_providers=["openalex"],
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID '{paper_id}' not found",
        )
    authors = [AuthorResponse(**a) for a in data.get("authors", [])]
    return PaperResponse(
        id=data["id"],
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


async def list_papers(db: AsyncSession, page: int, per_page: int) -> PaperListResponse:
    items, total = await repository.list_papers(db, page, per_page)
    results: list[PaperResponse] = []
    for item in items:
        authors = [AuthorResponse(**a) for a in item.get("authors", [])]
        results.append(
            PaperResponse(
                id=item["id"],
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
    try:
        pid = uuid.UUID(paper_id)
        return await repository.get_paper_references(db, pid)
    except Exception:
        return []
