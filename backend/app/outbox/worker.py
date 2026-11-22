from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.embeddings.model_wrapper import embed_texts
from app.outbox import indexing_queue

logger = structlog.get_logger(__name__)


async def is_qdrant_available(settings: Any) -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.qdrant_url}/healthz")
            return response.status_code == 200
    except Exception:
        return False


async def process_outbox_batch() -> int:
    """Process a single batch of pending outbox entries."""
    settings = get_settings()
    if not await is_qdrant_available(settings):
        return 0

    qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    collection_name = "paper_abstracts"
    try:
        qdrant.get_collection(collection_name)
    except Exception:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )

    async with AsyncSessionLocal() as db:
        pending_items = await indexing_queue.fetch_pending(db, limit=20)
        if not pending_items:
            return 0

        processed = 0
        for item in pending_items:
            item_id = str(item["id"])
            entity_id = str(item["entity_id"])
            entity_type = item["entity_type"]
            operation = item["operation"]

            await indexing_queue.mark_processing(db, item_id)

            try:
                if operation == "delete":
                    qdrant.delete(
                        collection_name=collection_name,
                        points_selector=[entity_id],
                    )
                elif entity_type == "paper":
                    row = await db.execute(
                        text("SELECT title, abstract FROM papers WHERE id = :id"),
                        {"id": entity_id},
                    )
                    paper = row.mappings().first()
                    if paper:
                        doc_text = f"{paper['title']}\n{paper['abstract'] or ''}"
                        vector = embed_texts(
                            [doc_text],
                            backend=settings.embedding_backend,
                            dimensions=settings.embedding_dimensions,
                        )[0]
                        qdrant.upsert(
                            collection_name=collection_name,
                            points=[
                                PointStruct(
                                    id=entity_id, vector=vector, payload={"entity_type": "paper"}
                                )
                            ],
                        )
                elif entity_type == "chunk":
                    row = await db.execute(
                        text(
                            "SELECT text, paper_id, page_number, section FROM document_chunks WHERE id = :id"
                        ),
                        {"id": entity_id},
                    )
                    chunk = row.mappings().first()
                    if chunk:
                        vector = embed_texts(
                            [chunk["text"]],
                            backend=settings.embedding_backend,
                            dimensions=settings.embedding_dimensions,
                        )[0]
                        qdrant.upsert(
                            collection_name=collection_name,
                            points=[
                                PointStruct(
                                    id=entity_id,
                                    vector=vector,
                                    payload={
                                        "entity_type": "chunk",
                                        "paper_id": str(chunk["paper_id"]),
                                        "page_number": chunk["page_number"],
                                        "section": chunk["section"],
                                    },
                                )
                            ],
                        )

                await indexing_queue.mark_done(db, item_id)
                processed += 1
            except Exception as exc:
                logger.error("outbox_processing_item_error", item_id=item_id, error=str(exc))
                await indexing_queue.mark_failed(db, item_id, str(exc))

        return processed


async def outbox_worker_loop() -> None:
    """Background polling loop for durable outbox processing."""
    logger.info("outbox_worker_loop_started")
    unavailable_notified = False
    while True:
        try:
            settings = get_settings()
            if not await is_qdrant_available(settings):
                if not unavailable_notified:
                    logger.warning(
                        "outbox_worker_qdrant_unavailable",
                        qdrant_url=settings.qdrant_url,
                        retry_in_seconds=15,
                    )
                    unavailable_notified = True
                await asyncio.sleep(15)
                continue

            if unavailable_notified:
                logger.info("outbox_worker_qdrant_recovered", qdrant_url=settings.qdrant_url)
                unavailable_notified = False

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
