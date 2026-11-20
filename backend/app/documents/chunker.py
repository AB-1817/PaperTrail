from __future__ import annotations

import re
from typing import Any

from app.documents.parser_interface import ParsedDocument


def chunk_document(
    doc: ParsedDocument,
    target_tokens: int = 512,
    overlap_tokens: int = 64,
    min_tokens: int = 50,
) -> list[dict[str, Any]]:
    """
    Section-aware document chunking.
    Respects section boundaries without cross-section spillover.
    """
    chunks: list[dict[str, Any]] = []
    chunk_index = 0

    for section in doc.sections:
        text = section.text.strip()
        if not text:
            continue

        words = text.split()
        # Approximate tokens ~ words / 0.75
        est_tokens = int(len(words) / 0.75)

        if est_tokens <= target_tokens:
            if est_tokens >= min_tokens:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "text": text,
                        "page_number": section.page_start,
                        "char_offset": section.char_offset_start,
                        "section": section.heading or "Body",
                        "token_count": est_tokens,
                    }
                )
                chunk_index += 1
        else:
            # Split into overlapping windows by sentence or paragraph
            sentences = re.split(r"(?<=[.!?])\s+", text)
            current_words: list[str] = []

            for sent in sentences:
                sent_words = sent.split()
                if len(current_words) + len(sent_words) > int(target_tokens * 0.75):
                    chunk_text = " ".join(current_words)
                    tokens = int(len(current_words) / 0.75)
                    if tokens >= min_tokens:
                        chunks.append(
                            {
                                "chunk_index": chunk_index,
                                "text": chunk_text,
                                "page_number": section.page_start,
                                "char_offset": section.char_offset_start,
                                "section": section.heading or "Body",
                                "token_count": tokens,
                            }
                        )
                        chunk_index += 1
                    # Keep tail for overlap
                    overlap_word_count = int(overlap_tokens * 0.75)
                    current_words = current_words[-overlap_word_count:] + sent_words
                else:
                    current_words.extend(sent_words)

            if current_words:
                chunk_text = " ".join(current_words)
                tokens = int(len(current_words) / 0.75)
                if tokens >= min_tokens:
                    chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "text": chunk_text,
                            "page_number": section.page_start,
                            "char_offset": section.char_offset_start,
                            "section": section.heading or "Body",
                            "token_count": tokens,
                        }
                    )
                    chunk_index += 1

    return chunks
