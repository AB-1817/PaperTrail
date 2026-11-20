from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ── Collections ─────────────────────────────────────────────────────────────


async def create_collection(
    db: AsyncSession, user_id: uuid.UUID, name: str, description: str | None
) -> dict[str, Any]:
    cid = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO collections (id, user_id, name, description)
            VALUES (:id, :uid, :name, :desc)
            """
        ),
        {"id": cid, "uid": str(user_id), "name": name, "desc": description},
    )
    await db.commit()
    return await get_collection(db, uuid.UUID(cid), user_id)  # type: ignore


async def get_collection(
    db: AsyncSession, collection_id: uuid.UUID, user_id: uuid.UUID
) -> dict[str, Any] | None:
    row = await db.execute(
        text(
            """
            SELECT c.*, count(cp.paper_id) as paper_count
            FROM collections c
            LEFT JOIN collection_papers cp ON cp.collection_id = c.id
            WHERE c.id = :cid AND c.user_id = :uid
            GROUP BY c.id
            """
        ),
        {"cid": str(collection_id), "uid": str(user_id)},
    )
    res = row.mappings().first()
    return dict(res) if res else None


async def list_collections(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * per_page
    rows = await db.execute(
        text(
            """
            SELECT c.*, count(cp.paper_id) as paper_count
            FROM collections c
            LEFT JOIN collection_papers cp ON cp.collection_id = c.id
            WHERE c.user_id = :uid
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT :lim OFFSET :off
            """
        ),
        {"uid": str(user_id), "lim": per_page, "off": offset},
    )
    items = [dict(r) for r in rows.mappings()]
    count_row = await db.execute(
        text("SELECT count(*) FROM collections WHERE user_id = :uid"),
        {"uid": str(user_id)},
    )
    total = count_row.scalar() or 0
    return items, total


async def update_collection(
    db: AsyncSession,
    collection_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any] | None:
    updates: list[str] = ["updated_at = now()"]
    params: dict[str, Any] = {"cid": str(collection_id), "uid": str(user_id)}
    if name is not None:
        updates.append("name = :name")
        params["name"] = name
    if description is not None:
        updates.append("description = :desc")
        params["desc"] = description

    await db.execute(
        text(f"UPDATE collections SET {', '.join(updates)} WHERE id = :cid AND user_id = :uid"),
        params,
    )
    await db.commit()
    return await get_collection(db, collection_id, user_id)


async def delete_collection(db: AsyncSession, collection_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    res = await db.execute(
        text("DELETE FROM collections WHERE id = :cid AND user_id = :uid"),
        {"cid": str(collection_id), "uid": str(user_id)},
    )
    await db.commit()
    return res.rowcount > 0


async def add_paper_to_collection(
    db: AsyncSession, collection_id: uuid.UUID, user_id: uuid.UUID, paper_id: uuid.UUID
) -> bool:
    col = await get_collection(db, collection_id, user_id)
    if not col:
        return False
    await db.execute(
        text(
            """
            INSERT INTO collection_papers (collection_id, paper_id)
            VALUES (:cid, :pid)
            ON CONFLICT DO NOTHING
            """
        ),
        {"cid": str(collection_id), "pid": str(paper_id)},
    )
    await db.commit()
    return True


async def remove_paper_from_collection(
    db: AsyncSession, collection_id: uuid.UUID, user_id: uuid.UUID, paper_id: uuid.UUID
) -> bool:
    col = await get_collection(db, collection_id, user_id)
    if not col:
        return False
    res = await db.execute(
        text("DELETE FROM collection_papers WHERE collection_id = :cid AND paper_id = :pid"),
        {"cid": str(collection_id), "pid": str(paper_id)},
    )
    await db.commit()
    return res.rowcount > 0


# ── Saved Papers ────────────────────────────────────────────────────────────


async def save_paper(db: AsyncSession, user_id: uuid.UUID, paper_id: uuid.UUID) -> dict[str, Any]:
    sid = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO saved_papers (id, user_id, paper_id)
            VALUES (:id, :uid, :pid)
            ON CONFLICT (user_id, paper_id) DO NOTHING
            """
        ),
        {"id": sid, "uid": str(user_id), "pid": str(paper_id)},
    )
    await db.commit()
    return {"id": sid, "user_id": user_id, "paper_id": paper_id}


