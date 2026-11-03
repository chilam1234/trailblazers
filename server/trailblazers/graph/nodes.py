from __future__ import annotations

import re
from typing import Any

from trailblazers.compose import (
    citations_from,
    compose_briefing,
    desk_note_proposal,
    fixture_compose,
    grounded,
    watchlist_proposal,
)
from trailblazers.corpus import company_alias_index, load_companies
from trailblazers.graph.state import DeskState
from trailblazers.observability import span
from trailblazers.schemas import Document
from trailblazers.tools import get_company, run_tools

_WRITE_VERBS = (
    (r"\badd\b.+\bwatchlist\b", "watchlist_add"),
    (r"\bremove\b.+\bwatchlist\b", "watchlist_remove"),
    (r"\bfile a desk note\b", "desk_note"),
    (r"\bdesk note\b", "desk_note"),
)


def classify(question: str) -> tuple[str, list[str]]:
    lowered = question.lower()
    intent = "research"
    for pattern, label in _WRITE_VERBS:
        if re.search(pattern, lowered):
            intent = label
            break
    tickers: list[str] = []
    seen: set[str] = set()
    for alias, ticker in company_alias_index():
        if alias in lowered and ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
    return intent, tickers


def plan_node(state: DeskState) -> dict[str, Any]:
    with span("plan", question=state["question"][:80]):
        intent, tickers = classify(state["question"])
        return {
            "intent": intent,
            "tickers": tickers,
            "hitl_required": intent != "research",
            "status": "running",
            "healed": False,
        }


def retrieve_node(state: DeskState) -> dict[str, Any]:
    with span("retrieve", intent=state.get("intent", "")):
        docs, used = run_tools(state.get("intent", "research"), state["question"], state.get("tickers") or [])
        return {"documents": [d.model_dump() for d in docs], "tools_used": used}


def _docs(state: DeskState) -> list[Document]:
    return [Document.model_validate(item) for item in state.get("documents") or []]


def draft_node(state: DeskState) -> dict[str, Any]:
    intent = state.get("intent", "research")
    tickers = state.get("tickers") or []
    docs = _docs(state)
    with span("draft", intent=intent):
        if intent == "research":
            text, provider = compose_briefing(state["question"], tickers, docs)
            cites = citations_from(docs)
            return {
                "draft": text,
                "citations": [c.model_dump() for c in cites],
                "grounded": grounded(text, cites),
                "provider": provider,
                "proposed": None,
            }
        ticker = tickers[0] if tickers else ""
        company = get_company(ticker) if ticker else None
        if intent in {"watchlist_add", "watchlist_remove"}:
            proposed = watchlist_proposal(intent, ticker, company, state["question"])
            return {
                "draft": f"Paused for desk approval: {intent} {ticker}",
                "citations": [],
                "grounded": True,
                "provider": "fixture",
                "proposed": proposed,
            }
        text, provider = compose_briefing(state["question"], tickers, docs)
        proposed = desk_note_proposal(ticker, state["question"], text)
        cites = citations_from(docs)
        return {
            "draft": text,
            "citations": [c.model_dump() for c in cites],
            "grounded": grounded(text, cites),
            "provider": provider,
            "proposed": proposed,
        }


def self_heal_node(state: DeskState) -> dict[str, Any]:
    if state.get("intent") != "research":
        return {}
    if state.get("grounded") and state.get("citations"):
        return {}
    with span("self_heal"):
        tickers = state.get("tickers") or []
        expanded = state["question"] + " " + " ".join(tickers)
        docs, used = run_tools("research", expanded, tickers)
        text = fixture_compose(state["question"], tickers, docs)
        cites = citations_from(docs)
        return {
            "documents": [d.model_dump() for d in docs],
            "tools_used": list(dict.fromkeys([*(state.get("tools_used") or []), *used])),
            "draft": text,
            "citations": [c.model_dump() for c in cites],
            "grounded": grounded(text, cites),
            "provider": "fixture",
            "healed": True,
        }


def apply_hitl_decision(state: DeskState) -> dict[str, Any]:
    from trailblazers.schemas import DeskNote, WatchlistEntry
    from trailblazers.store import store

    decision = state.get("hitl_decision") or {}
    action = decision.get("action", "reject")
    proposed = decision.get("proposed") or state.get("proposed") or {}
    if action == "reject":
        return {"status": "rejected", "draft": "Coverage write rejected at the desk."}
    intent = state.get("intent")
    if intent == "watchlist_add":
        store.add(WatchlistEntry.model_validate(proposed))
        ticker = proposed.get("ticker", "")
        companies = load_companies()
        if ticker in companies:
            companies[ticker].on_book = True
        return {"status": "ok", "draft": f"Added {ticker} to the coverage watchlist."}
    if intent == "watchlist_remove":
        ticker = proposed.get("ticker", "")
        store.remove(ticker)
        return {"status": "ok", "draft": f"Removed {ticker} from the watchlist."}
    if intent == "desk_note":
        store.add_note(DeskNote.model_validate(proposed))
        return {"status": "ok", "draft": f"Filed desk note for {proposed.get('ticker', '')}."}
    return {"status": "ok"}
