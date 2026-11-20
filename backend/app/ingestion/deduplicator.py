from __future__ import annotations

from dataclasses import dataclass, field

from app.ingestion.normalizer import normalize_doi, normalize_title
from app.providers.base import NormalizedPaper


@dataclass
class ExistingPaper:
    id: str
    doi: str | None
    title_norm: str
    year: int | None
    first_author_family: str | None
    sources: set[tuple[str, str]] = field(default_factory=set)


@dataclass(frozen=True)
class DedupMatch:
    paper_id: str
    strategy: str


def first_family(paper: NormalizedPaper) -> str | None:
    ordered = sorted(paper.authors, key=lambda author: author.position)
    for author in ordered:
        if author.family_name:
            return author.family_name
    return None


def find_duplicate(candidate: NormalizedPaper, existing: list[ExistingPaper]) -> DedupMatch | None:
    """Match in blueprint order: DOI, then title+author+year, then provider id."""
    doi = normalize_doi(candidate.doi)
    if doi:
        for paper in existing:
            if paper.doi and normalize_doi(paper.doi) == doi:
                return DedupMatch(paper.id, "doi")

    family = first_family(candidate)
    title = normalize_title(candidate.title)
    if title and family and candidate.year is not None:
        family_key = family.lower()
        for paper in existing:
            if (
                paper.title_norm == title
                and paper.year == candidate.year
                and paper.first_author_family
                and paper.first_author_family.lower() == family_key
            ):
                return DedupMatch(paper.id, "title_author_year")

    source_key = (candidate.source_provider, candidate.provider_id)
    for paper in existing:
        if source_key in paper.sources:
            return DedupMatch(paper.id, "provider_id")
    return None


class DedupIndex:
    def __init__(self) -> None:
        self._papers: dict[str, ExistingPaper] = {}

    def add(self, paper: ExistingPaper) -> None:
        current = self._papers.get(paper.id)
        if current is None:
            self._papers[paper.id] = paper
            return
        current.sources |= paper.sources
        if current.doi is None:
            current.doi = paper.doi
        if current.first_author_family is None:
            current.first_author_family = paper.first_author_family

    def find(self, candidate: NormalizedPaper) -> DedupMatch | None:
        return find_duplicate(candidate, list(self._papers.values()))

    def papers(self) -> list[ExistingPaper]:
        return list(self._papers.values())


def reference_target(cited_paper_id: str | None, doi: str | None) -> dict[str, str | None] | None:
    """A reference row needs a cited paper or a DOI. Never invent either."""
    normalized = normalize_doi(doi)
    if cited_paper_id is None and normalized is None:
        return None
    return {"cited_paper_id": cited_paper_id, "doi_fallback": normalized}