async def unsave_paper(db: AsyncSession, user_id: uuid.UUID, paper_id: uuid.UUID) -> bool:
    res = await db.execute(
        text("DELETE FROM saved_papers WHERE user_id = :uid AND paper_id = :pid"),
        {"uid": str(user_id), "pid": str(paper_id)},
    )
    await db.commit()
    return res.rowcount > 0


async def list_saved_papers(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * per_page
    rows = await db.execute(
        text(
            """
            SELECT sp.id, sp.paper_id, sp.saved_at, p.title as paper_title, p.year as paper_year
            FROM saved_papers sp
            JOIN papers p ON p.id = sp.paper_id
            WHERE sp.user_id = :uid
            ORDER BY sp.saved_at DESC
            LIMIT :lim OFFSET :off
            """
        ),
        {"uid": str(user_id), "lim": per_page, "off": offset},
    )
    items = [dict(r) for r in rows.mappings()]
    count_row = await db.execute(
        text("SELECT count(*) FROM saved_papers WHERE user_id = :uid"),
        {"uid": str(user_id)},
    )
    total = count_row.scalar() or 0
    return items, total


# ── Notes ───────────────────────────────────────────────────────────────────


async def create_note(
    db: AsyncSession, user_id: uuid.UUID, paper_id: uuid.UUID, content: str
) -> dict[str, Any]:
    nid = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO notes (id, user_id, paper_id, content)
            VALUES (:id, :uid, :pid, :content)
            """
        ),
        {"id": nid, "uid": str(user_id), "pid": str(paper_id), "content": content},
    )
    await db.commit()
    row = await db.execute(
        text("SELECT * FROM notes WHERE id = :nid"),
        {"nid": nid},
    )
    return dict(row.mappings().first())  # type: ignore


async def list_notes(
    db: AsyncSession,
    user_id: uuid.UUID,
    paper_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * per_page
    query = "SELECT * FROM notes WHERE user_id = :uid"
    params: dict[str, Any] = {"uid": str(user_id), "lim": per_page, "off": offset}
    if paper_id:
        query += " AND paper_id = :pid"
        params["pid"] = str(paper_id)
    query += " ORDER BY updated_at DESC LIMIT :lim OFFSET :off"

    rows = await db.execute(text(query), params)
    items = [dict(r) for r in rows.mappings()]
    count_row = await db.execute(
        text(f"SELECT count(*) FROM notes WHERE user_id = :uid {'AND paper_id = :pid' if paper_id else ''}"),
        params,
    )
    total = count_row.scalar() or 0
    return items, total


async def delete_note(db: AsyncSession, note_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    res = await db.execute(
        text("DELETE FROM notes WHERE id = :nid AND user_id = :uid"),
        {"nid": str(note_id), "uid": str(user_id)},
    )
    await db.commit()
    return res.rowcount > 0


# ── Reading Progress ────────────────────────────────────────────────────────


async def upsert_reading_progress(
    db: AsyncSession, user_id: uuid.UUID, paper_id: uuid.UUID, status_val: str
) -> dict[str, Any]:
    await db.execute(
        text(
            """
            INSERT INTO reading_progress (id, user_id, paper_id, status, updated_at)
            VALUES (:id, :uid, :pid, :status, now())
            ON CONFLICT (user_id, paper_id)
            DO UPDATE SET status = EXCLUDED.status, updated_at = now()
            """
        ),
        {"id": str(uuid.uuid4()), "uid": str(user_id), "pid": str(paper_id), "status": status_val},
    )
    await db.commit()
    return {"paper_id": paper_id, "status": status_val}


async def get_reading_progress(
    db: AsyncSession, user_id: uuid.UUID, paper_id: uuid.UUID
) -> dict[str, Any] | None:
    row = await db.execute(
        text("SELECT * FROM reading_progress WHERE user_id = :uid AND paper_id = :pid"),
        {"uid": str(user_id), "pid": str(paper_id)},
    )
    res = row.mappings().first()
    return dict(res) if res else None
