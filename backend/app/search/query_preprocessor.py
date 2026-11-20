from __future__ import annotations

import re
from dataclasses import dataclass, field

_FIELD = re.compile(r"\b(author|doi|title|year):(\S+)", re.IGNORECASE)


@dataclass
class ParsedQuery:
    text: str
    fields: dict[str, str] = field(default_factory=dict)
    non_ascii: bool = False


def preprocess(raw: str) -> ParsedQuery:
    collapsed = re.sub(r"\s+", " ", raw).strip()
    if len(collapsed) > 500:
        collapsed = collapsed[:500].rstrip()
    fields: dict[str, str] = {}

    def _capture(match: re.Match[str]) -> str:
        fields[match.group(1).lower()] = match.group(2)
        return " "

    without_fields = _FIELD.sub(_capture, collapsed)
    text = re.sub(r"\s+", " ", without_fields).strip()
    if len(text) < 2 and not fields.get("doi"):
        raise ValueError("Query must be at least 2 characters")
    if not text and fields.get("doi"):
        text = fields["doi"]
    return ParsedQuery(text=text.lower(), fields=fields, non_ascii=any(ord(ch) > 127 for ch in text))
