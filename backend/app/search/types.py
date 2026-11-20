from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PaperDoc:
    id: str
    title: str
    abstract: str | None
    year: int | None
    venue: str | None
    open_access: bool
    doi: str | None
    topics: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)


@dataclass
class RankedPaper:
    paper: PaperDoc
    score: float
    bm25_score: float | None
    dense_score: float | None
    rerank_score: float | None
    explanation: dict[str, object]
