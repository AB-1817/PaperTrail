from __future__ import annotations

import math
import re

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an the and or not in on at to of for with by from is are was were be been"
    " has have had do does did will would could should may might shall can its it"
    " this that these those i we you he she they us them our your his her their"
    " as if so but yet nor up out about into over after before between through"
    " than then when where who which what how all any each both few more most"
    " other such no only same also just than too very s t".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


def bm25_rank(
    query: str,
    documents: list[tuple[str, str]],
    *,
    k1: float = 1.2,
    b: float = 0.75,
) -> list[tuple[str, float]]:
    """Classical BM25 (k1, b). This is not PostgreSQL ts_rank."""
    tokenized = [(doc_id, tokenize(text)) for doc_id, text in documents]
    total = len(tokenized)
    if total == 0:
        return []
    average_length = sum(len(tokens) for _, tokens in tokenized) / total
    document_frequency: dict[str, int] = {}
    for _, tokens in tokenized:
        for term in set(tokens):
            document_frequency[term] = document_frequency.get(term, 0) + 1

    query_terms = tokenize(query)
    scored: list[tuple[str, float]] = []
    for doc_id, tokens in tokenized:
        term_frequency: dict[str, int] = {}
        for term in tokens:
            term_frequency[term] = term_frequency.get(term, 0) + 1
        length = len(tokens) or 1
        score = 0.0
        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if frequency == 0:
                continue
            df = document_frequency.get(term, 0)
            idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * length / average_length)
            score += idf * (frequency * (k1 + 1)) / denominator
        scored.append((doc_id, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored
