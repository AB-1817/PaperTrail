from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db
from app.reviews import exporter, matrix_builder, projects, synthesis_generator
from app.reviews.schemas import ReviewAddPaper, ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    item = await projects.create_review(db, current_user.user_id, body.title, body.description)
    return ReviewResponse(**item)


@router.get("", response_model=dict[str, Any])
async def list_reviews(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    items, total = await projects.list_reviews(db, current_user.user_id, page, per_page)
    return {
        "data": [ReviewResponse(**i) for i in items],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "error": None,
    }


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    item = await projects.get_review(db, review_id, current_user.user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse(**item)


@router.get("/{review_id}/papers")
async def get_review_papers(
    review_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    papers = await projects.get_review_papers(db, review_id, current_user.user_id)
    return {"data": papers, "meta": {"total": len(papers)}, "error": None}


@router.post("/{review_id}/papers", status_code=status.HTTP_200_OK)
async def add_paper_to_review(
    review_id: uuid.UUID,
    body: ReviewAddPaper,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    from app.workspace.repository import paper_exists

    if not await paper_exists(db, body.paper_id):
        raise HTTPException(status_code=404, detail="Paper not found")

    ok = await projects.add_paper_to_review(db, review_id, current_user.user_id, body.paper_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"status": "added"}


@router.delete("/{review_id}/papers/{paper_id}", status_code=status.HTTP_200_OK)
async def remove_paper_from_review(
    review_id: uuid.UUID,
    paper_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ok = await projects.remove_paper_from_review(db, review_id, current_user.user_id, paper_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Paper not found in review")
    return {"status": "removed"}


@router.post("/{review_id}/sections/{section_type}/generate")
async def generate_review_section(
    review_id: uuid.UUID,
    section_type: str,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    res = await synthesis_generator.generate_section(
        review_id, section_type, current_user.user_id, db
    )
    return {"data": res, "meta": None, "error": None}


@router.get("/{review_id}/sections")
async def get_review_sections(
    review_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # Check ownership
    rev = await projects.get_review(db, review_id, current_user.user_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")

    rows = await db.execute(
        text("SELECT * FROM synthesis_sections WHERE review_id = :rid ORDER BY generated_at ASC"),
        {"rid": str(review_id)},
    )
    items = [dict(r) for r in rows.mappings()]
    return {"data": items, "meta": {"total": len(items)}, "error": None}


@router.get("/{review_id}/matrix")
async def get_review_matrix(
    review_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    matrix = await matrix_builder.build_comparison_matrix(review_id, current_user.user_id, db)
    return {"data": matrix, "meta": {"total": len(matrix)}, "error": None}


@router.get("/{review_id}/export")
async def export_review_markdown(
    review_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    rev = await projects.get_review(db, review_id, current_user.user_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")

    sec_rows = await db.execute(
        text("SELECT * FROM synthesis_sections WHERE review_id = :rid"),
        {"rid": str(review_id)},
    )
    sections = [dict(r) for r in sec_rows.mappings()]
    matrix = await matrix_builder.build_comparison_matrix(review_id, current_user.user_id, db)

    md_content = exporter.export_to_markdown(rev, sections, matrix)
    filename = f"literature_review_{review_id}.md"

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
