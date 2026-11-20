from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def enqueue(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID | str,
    operation: str = "upsert",
) -> str:
    """Enqueue an indexing operation into the durable outbox table."""
    queue_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO qdrant_indexing_queue (id, entity_type, entity_id, operation, status)
            VALUES (:id, :type, :eid, :op, 'pending')
            """
        ),
        {"id": queue_id, "type": entity_type, "eid": str(entity_id), "op": operation},
    )
    return queue_id


async def fetch_pending(db: AsyncSession, limit: int = 50) -> list[dict[str, Any]]:
    """Fetch pending or retryable failed queue items."""
    rows = await db.execute(
        text(
            """
            SELECT * FROM qdrant_indexing_queue
            WHERE status = 'pending' OR (status = 'failed' AND attempts < 5)
            ORDER BY created_at ASC
            LIMIT :lim
            """
        ),
        {"lim": limit},
    )
    return [dict(r) for r in rows.mappings()]


async def mark_processing(db: AsyncSession, item_id: str) -> None:
    await db.execute(
        text(
            """
            UPDATE qdrant_indexing_queue
            SET status = 'processing', attempts = attempts + 1
            WHERE id = :id
            """
        ),
        {"id": item_id},
    )
    await db.commit()


async def mark_done(db: AsyncSession, item_id: str) -> None:
    await db.execute(
        text(
            """
            UPDATE qdrant_indexing_queue
            SET status = 'done', processed_at = now()
            WHERE id = :id
            """
        ),
        {"id": item_id},
    )
    await db.commit()


async def mark_failed(db: AsyncSession, item_id: str, error_message: str) -> None:
    await db.execute(
        text(
            """
            UPDATE qdrant_indexing_queue
            SET status = 'failed', last_error = :err
            WHERE id = :id
            """
        ),
        {"id": item_id, "err": error_message[:1000]},
    )
    await db.commit()
