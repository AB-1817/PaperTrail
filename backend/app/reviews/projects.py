from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def create_review(
    db: AsyncSession, user_id: uuid.UUID, title: str, description: str | None
) -> dict[str, Any]:
    rid = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO literature_reviews (id, user_id, title, description, status)
            VALUES (:id, :uid, :title, :desc, 'draft')
            """
        ),
        {"id": rid, "uid": str(user_id), "title": title, "desc": description},
    )
    await db.commit()
    return await get_review(db, uuid.UUID(rid), user_id)  # type: ignore


async def get_review(
    db: AsyncSession, review_id: uuid.UUID, user_id: uuid.UUID
) -> dict[str, Any] | None:
    row = await db.execute(
        text(
            """
            SELECT r.*, count(rp.paper_id) as paper_count
            FROM literature_reviews r
            LEFT JOIN literature_review_papers rp ON rp.review_id = r.id
            WHERE r.id = :rid AND r.user_id = :uid
            GROUP BY r.id
            """
        ),
        {"rid": str(review_id), "uid": str(user_id)},
    )
    res = row.mappings().first()
    return dict(res) if res else None


async def list_reviews(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * per_page
    rows = await db.execute(
        text(
            """
            SELECT r.*, count(rp.paper_id) as paper_count
            FROM literature_reviews r
            LEFT JOIN literature_review_papers rp ON rp.review_id = r.id
            WHERE r.user_id = :uid
            GROUP BY r.id
            ORDER BY r.updated_at DESC
            LIMIT :lim OFFSET :off
            """
        ),
        {"uid": str(user_id), "lim": per_page, "off": offset},
    )
    items = [dict(r) for r in rows.mappings()]
    count_row = await db.execute(
        text("SELECT count(*) FROM literature_reviews WHERE user_id = :uid"),
        {"uid": str(user_id)},
    )
    total = count_row.scalar() or 0
    return items, total


async def add_paper_to_review(
    db: AsyncSession, review_id: uuid.UUID, user_id: uuid.UUID, paper_id: uuid.UUID
) -> bool:
    rev = await get_review(db, review_id, user_id)
    if not rev:
        return False
    await db.execute(
        text(
            """
            INSERT INTO literature_review_papers (review_id, paper_id)
            VALUES (:rid, :pid)
            ON CONFLICT DO NOTHING
            """
        ),
        {"rid": str(review_id), "pid": str(paper_id)},
    )
    await db.commit()
    return True


async def remove_paper_from_review(
    db: AsyncSession, review_id: uuid.UUID, user_id: uuid.UUID, paper_id: uuid.UUID
) -> bool:
    rev = await get_review(db, review_id, user_id)
    if not rev:
        return False
    res = await db.execute(
        text("DELETE FROM literature_review_papers WHERE review_id = :rid AND paper_id = :pid"),
        {"rid": str(review_id), "pid": str(paper_id)},
    )
    await db.commit()
    return res.rowcount > 0


async def get_review_papers(
    db: AsyncSession, review_id: uuid.UUID, user_id: uuid.UUID
) -> list[dict[str, Any]]:
    rev = await get_review(db, review_id, user_id)
    if not rev:
        return []
    rows = await db.execute(
        text(
            """
            SELECT p.id, p.title, p.abstract, p.year, p.venue, p.open_access
            FROM literature_review_papers rp
            JOIN papers p ON p.id = rp.paper_id
            WHERE rp.review_id = :rid
            ORDER BY p.year DESC NULLS LAST
            """
        ),
        {"rid": str(review_id)},
    )
    return [dict(r) for r in rows.mappings()]
