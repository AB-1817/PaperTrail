from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_seed_graph(paper_id: str, db: AsyncSession) -> dict[str, Any]:
    """
    Returns graph representation centered around paper_id:
    - Target paper node
    - Direct citations (papers it cites)
    - Direct cited_by (papers that cite it)
    """
    pid_str = str(paper_id)

    # 1. Fetch seed paper from DB if possible
    seed = None
    try:
        seed_row = await db.execute(
            text(
                "SELECT id, title, year, venue, open_access FROM papers WHERE id = :pid OR doi = :pid"
            ),
            {"pid": pid_str},
        )
        seed = seed_row.mappings().first()
    except Exception:
        pass

    if not seed:
        return {"nodes": [], "edges": []}

    nodes: dict[str, dict[str, Any]] = {
        pid_str: {
            "id": pid_str,
            "title": seed["title"],
            "year": seed["year"],
            "open_access": seed["open_access"],
            "is_seed": True,
        }
    }
    edges: list[dict[str, Any]] = []

    # 2. Citations made by this paper (outward)
    try:
        cites_rows = await db.execute(
            text(
                """
                SELECT pr.cited_paper_id as target_id, p.title, p.year, p.open_access
                FROM paper_references pr
                JOIN papers p ON p.id = pr.cited_paper_id
                WHERE pr.citing_paper_id = :pid
                LIMIT 25
                """
            ),
            {"pid": pid_str},
        )
        for r in cites_rows.mappings():
            tid = str(r["target_id"])
            if tid not in nodes:
                nodes[tid] = {
                    "id": tid,
                    "title": r["title"],
                    "year": r["year"],
                    "open_access": r["open_access"],
                    "is_seed": False,
                }
            edges.append({"source": pid_str, "target": tid, "type": "cites"})
    except Exception:
        pass

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }


async def expand_node(
    paper_id: str, existing_node_ids: set[str], db: AsyncSession
) -> dict[str, Any]:
    full_graph = await get_seed_graph(paper_id, db)
    new_nodes = [n for n in full_graph["nodes"] if n["id"] not in existing_node_ids]
    return {
        "nodes": new_nodes,
        "edges": full_graph["edges"],
    }
