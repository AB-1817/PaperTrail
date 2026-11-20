from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import jwt
import structlog

from app.auth.jwks_client import jwks_client
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class TokenVerificationError(Exception):
    pass


@dataclass(frozen=True)
class VerifiedClaims:
    user_id: uuid.UUID
    email: str | None
    role: str


async def verify_token(token: str) -> VerifiedClaims:
    """
    Verify a Supabase JWT.

    Supabase projects use HS256 by default (signed with the JWT secret).
    RS256 projects expose a JWKS endpoint. We support both:
      - If supabase_jwt_secret is set → HS256 verification.
      - Otherwise → RS256 via JWKS.
    """
    settings = get_settings()

    try:
        if settings.supabase_jwt_secret:
            payload = _verify_hs256(token, settings)
        else:
            payload = await _verify_rs256(token, settings)
    except jwt.ExpiredSignatureError:
        raise TokenVerificationError("Token has expired")
    except jwt.InvalidAudienceError:
        raise TokenVerificationError("Invalid token audience")
    except jwt.InvalidIssuerError:
        raise TokenVerificationError("Invalid token issuer")
    except jwt.PyJWTError as exc:
        raise TokenVerificationError(f"Token verification failed: {exc}") from exc

    sub = payload.get("sub", "")
    if not sub or not str(sub).strip():
        raise TokenVerificationError("Token missing or empty 'sub' claim")

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise TokenVerificationError("Token 'sub' claim is not a valid UUID")

    return VerifiedClaims(
        user_id=user_id,
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
    )


def _verify_hs256(token: str, settings: Any) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience="authenticated",
        issuer=settings.supabase_jwt_issuer,
        options={"require": ["exp", "iss", "aud"]},
    )
    # PyJWT's 'require' accepts empty strings; enforce non-empty sub explicitly
    if not payload.get("sub", "").strip():
        raise jwt.MissingRequiredClaimError("sub")
    return payload  # type: ignore[no-any-return]


async def _verify_rs256(token: str, settings: Any) -> dict[str, Any]:
    # Decode header to find the key ID
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    keys = await jwks_client.get_keys()
    public_key = _find_key(keys, kid)

    if public_key is None:
        # Key not found — may be a rotation; force refresh once
        keys = await jwks_client.get_keys(force_refresh=True)
        public_key = _find_key(keys, kid)

    if public_key is None:
        raise TokenVerificationError(f"No matching JWKS key for kid='{kid}'")

    return jwt.decode(  # type: ignore[no-any-return]
        token,
        public_key,
        algorithms=["RS256"],
        audience="authenticated",
        issuer=settings.supabase_jwt_issuer,
        options={"require": ["sub", "exp", "iss", "aud"]},
    )


def _find_key(keys: list[dict[str, Any]], kid: str | None) -> Any:
    for key_data in keys:
        if kid is None or key_data.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
    return None
