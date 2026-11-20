from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.embeddings.batch_generator import embed_batch
from app.search.filters import FilterSpec
from app.search.query_preprocessor import preprocess
from app.search.ranking import paginate, rank_papers
from app.search.reranker import lexical_rerank
from app.search.types import PaperDoc

router = APIRouter(prefix="/search", tags=["search"])


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

    # Fetch pool of papers from PostgreSQL
    rows = await db.execute(
        text(
            """
            SELECT p.id, p.title, p.abstract, p.year, p.venue, p.open_access, p.doi
            FROM papers p
            ORDER BY p.created_at DESC
            LIMIT 500
            """
        )
    )
    paper_rows = list(rows.mappings())

    # Build PaperDoc items
    paper_docs: list[PaperDoc] = []
    for r in paper_rows:
        pid = str(r["id"])
        # Fetch authors and topics
        author_rows = await db.execute(
            text(
                """
                SELECT a.name
                FROM paper_authors pa
                JOIN authors a ON a.id = pa.author_id
                WHERE pa.paper_id = :pid
                """
            ),
            {"pid": pid},
        )
        authors = [a["name"] for a in author_rows.mappings()]

        topic_rows = await db.execute(
            text("SELECT topic FROM paper_topics WHERE paper_id = :pid"),
            {"pid": pid},
        )
        topics = [t["topic"] for t in topic_rows.mappings()]

        paper_docs.append(
            PaperDoc(
                id=pid,
                title=r["title"],
                abstract=r["abstract"],
                year=r["year"],
                venue=r["venue"],
                open_access=r["open_access"],
                doi=r["doi"],
                authors=authors,
                topics=topics,
            )
        )

    # Execute full ranking pipeline with exact requested strategy
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
                "authors": [{"name": a, "position": idx + 1} for idx, a in enumerate(item.paper.authors)],
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
        },
        "error": None,
    }


@router.get("")
async def search_papers_get(
    q: str = Query(..., min_length=2, max_length=500),
    strategy: str = Query(default="hybrid_rrf"),
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
