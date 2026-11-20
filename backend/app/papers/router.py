from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.papers import service
from app.papers.schemas import PaperListResponse, PaperResponse

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PaperResponse:
    """Fetch complete metadata for a single research paper."""
    return await service.get_paper(db, paper_id)


@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaperListResponse:
    """Paginated list of papers in the PaperTrail library."""
    return await service.list_papers(db, page, per_page)


@router.get("/{paper_id}/references")
async def get_paper_references(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Citation references made by this paper."""
    refs = await service.get_references(db, paper_id)
    return {"data": refs, "meta": {"total": len(refs)}, "error": None}
