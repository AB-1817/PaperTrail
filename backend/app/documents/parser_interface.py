from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class ParsedSection:
    heading: str | None
    text: str
    page_start: int
    page_end: int
    char_offset_start: int


@dataclass
class ParsedDocument:
    title: str | None
    sections: list[ParsedSection]
    page_count: int
    parser_name: str


class DocumentParser(Protocol):
    parser_name: str

    def parse(self, pdf_path: Path) -> ParsedDocument: ...
