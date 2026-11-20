from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def citation_based_recommend(
    paper_id: uuid.UUID,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Bibliographic coupling / co-citation recommendations.
    Finds papers that share references with the target paper.
    """
    query = """
        SELECT pr2.citing_paper_id as rec_id, count(*) as shared_refs,
               p.title, p.year, p.venue, p.open_access
        FROM paper_references pr1
        JOIN paper_references pr2 ON (
            (pr1.cited_paper_id IS NOT NULL AND pr1.cited_paper_id = pr2.cited_paper_id)
            OR (pr1.doi_fallback IS NOT NULL AND pr1.doi_fallback = pr2.doi_fallback)
        )
        JOIN papers p ON p.id = pr2.citing_paper_id
        WHERE pr1.citing_paper_id = :pid
          AND pr2.citing_paper_id != :pid
    """
    params: dict[str, Any] = {"pid": str(paper_id), "lim": limit}
    if user_id:
        query += " AND pr2.citing_paper_id NOT IN (SELECT paper_id FROM saved_papers WHERE user_id = :uid)"
        params["uid"] = str(user_id)

    query += """
        GROUP BY pr2.citing_paper_id, p.title, p.year, p.venue, p.open_access
        ORDER BY shared_refs DESC
        LIMIT :lim
    """

    rows = await db.execute(text(query), params)
    items = list(rows.mappings())

    results = []
    max_shared = items[0]["shared_refs"] if items else 1
    for r in items:
        norm_score = round(r["shared_refs"] / max_shared, 4)
        results.append(
            {
                "paper_id": r["rec_id"],
                "title": r["title"],
                "year": r["year"],
                "venue": r["venue"],
                "open_access": r["open_access"],
                "score": norm_score,
                "explanation": {
                    "primary_reason": "shared_references",
                    "details": [f"Shares {r['shared_refs']} bibliographic references with seed paper"],
                    "component_scores": {"citation": norm_score},
                },
            }
        )
    return results
