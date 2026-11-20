from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class NormalizedAuthor:
    name: str
    family_name: str | None
    orcid: str | None
    institution: str | None
    position: int


@dataclass
class NormalizedPaper:
    doi: str | None
    title: str
    abstract: str | None
    year: int | None
    venue: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    open_access: bool
    oa_url: str | None
    access_license: str | None
    authors: list[NormalizedAuthor]
    topics: list[str]
    reference_dois: list[str]
    source_provider: str
    provider_id: str
    raw_metadata: dict[str, object]
    fetched_at: datetime
    has_abstract: bool
    has_references: bool
    has_full_text_url: bool


@dataclass
class OALocation:
    doi: str
    is_oa: bool
    pdf_url: str | None
    license: str | None


class ProviderAdapter(Protocol):
    name: str

    async def search(self, query: str, limit: int) -> list[NormalizedPaper]: ...


@dataclass
class RateLimited(Exception):
    provider: str

    def __str__(self) -> str:
        return f"{self.provider} rate limit exceeded"


def family_name_from(display_name: str) -> str | None:
    parts = [part for part in display_name.replace(",", " ").split() if part]
    if not parts:
        return None
    return parts[-1]


def empty_paper_kwargs() -> dict[str, object]:
    return {"authors": field(default_factory=list)}
