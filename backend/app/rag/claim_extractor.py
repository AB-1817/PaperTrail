from __future__ import annotations

import re

_CITATION_PATTERN = re.compile(r"\[CITATION:([^\]]+)\]")


def extract_citations(response_text: str) -> list[dict[str, str]]:
    """
    Extract claim-to-citation mappings from [CITATION:chunk_id] markers.
    Returns list of dicts: {"claim_text": str, "chunk_id": str}
    """
    results: list[dict[str, str]] = []

    # Split by sentence or marker
    sentences = re.split(r"(?<=[.!?])\s+", response_text)
    for sent in sentences:
        matches = _CITATION_PATTERN.findall(sent)
        if matches:
            # Clean claim text of citation tags
            clean_claim = _CITATION_PATTERN.sub("", sent).strip()
            for chunk_id in matches:
                results.append({"claim_text": clean_claim, "chunk_id": chunk_id.strip()})

    return results
