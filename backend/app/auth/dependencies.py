from __future__ import annotations

import uuid
from dataclasses import dataclass

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.token_verifier import TokenVerificationError, VerifiedClaims, verify_token
from app.core.db import get_db

logger = structlog.get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class UserContext:
    """
    The only trusted user identity object in the system.
    Constructed from a verified JWT — never from request body or query params.
    """

    user_id: uuid.UUID
    email: str | None
    role: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> UserContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        claims: VerifiedClaims = await verify_token(token)
    except TokenVerificationError as exc:
        logger.warning("auth_failed", reason=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Ensure profile row exists (idempotent — trigger handles it, this is a safety net)
    await _ensure_profile(db, claims.user_id)

    return UserContext(
        user_id=claims.user_id,
        email=claims.email,
        role=claims.role,
    )


async def _ensure_profile(db: AsyncSession, user_id: uuid.UUID) -> None:
    """
    Idempotently create a profile row if the Auth trigger hasn't fired yet.
    Uses ON CONFLICT DO NOTHING so it is safe to call on every request.
    """
    await db.execute(
        text("INSERT INTO profiles (id) VALUES (:uid) ON CONFLICT (id) DO NOTHING"),
        {"uid": str(user_id)},
    )
