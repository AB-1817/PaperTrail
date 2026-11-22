from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_paper_by_id(db: AsyncSession, paper_id: uuid.UUID) -> dict[str, Any] | None:
    paper_row = await db.execute(
        text("SELECT * FROM papers WHERE id = :id"),
        {"id": str(paper_id)},
    )
    p = paper_row.mappings().first()
    if not p:
        return None

    # Authors
    author_rows = await db.execute(
        text(
            """
            SELECT a.id, a.name, a.family_name, a.orcid, pa.position
            FROM paper_authors pa
            JOIN authors a ON a.id = pa.author_id
            WHERE pa.paper_id = :pid
            ORDER BY pa.position
            """
        ),
        {"pid": str(paper_id)},
    )
    authors = [dict(a) for a in author_rows.mappings()]

    # Topics
    topic_rows = await db.execute(
        text("SELECT topic FROM paper_topics WHERE paper_id = :pid"),
        {"pid": str(paper_id)},
    )
    topics = [r["topic"] for r in topic_rows.mappings()]

    # Sources
    source_rows = await db.execute(
        text("SELECT DISTINCT provider FROM paper_sources WHERE paper_id = :pid"),
        {"pid": str(paper_id)},
    )
    sources = [r["provider"] for r in source_rows.mappings()]

    res = dict(p)
    res["authors"] = authors
    res["topics"] = topics
    res["source_providers"] = sources
    return res


async def list_papers(
    db: AsyncSession, page: int = 1, per_page: int = 20
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * per_page
    rows = await db.execute(
        text("SELECT * FROM papers ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
        {"lim": per_page, "off": offset},
    )
    papers = [dict(r) for r in rows.mappings()]

    # For each paper, attach minimal authors & topics
    for p in papers:
        author_rows = await db.execute(
            text(
                """
                SELECT a.name, pa.position
                FROM paper_authors pa
                JOIN authors a ON a.id = pa.author_id
                WHERE pa.paper_id = :pid
                ORDER BY pa.position
                LIMIT 5
                """
            ),
            {"pid": str(p["id"])},
        )
        p["authors"] = [dict(a) for a in author_rows.mappings()]
        p["topics"] = []
        p["source_providers"] = []

    count_row = await db.execute(text("SELECT count(*) FROM papers"))
    total = count_row.scalar() or 0
    return papers, total


async def get_paper_by_doi(db: AsyncSession, doi: str) -> dict[str, Any] | None:
    paper_row = await db.execute(
        text("SELECT * FROM papers WHERE doi = :doi"),
        {"doi": doi},
    )
    p = paper_row.mappings().first()
    if not p:
        return None

    pid = p["id"]

    author_rows = await db.execute(
        text(
            """
            SELECT a.id, a.name, a.family_name, a.orcid, pa.position
            FROM paper_authors pa
            JOIN authors a ON a.id = pa.author_id
            WHERE pa.paper_id = :pid
            ORDER BY pa.position
            """
        ),
        {"pid": str(pid)},
    )
    topic_rows = await db.execute(
        text("SELECT topic FROM paper_topics WHERE paper_id = :pid"),
        {"pid": str(pid)},
    )
    source_rows = await db.execute(
        text("SELECT DISTINCT provider FROM paper_sources WHERE paper_id = :pid"),
        {"pid": str(pid)},
    )

    res = dict(p)
    res["authors"] = [dict(a) for a in author_rows.mappings()]
    res["topics"] = [r["topic"] for r in topic_rows.mappings()]
    res["source_providers"] = [r["provider"] for r in source_rows.mappings()]
    return res


async def get_paper_references(db: AsyncSession, paper_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = await db.execute(
        text(
            """
            SELECT pr.id, pr.citing_paper_id, pr.cited_paper_id, pr.doi_fallback,
                   p.title as cited_title, p.year as cited_year
            FROM paper_references pr
            LEFT JOIN papers p ON p.id = pr.cited_paper_id
            WHERE pr.citing_paper_id = :pid
            """
        ),
        {"pid": str(paper_id)},
    )
    return [dict(r) for r in rows.mappings()]
