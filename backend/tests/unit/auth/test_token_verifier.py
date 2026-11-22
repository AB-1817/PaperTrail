from __future__ import annotations

import time
import uuid

import jwt as pyjwt
import pytest

from app.auth.token_verifier import TokenVerificationError, verify_token

SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"
ISSUER = "http://localhost:54321/auth/v1"


def _make_token(
    sub: str | None = None,
    exp_offset: int = 3600,
    aud: str = "authenticated",
    iss: str = ISSUER,
    secret: str = SECRET,
) -> str:
    payload: dict = {
        "sub": sub or str(uuid.uuid4()),
        "email": "test@example.com",
        "role": "authenticated",
        "aud": aud,
        "iss": iss,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_offset,
    }
    return pyjwt.encode(payload, secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_valid_token(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", ISSUER)
    # Reset cached settings
    from app.core.config import get_settings

    get_settings.cache_clear()

    token = _make_token()
    claims = await verify_token(token)
    assert claims.user_id is not None
    assert claims.email == "test@example.com"
    assert claims.role == "authenticated"


@pytest.mark.asyncio
async def test_expired_token(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", ISSUER)
    from app.core.config import get_settings

    get_settings.cache_clear()

    token = _make_token(exp_offset=-1)
    with pytest.raises(TokenVerificationError, match="expired"):
        await verify_token(token)


@pytest.mark.asyncio
async def test_wrong_issuer(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", ISSUER)
    from app.core.config import get_settings

    get_settings.cache_clear()

    token = _make_token(iss="https://evil.example.com/auth/v1")
    with pytest.raises(TokenVerificationError, match="issuer"):
        await verify_token(token)


@pytest.mark.asyncio
async def test_wrong_audience(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", ISSUER)
    from app.core.config import get_settings

    get_settings.cache_clear()

    token = _make_token(aud="anon")
    with pytest.raises(TokenVerificationError, match="audience"):
        await verify_token(token)


@pytest.mark.asyncio
async def test_missing_sub(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", ISSUER)
    from app.core.config import get_settings

    get_settings.cache_clear()

    import time

    import jwt as pyjwt

    # Token with sub key entirely absent
    payload_no_sub = {
        "email": "test@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": ISSUER,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token_no_sub = pyjwt.encode(payload_no_sub, SECRET, algorithm="HS256")
    with pytest.raises(TokenVerificationError):
        await verify_token(token_no_sub)


@pytest.mark.asyncio
async def test_wrong_secret(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", ISSUER)
    from app.core.config import get_settings

    get_settings.cache_clear()

    token = _make_token(secret="a-completely-different-secret-that-is-long-enough")
    with pytest.raises(TokenVerificationError):
        await verify_token(token)
