from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.reviews.projects import get_review_papers


async def build_comparison_matrix(
    review_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict[str, Any]]:
    papers = await get_review_papers(db, review_id, user_id)
    matrix = []

    for p in papers:
        pid = str(p["id"])
        # Topics
        t_rows = await db.execute(
            text("SELECT topic FROM paper_topics WHERE paper_id = :pid LIMIT 3"),
            {"pid": pid},
        )
        topics = [r["topic"] for r in t_rows.mappings()]

        abstract = p.get("abstract") or ""
        problem = (
            abstract[:150] + "..."
            if len(abstract) > 150
            else abstract or "Not specified in abstract"
        )

        matrix.append(
            {
                "paper_id": p["id"],
                "title": p["title"],
                "year": p["year"],
                "research_problem": problem,
                "methodology": ", ".join(topics) if topics else "Not specified in metadata",
                "dataset": "Not available in source metadata",
                "key_findings": "Refer to section synthesis or full text",
                "limitations": "Not available in source metadata",
            }
        )

    return matrix
