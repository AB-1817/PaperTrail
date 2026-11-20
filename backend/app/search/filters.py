from __future__ import annotations

from dataclasses import dataclass

from app.search.types import PaperDoc


@dataclass
class FilterSpec:
    year_from: int | None = None
    year_to: int | None = None
    open_access: bool | None = None
    topics: list[str] | None = None
    author: str | None = None
    doi: str | None = None


def build_qdrant_filter(spec: FilterSpec) -> dict[str, object] | None:
    """Filter payload applied inside Qdrant, before candidates are returned."""
    must: list[dict[str, object]] = []
    if spec.year_from is not None or spec.year_to is not None:
        bounds: dict[str, int] = {}
        if spec.year_from is not None:
            bounds["gte"] = spec.year_from
        if spec.year_to is not None:
            bounds["lte"] = spec.year_to
        must.append({"key": "year", "range": bounds})
    if spec.open_access is not None:
        must.append({"key": "open_access", "match": {"value": spec.open_access}})
    if spec.topics:
        must.append({"key": "topics", "match": {"any": spec.topics}})
    if not must:
        return None
    return {"must": must}


def apply_filters(papers: list[PaperDoc], spec: FilterSpec) -> list[PaperDoc]:
    selected: list[PaperDoc] = []
    for paper in papers:
        if spec.year_from is not None and (paper.year is None or paper.year < spec.year_from):
            continue
        if spec.year_to is not None and (paper.year is None or paper.year > spec.year_to):
            continue
        if spec.open_access is not None and paper.open_access != spec.open_access:
            continue
        if spec.topics:
            wanted = {topic.lower() for topic in spec.topics}
            have = {topic.lower() for topic in paper.topics}
            if not wanted & have:
                continue
        if spec.author:
            needle = spec.author.lower()
            if not any(needle in name.lower() for name in paper.authors):
                continue
        if spec.doi and (paper.doi or "").lower() != spec.doi.lower():
            continue
        selected.append(paper)
    return selected
