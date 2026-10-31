from __future__ import annotations

import re
from typing import Any

import httpx

from meridian.schemas import Citation, Document
from meridian.settings import settings


def _excerpt(text: str, limit: int = 280) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def citations_from(docs: list[Document], limit: int = 6) -> list[Citation]:
    out: list[Citation] = []
    for doc in docs:
        if doc.kind == "company":
            continue
        out.append(
            Citation(
                id=doc.id,
                kind=doc.kind,  # type: ignore[arg-type]
                ticker=doc.ticker,
                title=doc.title,
                filed=doc.filed,
                excerpt=_excerpt(doc.text),
            )
        )
        if len(out) >= limit:
            break
    return out


def _lead_sentences(text: str, n: int = 2) -> str:
    parts = re.split(r"(?<=[.!;])\s+", text.strip())
    return " ".join(parts[:n]).strip()


def fixture_compose(question: str, tickers: list[str], docs: list[Document]) -> str:
    """Deterministic grounded briefing. Used when OPENAI_API_KEY is missing."""
    companies = {d.ticker: d.title for d in docs if d.kind == "company"}
    filings = [d for d in docs if d.kind == "filing"]
    news = [d for d in docs if d.kind == "news"]
    coverage = ", ".join(f"{t} ({companies.get(t, t)})" for t in tickers) or "multi-name"
    facts = []
    for doc in filings + news:
        facts.append(f"{_lead_sentences(doc.text)} [{doc.id}]")
    if not facts:
        body = "No fixture documents cleared the retriever. Widen the question or ticker."
    else:
        body = " ".join(facts[:4])
    filing_lines = []
    for doc in filings:
        filing_lines.append(
            f"- {doc.ticker} {doc.form} ({doc.filed}) [{doc.id}]: {_excerpt(doc.text, 360)}"
        )
    if not filing_lines:
        filing_lines = ["- No filings retrieved."]
    news_lines = [f"- {doc.title} ({doc.filed}) [{doc.id}]: {_excerpt(doc.text, 240)}" for doc in news]
    news_block = "\n".join(news_lines) if news_lines else "- No tape items retrieved."
    return (
        "MERIDIAN DESK BRIEFING\n\n"
        f"Coverage: {coverage}\n"
        f"Question: {question}\n\n"
        "BOTTOM LINE\n"
        f"{body}\n\n"
        "FILING READ-THROUGH\n"
        + "\n".join(filing_lines)
        + "\n\nTAPE\n"
        + news_block
    )


def openai_compose(question: str, docs: list[Document]) -> str:
    context = "\n\n".join(f"[{d.id}] {d.title}: {d.text}" for d in docs[:6])
    payload = {
        "model": settings.openai_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Meridian, an investment research desk. Answer only from the "
                    "provided fixture excerpts. Cite source ids like [F-NVDA-10K]. "
                    "Use BOTTOM LINE then FILING READ-THROUGH."
                ),
            },
            {"role": "user", "content": f"Question: {question}\n\nSources:\n{context}"},
        ],
        "temperature": 0.1,
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(f"{settings.openai_base_url}/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def compose_briefing(question: str, tickers: list[str], docs: list[Document]) -> tuple[str, str]:
    """Return (text, provider). Fixture composer is the default and the fallback."""
    if settings.has_openai:
        try:
            return openai_compose(question, docs), "openai"
        except Exception:
            pass
    return fixture_compose(question, tickers, docs), "fixture"


def grounded(text: str, citations: list[Citation], required: list[str] | None = None) -> bool:
    if not citations:
        return False
    cited = {c.id for c in citations if c.id in text}
    if not cited:
        return False
    if required:
        return all(token.lower() in text.lower() for token in required)
    return True


def watchlist_proposal(intent: str, ticker: str, company: dict[str, Any] | None, question: str) -> dict:
    name = company["name"] if company else ticker
    pod = company["pod"] if company else ""
    if intent == "watchlist_add":
        reason = (
            f"Coverage initiation requested: {question.strip()} "
            "Advantaged-barrel / filing-backed setup from the fixture spine."
            if ticker == "XOM"
            else f"Coverage initiation requested: {question.strip()}"
        )
        return {
            "ticker": ticker,
            "name": name,
            "sector": company["sector"] if company else "",
            "pod": pod,
            "priority": "core",
            "reason": reason,
        }
    return {"ticker": ticker, "name": name, "action": "remove", "reason": question.strip()}


def desk_note_proposal(ticker: str, question: str, briefing: str) -> dict:
    return {
        "ticker": ticker,
        "title": question.strip(),
        "body": briefing,
    }
