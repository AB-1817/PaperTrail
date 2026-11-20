from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.recommendations.content_ranker import content_based_recommend


async def personalized_recommend(
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 20,
) -> list[dict[str, Any]]:
    # 1. Fetch user's saved papers
    saved_rows = await db.execute(
        text("SELECT paper_id FROM saved_papers WHERE user_id = :uid ORDER BY saved_at DESC LIMIT 10"),
        {"uid": str(user_id)},
    )
    saved_ids = [r["paper_id"] for r in saved_rows.mappings()]

    if not saved_ids:
        # Cold start fallback: recommend most popular or newest open access papers
        popular_rows = await db.execute(
            text(
                """
                SELECT id as paper_id, title, year, venue, open_access
                FROM papers
                ORDER BY open_access DESC, created_at DESC
                LIMIT :lim
                """
            ),
            {"lim": limit},
        )
        results = []
        for r in popular_rows.mappings():
            results.append(
                {
                    "paper_id": r["paper_id"],
                    "title": r["title"],
                    "year": r["year"],
                    "venue": r["venue"],
                    "open_access": r["open_access"],
                    "score": 0.5,
                    "explanation": {
                        "primary_reason": "cold_start_discovery",
                        "details": ["Popular discovery seed paper"],
                        "component_scores": {"topic": 0.5},
                    },
                }
            )
        return results

    # Content-based recommendation from the latest saved paper
    seed_paper_id = saved_ids[0]
    return await content_based_recommend(seed_paper_id, user_id, db, limit=limit)
