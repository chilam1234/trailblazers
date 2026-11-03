from __future__ import annotations

import re
from collections import Counter

from trailblazers.corpus import load_documents
from trailblazers.schemas import Document

_TOKEN = re.compile(r"[a-z0-9$%]+")
_STOP = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "from",
    "what",
    "how",
    "does",
    "did",
    "is",
    "are",
    "versus",
    "vs",
    "latest",
    "compare",
    "summarize",
    "walk",
    "through",
    "pull",
    "file",
    "add",
    "remove",
}


def tokenize(text: str) -> list[str]:
    return [tok for tok in _TOKEN.findall(text.lower()) if tok not in _STOP and len(tok) > 1]


def token_set(text: str) -> set[str]:
    return set(tokenize(text))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _score(query_tokens: list[str], doc: Document) -> float:
    hay = tokenize(f"{doc.id} {doc.ticker} {doc.title} {doc.form} {doc.text}")
    if not query_tokens or not hay:
        return 0.0
    q_counts = Counter(query_tokens)
    h_counts = Counter(hay)
    overlap = sum(min(q_counts[t], h_counts[t]) for t in q_counts)
    unique = len(set(query_tokens) & set(hay))
    ticker_boost = 2.2 if doc.ticker.lower() in query_tokens else 0.0
    form_boost = 1.4 if doc.form.lower() in query_tokens else 0.0
    id_boost = 3.0 if doc.id.lower() in " ".join(query_tokens) else 0.0
    return overlap + 1.5 * unique + ticker_boost + form_boost + id_boost


def retrieve(
    query: str,
    *,
    tickers: list[str] | None = None,
    kind: str | None = None,
    form: str | None = None,
    limit: int = 6,
) -> list[Document]:
    q_tokens = tokenize(query)
    if tickers:
        q_tokens = q_tokens + [t.lower() for t in tickers]
    scored: list[Document] = []
    for doc in load_documents():
        if tickers and doc.ticker not in {t.upper() for t in tickers}:
            continue
        if kind and doc.kind != kind:
            continue
        if form and form != "any" and doc.form != form:
            continue
        score = _score(q_tokens, doc)
        if score <= 0:
            continue
        item = doc.model_copy(update={"score": score})
        scored.append(item)
    scored.sort(key=lambda d: d.score, reverse=True)
    return scored[:limit]
