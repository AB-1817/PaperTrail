from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
import structlog

from app.documents.parser_interface import ParsedDocument, ParsedSection

logger = structlog.get_logger(__name__)


class GROBIDParser:
    parser_name = "grobid"

    def __init__(self, base_url: str = "http://localhost:8070") -> None:
        self.base_url = base_url

    def parse(self, pdf_path: Path) -> ParsedDocument:
        url = f"{self.base_url}/api/processFulltextDocument"

        with open(pdf_path, "rb") as f:
            files = {"input": (pdf_path.name, f, "application/pdf")}
            response = httpx.post(url, files=files, timeout=60.0)
            response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}

        title_elem = root.find(".//tei:titleStmt/tei:title", ns)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else None

        sections: list[ParsedSection] = []
        char_offset = 0

        for div in root.findall(".//tei:body/tei:div", ns):
            head_elem = div.find("tei:head", ns)
            heading = head_elem.text.strip() if head_elem is not None and head_elem.text else None

            paras = [p.text.strip() for p in div.findall("tei:p", ns) if p.text]
            text = "\n\n".join(paras).strip()
            if not text:
                continue

            sections.append(
                ParsedSection(
                    heading=heading,
                    text=text,
                    page_start=1,
                    page_end=1,
                    char_offset_start=char_offset,
                )
            )
            char_offset += len(text) + 2

        return ParsedDocument(
            title=title,
            sections=sections,
            page_count=1,
            parser_name=self.parser_name,
        )
