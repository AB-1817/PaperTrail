from __future__ import annotations

import asyncio
from typing import Any

import structlog
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.embeddings.model_wrapper import embed_texts
from app.outbox import indexing_queue

logger = structlog.get_logger(__name__)


async def process_outbox_batch() -> int:
    """Process a single batch of pending outbox entries."""
    settings = get_settings()

    async with AsyncSessionLocal() as db:
        pending_items = await indexing_queue.fetch_pending(db, limit=20)
        if not pending_items:
            return 0

        processed = 0
        for item in pending_items:
            item_id = str(item["id"])
            entity_id = str(item["entity_id"])
            entity_type = item["entity_type"]

            await indexing_queue.mark_processing(db, item_id)

            try:
                if entity_type == "paper":
                    # Fetch paper text
                    row = await db.execute(
                        text("SELECT title, abstract FROM papers WHERE id = :id"),
                        {"id": entity_id},
                    )
                    paper = row.mappings().first()
                    if paper:
                        doc_text = f"{paper['title']}\n{paper['abstract'] or ''}"
                        # Generate embedding using active backend
                        embed_texts([doc_text], backend=settings.embedding_backend)
                        logger.info("vector_indexed_simulated", entity_id=entity_id)

                await indexing_queue.mark_done(db, item_id)
                processed += 1
            except Exception as exc:
                logger.error("outbox_processing_item_error", item_id=item_id, error=str(exc))
                await indexing_queue.mark_failed(db, item_id, str(exc))

        return processed


async def outbox_worker_loop() -> None:
    """Background polling loop for durable outbox processing."""
    logger.info("outbox_worker_loop_started")
    while True:
        try:
            count = await process_outbox_batch()
            if count == 0:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("outbox_worker_error", error=str(exc))
            await asyncio.sleep(5)
