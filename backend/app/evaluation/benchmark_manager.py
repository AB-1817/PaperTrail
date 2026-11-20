from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_or_create_dataset(
    db: AsyncSession,
    name: str,
    version: str,
    description: str | None = None,
    domain: str = "ai_cs",
) -> str:
    row = await db.execute(
        text("SELECT id FROM evaluation_datasets WHERE name = :name AND version = :version"),
        {"name": name, "version": version},
    )
    existing = row.scalar()
    if existing:
        return str(existing)

    dataset_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO evaluation_datasets (id, name, version, description, domain)
            VALUES (:id, :name, :version, :desc, :domain)
            """
        ),
        {"id": dataset_id, "name": name, "version": version, "desc": description, "domain": domain},
    )
    await db.commit()
    return dataset_id


async def add_judgment(
    db: AsyncSession,
    dataset_id: str,
    query: str,
    paper_id: str,
    relevance: int,
    annotator: str,
    source: str = "manual_evaluation",
) -> None:
    await db.execute(
        text(
            """
            INSERT INTO relevance_judgments (dataset_id, query, paper_id, relevance, annotator, source)
            VALUES (:did, :query, :pid, :rel, :annotator, :source)
            ON CONFLICT (dataset_id, query, paper_id, annotator)
            DO UPDATE SET relevance = EXCLUDED.relevance, judged_at = now()
            """
        ),
        {
            "did": dataset_id,
            "query": query,
            "pid": paper_id,
            "rel": relevance,
            "annotator": annotator,
            "source": source,
        },
    )
    await db.commit()


async def get_judgments(db: AsyncSession, dataset_id: str) -> list[dict[str, Any]]:
    rows = await db.execute(
        text("SELECT * FROM relevance_judgments WHERE dataset_id = :did ORDER BY query"),
        {"did": dataset_id},
    )
    return [dict(r) for r in rows.mappings()]
