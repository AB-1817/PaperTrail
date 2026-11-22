from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db
from app.documents.pipeline import process_document

router = APIRouter(prefix="/documents", tags=["documents"])


class IngestDocumentRequest(BaseModel):
    paper_id: uuid.UUID
    source_url: str
    access_type: str = Field(..., pattern="^(arxiv_oa|unpaywall_oa|user_upload)$")


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    body: IngestDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    doc_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO documents (id, paper_id, source_url, access_type, parse_status)
            VALUES (:id, :pid, :url, :type, 'pending')
            """
        ),
        {
            "id": doc_id,
            "pid": str(body.paper_id),
            "url": body.source_url,
            "type": body.access_type,
        },
    )
    await db.commit()

    background_tasks.add_task(
        process_document,
        document_id=uuid.UUID(doc_id),
        paper_id=body.paper_id,
        pdf_url=body.source_url,
        access_type=body.access_type,
        db=db,
    )

    return {"data": {"document_id": doc_id, "status": "pending"}, "meta": None, "error": None}


@router.get("/status/{document_id}")
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    row = await db.execute(
        text(
            "SELECT id, parse_status, parser_used, page_count, parsed_at FROM documents WHERE id = :id"
        ),
        {"id": str(document_id)},
    )
    item = row.mappings().first()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"data": dict(item), "meta": None, "error": None}


@router.get("/chunks/{paper_id}")
async def get_paper_chunks(
    paper_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    offset = (page - 1) * per_page
    rows = await db.execute(
        text(
            """
            SELECT id, chunk_index, page_number, section, token_count
            FROM document_chunks
            WHERE paper_id = :pid
            ORDER BY chunk_index ASC
            LIMIT :lim OFFSET :off
            """
        ),
        {"pid": str(paper_id), "lim": per_page, "off": offset},
    )
    items = [dict(r) for r in rows.mappings()]
    return {"data": items, "meta": {"total": len(items)}, "error": None}
