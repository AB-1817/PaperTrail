from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def validate_structural(
    chunk_id_str: str,
    retrieved_chunk_ids: set[str],
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Layer 1: Structural Citation Validation.
    Verifies that the citation refers to a real, retrievable chunk in the database
    and was part of the retrieved candidate set.
    """
    try:
        cid = uuid.UUID(chunk_id_str)
    except ValueError:
        return {
            "chunk_id_exists": False,
            "chunk_in_retrieved_set": False,
            "structural_valid": False,
            "passage": "",
            "page_number": None,
            "paper_id": None,
        }

    in_retrieved = chunk_id_str in retrieved_chunk_ids

    row = await db.execute(
        text("SELECT id, paper_id, text, page_number FROM document_chunks WHERE id = :id"),
        {"id": str(cid)},
    )
    chunk = row.mappings().first()

    if not chunk:
        return {
            "chunk_id_exists": False,
            "chunk_in_retrieved_set": in_retrieved,
            "structural_valid": False,
            "passage": "",
            "page_number": None,
            "paper_id": None,
        }

    return {
        "chunk_id_exists": True,
        "chunk_in_retrieved_set": in_retrieved,
        "structural_valid": in_retrieved,
        "passage": chunk["text"],
        "page_number": chunk["page_number"],
        "paper_id": chunk["paper_id"],
    }
