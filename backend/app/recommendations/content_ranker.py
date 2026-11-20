from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.search.bm25 import bm25_rank


async def content_based_recommend(
    paper_id: uuid.UUID,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    limit: int = 20,
) -> list[dict[str, Any]]:
    # Fetch target paper
    target_row = await db.execute(
        text("SELECT title, abstract FROM papers WHERE id = :pid"),
        {"pid": str(paper_id)},
    )
    target = target_row.mappings().first()
    if not target or not target["title"]:
        return []

    target_text = f"{target['title']}\n{target['abstract'] or ''}"

    # Fetch pool of papers excluding the target and (if authenticated) user's saved papers
    query = """
        SELECT p.id, p.title, p.abstract, p.year, p.venue, p.open_access
        FROM papers p
        WHERE p.id != :pid
    """
    params: dict[str, Any] = {"pid": str(paper_id)}
    if user_id:
        query += " AND p.id NOT IN (SELECT paper_id FROM saved_papers WHERE user_id = :uid)"
        params["uid"] = str(user_id)
    query += " LIMIT 300"

    rows = await db.execute(text(query), params)
    papers = list(rows.mappings())
    if not papers:
        return []

    docs = [(str(p["id"]), f"{p['title']}\n{p['abstract'] or ''}") for p in papers]
    scored = bm25_rank(target_text, docs)

    by_id = {str(p["id"]): dict(p) for p in papers}
    results = []
    for doc_id, score in scored[:limit]:
        p = by_id[doc_id]
        results.append(
            {
                "paper_id": p["id"],
                "title": p["title"],
                "year": p["year"],
                "venue": p["venue"],
                "open_access": p["open_access"],
                "score": round(score, 4),
                "explanation": {
                    "primary_reason": "semantic_content_similarity",
                    "details": [f"High content similarity with target paper ({target['title'][:60]}...)"],
                    "component_scores": {"semantic": round(score, 4)},
                },
            }
        )
    return results
