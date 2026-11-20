from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db
from app.ingestion.orchestrator import run_ingestion

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionTriggerRequest(BaseModel):
    provider: str = Field(..., pattern="^(openalex|arxiv|semantic_scholar|crossref)$")
    query: str = Field(..., min_length=2, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)


class IngestionJobResponse(BaseModel):
    id: str
    provider: str
    query_or_scope: str | None
    status: str
    papers_found: int
    papers_inserted: int
    papers_updated: int
    errors: list[Any]
    started_at: str | None
    completed_at: str | None
    created_at: str


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion(
    body: IngestionTriggerRequest,
    background_tasks: BackgroundTasks,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    job_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO ingestion_jobs (id, provider, query_or_scope, status)
            VALUES (:id, :provider, :query, 'pending')
            """
        ),
        {"id": job_id, "provider": body.provider, "query": body.query},
    )
    await db.commit()

    background_tasks.add_task(
        run_ingestion,
        job_id=job_id,
        provider_name=body.provider,
        query=body.query,
        limit=body.limit,
        db=db,
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_job_status(
    job_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobResponse:
    row = await db.execute(
        text("SELECT * FROM ingestion_jobs WHERE id = :jid"),
        {"jid": job_id},
    )
    item = row.mappings().first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingestion job not found")

    return IngestionJobResponse(
        id=str(item["id"]),
        provider=item["provider"],
        query_or_scope=item["query_or_scope"],
        status=item["status"],
        papers_found=item["papers_found"],
        papers_inserted=item["papers_inserted"],
        papers_updated=item["papers_updated"],
        errors=item["errors"] or [],
        started_at=item["started_at"].isoformat() if item["started_at"] else None,
        completed_at=item["completed_at"].isoformat() if item["completed_at"] else None,
        created_at=item["created_at"].isoformat() if item["created_at"] else "",
    )


@router.get("/jobs")
async def list_jobs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    offset = (page - 1) * per_page
    rows = await db.execute(
        text("SELECT * FROM ingestion_jobs ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
        {"lim": per_page, "off": offset},
    )
    items = [dict(r) for r in rows.mappings()]
    count_row = await db.execute(text("SELECT count(*) FROM ingestion_jobs"))
    total = count_row.scalar() or 0

    return {
        "data": items,
        "meta": {"page": page, "per_page": per_page, "total": total},
        "error": None,
    }
