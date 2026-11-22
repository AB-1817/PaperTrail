from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel


class AuthorResponse(BaseModel):
    id: uuid.UUID | None = None
    name: str
    family_name: str | None = None
    orcid: str | None = None
    position: int = 1


class PaperResponse(BaseModel):
    id: str
    doi: str | None = None
    title: str
    abstract: str | None = None
    year: int | None = None
    venue: str | None = None
    volume: str | None = None
    issue: str | None = None
    open_access: bool = False
    oa_url: str | None = None
    has_abstract: bool = False
    has_references: bool = False
    authors: list[AuthorResponse] = []
    topics: list[str] = []
    source_providers: list[str] = []


class PaperListResponse(BaseModel):
    data: list[PaperResponse]
    meta: dict[str, Any]
    error: Any = None
