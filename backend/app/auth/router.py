from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    display_name: str | None
    bio: str | None
    interests: list[str]


@router.get("/me", response_model=ProfileResponse)
async def get_me(
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    from sqlalchemy import text

    row = await db.execute(
        text("SELECT id, display_name, bio, interests FROM profiles WHERE id = :uid"),
        {"uid": str(current_user.user_id)},
    )
    profile = row.mappings().first()

    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return ProfileResponse(
        id=profile["id"],
        email=current_user.email,
        display_name=profile["display_name"],
        bio=profile["bio"],
        interests=profile["interests"] or [],
    )


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    interests: list[str] | None = None


@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    body: ProfileUpdateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    from sqlalchemy import text

    updates: dict[str, object] = {"uid": str(current_user.user_id)}
    set_clauses: list[str] = ["updated_at = now()"]

    if body.display_name is not None:
        set_clauses.append("display_name = :display_name")
        updates["display_name"] = body.display_name
    if body.bio is not None:
        set_clauses.append("bio = :bio")
        updates["bio"] = body.bio
    if body.interests is not None:
        set_clauses.append("interests = :interests")
        updates["interests"] = body.interests

    await db.execute(
        text(f"UPDATE profiles SET {', '.join(set_clauses)} WHERE id = :uid"),
        updates,
    )

    return await get_me(current_user=current_user, db=db)
