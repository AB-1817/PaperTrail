from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.graph import edge_resolver

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/seed/{paper_id}")
async def get_seed_graph(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    graph_data = await edge_resolver.get_seed_graph(paper_id, db)
    return {"data": graph_data, "meta": None, "error": None}


@router.get("/expand/{paper_id}")
async def expand_graph_node(
    paper_id: uuid.UUID,
    existing_ids: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    existing_set = {id_str.strip() for id_str in existing_ids.split(",") if id_str.strip()}
    res = await edge_resolver.expand_node(paper_id, existing_set, db)
    return {"data": res, "meta": None, "error": None}


@router.get("/topics")
async def list_graph_topics(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await db.execute(
        text("SELECT topic, count(*) as count FROM paper_topics GROUP BY topic ORDER BY count DESC LIMIT 50")
    )
    items = [dict(r) for r in rows.mappings()]
    return {"data": items, "meta": {"total": len(items)}, "error": None}
