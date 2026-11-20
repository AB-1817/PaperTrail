from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Point at the local Supabase test DB before importing app modules
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_JWT_ISSUER", "http://localhost:54321/auth/v1")
os.environ.setdefault("SUPABASE_JWT_SECRET", "super-secret-jwt-token-with-at-least-32-characters-long")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


def make_jwt(user_id: uuid.UUID | None = None) -> str:
    """
    Create a signed HS256 JWT for testing.
    Uses the SUPABASE_JWT_SECRET from the environment.
    """
    import jwt as pyjwt
    import time

    uid = user_id or uuid.uuid4()
    secret = os.environ["SUPABASE_JWT_SECRET"]
    payload = {
        "sub": str(uid),
        "email": f"{uid}@test.example",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": os.environ["SUPABASE_JWT_ISSUER"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return pyjwt.encode(payload, secret, algorithm="HS256")


def auth_headers(user_id: uuid.UUID | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt(user_id)}"}
