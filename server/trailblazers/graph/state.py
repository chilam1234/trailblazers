from __future__ import annotations

from typing import Any, TypedDict


class DeskState(TypedDict, total=False):
    question: str
    intent: str
    tickers: list[str]
    documents: list[dict[str, Any]]
    tools_used: list[str]
    draft: str
    citations: list[dict[str, Any]]
    grounded: bool
    proposed: dict[str, Any] | None
    hitl_required: bool
    hitl_decision: dict[str, Any] | None
    provider: str
    status: str
    healed: bool
