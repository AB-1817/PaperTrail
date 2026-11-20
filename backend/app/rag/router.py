from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db
from app.rag.orchestrator import rag_query

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    paper_ids: list[uuid.UUID] | None = None


@router.post("/query", status_code=status.HTTP_200_OK)
async def query_rag(
    body: RAGQueryRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    res = await rag_query(
        question=body.question,
        paper_ids=body.paper_ids,
        user_id=current_user.user_id,
        db=db,
    )
    return {"data": res, "meta": None, "error": None}
