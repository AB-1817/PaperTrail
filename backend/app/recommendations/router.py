from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db
from app.recommendations.citation_ranker import citation_based_recommend
from app.recommendations.content_ranker import content_based_recommend
from app.recommendations.diversity_filter import mmr_diversity_filter
from app.recommendations.personalized_ranker import personalized_recommend
from app.recommendations.schemas import EventCreate

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/personalized")
async def get_personalized_recommendations(
    limit: int = Query(default=20, ge=1, le=50),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    recs = await personalized_recommend(current_user.user_id, db, limit=limit)
    diverse = mmr_diversity_filter(recs, limit=limit)
    return {"data": diverse, "meta": {"total": len(diverse)}, "error": None}


@router.get("/content/{paper_id}")
async def get_content_recommendations(
    paper_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    recs = await content_based_recommend(paper_id, user_id=None, db=db, limit=limit)
    return {"data": recs, "meta": {"total": len(recs)}, "error": None}


@router.get("/citation/{paper_id}")
async def get_citation_recommendations(
    paper_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    recs = await citation_based_recommend(paper_id, user_id=None, db=db, limit=limit)
    return {"data": recs, "meta": {"total": len(recs)}, "error": None}


@router.post("/events")
async def record_recommendation_event(
    body: EventCreate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await db.execute(
        text(
            """
            INSERT INTO recommendation_events (id, user_id, paper_id, event_type, source)
            VALUES (:id, :uid, :pid, :type, :src)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "uid": str(current_user.user_id),
            "pid": str(body.paper_id),
            "type": body.event_type,
            "src": body.source,
        },
    )
    await db.commit()
    return {"data": {"status": "recorded"}, "meta": None, "error": None}
