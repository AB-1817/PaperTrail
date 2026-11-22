from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.health import router as health_router
from app.core.logging import configure_logging, get_logger
from app.documents.router import router as documents_router
from app.evaluation.router import router as evaluation_router
from app.graph.router import router as graph_router
from app.ingestion.router import router as ingestion_router
from app.papers.router import router as papers_router
from app.rag.router import router as rag_router
from app.recommendations.router import router as recommendations_router
from app.reviews.router import router as reviews_router
from app.search.router import router as search_router
from app.workspace.router import collections_router
from app.workspace.router import router as workspace_router

configure_logging()
logger = get_logger(__name__)

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from app.core.sentry import init_sentry
    from app.outbox.worker import outbox_worker_loop

    init_sentry()
    worker_task = asyncio.create_task(outbox_worker_loop())
    try:
        yield
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="PaperTrail API",
        version="0.3.0",
        docs_url="/api/docs" if settings.environment == "development" else None,
        redoc_url="/api/redoc" if settings.environment == "development" else None,
        openapi_url="/api/openapi.json" if settings.environment == "development" else None,
        lifespan=lifespan,
    )

    # ── Rate limiting ──────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # ── CORS ───────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request ID middleware ──────────────────────────────────────────────────
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: object) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response: Response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Request body size limit ────────────────────────────────────────────────
    @app.middleware("http")
    async def body_size_limit(request: Request, call_next: object) -> Response:
        content_length = request.headers.get("content-length")
        upload_paths = ["/api/v1/documents/ingest"]
        limit = 50 * 1024 * 1024 if request.url.path in upload_paths else 1 * 1024 * 1024
        if content_length and int(content_length) > limit:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=413,
                content={
                    "data": None,
                    "meta": None,
                    "error": {
                        "code": "REQUEST_TOO_LARGE",
                        "message": f"Request body exceeds {limit} bytes",
                        "request_id": getattr(request.state, "request_id", ""),
                    },
                },
            )
        return await call_next(request)  # type: ignore[operator,return-value]

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers (all prefixed under /api/v1) ──────────────────────────────────
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(papers_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(ingestion_router, prefix="/api/v1")
    app.include_router(workspace_router, prefix="/api/v1")
    app.include_router(collections_router, prefix="/api/v1")
    app.include_router(recommendations_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(rag_router, prefix="/api/v1")
    app.include_router(reviews_router, prefix="/api/v1")
    app.include_router(graph_router, prefix="/api/v1")
    app.include_router(evaluation_router, prefix="/api/v1")

    return app


app = create_app()
