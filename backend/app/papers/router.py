from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.papers import service
from app.papers.schemas import PaperListResponse, PaperResponse

router = APIRouter(prefix="/papers", tags=["papers"])


# List papers -- must be declared BEFORE any path-param routes
@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaperListResponse:
    """Paginated list of papers in the PaperTrail library."""
    return await service.list_papers(db, page, per_page)


# References sub-route -- must be before the :path catch-all
@router.get("/{paper_id}/references")
async def get_paper_references(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Citation references made by this paper (UUID or DOI)."""
    refs = await service.get_references(db, paper_id)
    return {"data": refs, "meta": {"total": len(refs)}, "error": None}


# Single paper catch-all -- :path so DOIs with slashes work (e.g. 10.1016/j.xxx)
@router.get("/{paper_id:path}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaperResponse:
    """Fetch complete metadata for a single research paper by UUID or DOI."""
    return await service.get_paper(db, paper_id)
