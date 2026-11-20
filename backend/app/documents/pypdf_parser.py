from __future__ import annotations

from pathlib import Path

from app.documents.parser_interface import ParsedDocument, ParsedSection


class PyPDFParser:
    parser_name = "pypdf"

    def parse(self, pdf_path: Path) -> ParsedDocument:
        import pypdf

        reader = pypdf.PdfReader(str(pdf_path))
        sections: list[ParsedSection] = []
        char_offset = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue

            sections.append(
                ParsedSection(
                    heading=f"Page {page_idx}",
                    text=text,
                    page_start=page_idx,
                    page_end=page_idx,
                    char_offset_start=char_offset,
                )
            )
            char_offset += len(text) + 1

        return ParsedDocument(
            title=None,
            sections=sections,
            page_count=len(reader.pages),
            parser_name=self.parser_name,
        )
