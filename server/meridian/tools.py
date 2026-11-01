from __future__ import annotations

from typing import Any

from meridian.corpus import load_companies
from meridian.retrieve import retrieve
from meridian.schemas import Document


def search_filings(query: str, tickers: list[str] | None = None, form: str = "any") -> list[Document]:
    return retrieve(query, tickers=tickers, kind="filing", form=form, limit=5)


def search_news(query: str, tickers: list[str] | None = None) -> list[Document]:
    return retrieve(query, tickers=tickers, kind="news", limit=4)


def get_company(ticker: str) -> dict[str, Any] | None:
    company = load_companies().get(ticker.upper())
    return company.model_dump() if company else None


def run_tools(intent: str, query: str, tickers: list[str]) -> tuple[list[Document], list[str]]:
    used: list[str] = []
    docs: list[Document] = []
    seen: set[str] = set()

    def _add(items: list[Document]) -> None:
        for item in items:
            if item.id in seen:
                continue
            seen.add(item.id)
            docs.append(item)

    if intent == "research" or intent == "desk_note":
        filings = search_filings(query, tickers=tickers or None)
        if filings:
            used.append("search_filings")
            _add(filings)
        news = search_news(query, tickers=tickers or None)
        if news:
            used.append("search_news")
            _add(news)
    if intent in {"watchlist_add", "watchlist_remove", "desk_note"} and tickers:
        used.append("get_company")
        for ticker in tickers:
            card = get_company(ticker)
            if not card:
                continue
            _add(
                [
                    Document(
                        id=f"C-{ticker}",
                        kind="company",
                        ticker=ticker,
                        title=card["name"],
                        text=f"{card['name']} {card['pod']} {card['sector']} {card.get('reason', '')}",
                    )
                ]
            )
    return docs, used
