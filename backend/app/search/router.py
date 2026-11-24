from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.embeddings.batch_generator import embed_batch
from app.ingestion.live_fetch import live_search_and_store
from app.search.filters import FilterSpec
from app.search.query_preprocessor import preprocess
from app.search.ranking import paginate, rank_papers
from app.search.reranker import lexical_rerank
from app.search.types import PaperDoc

router = APIRouter(prefix="/search", tags=["search"])
logger = structlog.get_logger(__name__)


class SearchRequest(BaseModel):
    q: str = Field(..., min_length=2, max_length=500)
    strategy: str = Field(
        default="hybrid_rrf",
        pattern="^(bm25_only|dense_only|hybrid_rrf|hybrid_rerank)$",
    )
    year_from: int | None = None
    year_to: int | None = None
    open_access: bool | None = None
    topics: list[str] | None = None
    author: str | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


@router.post("")
async def search_papers_post(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        parsed_query = preprocess(body.q)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    filter_spec = FilterSpec(
        year_from=body.year_from,
        year_to=body.year_to,
        open_access=body.open_access,
        topics=body.topics,
        author=body.author or parsed_query.fields.get("author"),
        doi=parsed_query.fields.get("doi"),
    )

    # Always live-fetch from OpenAlex + arXiv for the actual query.
    # Results are persisted to DB so repeat searches are fast.
    paper_docs: list[PaperDoc] = []
    live_sourced = False
    try:
        live_rows = await live_search_and_store(db, body.q, limit=body.per_page)
        live_sourced = True
        for row in live_rows:
            paper_docs.append(
                PaperDoc(
                    id=row["id"],
                    title=row["title"],
                    abstract=row.get("abstract") or "",
                    year=row.get("year"),
                    venue=row.get("venue"),
                    open_access=row.get("open_access", False),
                    doi=row.get("doi"),
                    authors=[a["name"] for a in row.get("authors", [])],
                    topics=row.get("topics", []),
                )
            )
    except Exception as exc:
        logger.error("live_search_failed", query=body.q, error=str(exc))

    ranked = rank_papers(
        strategy=body.strategy,
        query=parsed_query.text,
        papers=paper_docs,
        embedder=embed_batch,
        reranker=lexical_rerank,
        filters=filter_spec,
    )

    page_items, total = paginate(ranked, page=body.page, per_page=body.per_page)

    results = []
    for item in page_items:
        results.append(
            {
                "id": item.paper.id,
                "title": item.paper.title,
                "abstract": item.paper.abstract,
                "year": item.paper.year,
                "venue": item.paper.venue,
                "open_access": item.paper.open_access,
                "doi": item.paper.doi,
                "authors": [
                    {"name": a, "position": idx + 1} for idx, a in enumerate(item.paper.authors)
                ],
                "topics": item.paper.topics,
                "score": round(item.score, 4),
                "explanation": item.explanation,
            }
        )

    return {
        "data": results,
        "meta": {
            "page": body.page,
            "per_page": body.per_page,
            "total": total,
            "strategy": body.strategy,
            "query": body.q,
            "live_sourced": live_sourced,
        },
        "error": None,
    }


@router.get("")
async def search_papers_get(
    q: str = Query(..., min_length=2, max_length=500),
    strategy: str = Query(
        default="hybrid_rrf",
        pattern="^(bm25_only|dense_only|hybrid_rrf|hybrid_rerank)$",
    ),
    year_from: int | None = Query(default=None),
    year_to: int | None = Query(default=None),
    open_access: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    req = SearchRequest(
        q=q,
        strategy=strategy,
        year_from=year_from,
        year_to=year_to,
        open_access=open_access,
        page=page,
        per_page=per_page,
    )
    return await search_papers_post(req, db)
