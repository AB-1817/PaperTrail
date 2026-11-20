from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class AppError(Exception):
    """Domain error mapped to the standard API envelope."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class APIResponse(BaseModel):
    data: Any = None
    meta: dict[str, Any] | None = None
    error: ErrorDetail | None = None


def _error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None = None,
) -> JSONResponse:
    rid = request_id or str(uuid.uuid4())
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "meta": None,
            "error": {"code": code, "message": message, "request_id": rid},
        },
        headers={"X-Request-ID": rid},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        rid = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.info("app_error", code=exc.code, request_id=rid)
        return _error_response(exc.status_code, exc.code, exc.message, rid)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        rid = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.warning("validation_error", errors=exc.errors(), request_id=rid)
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            str(exc.errors()),
            rid,
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
        rid = getattr(request.state, "request_id", str(uuid.uuid4()))
        return _error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Resource not found", rid)

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Any) -> JSONResponse:
        rid = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.error("internal_server_error", exc_info=exc, request_id=rid)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "An unexpected error occurred",
            rid,
        )
