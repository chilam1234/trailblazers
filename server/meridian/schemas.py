from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Intent = Literal["research", "watchlist_add", "watchlist_remove", "desk_note"]


class Citation(BaseModel):
    id: str
    kind: Literal["filing", "news", "company"]
    ticker: str
    title: str
    filed: str = ""
    excerpt: str = ""


class Document(BaseModel):
    id: str
    kind: Literal["filing", "news", "company"]
    ticker: str
    title: str
    text: str
    filed: str = ""
    form: str = ""
    score: float = 0.0


class Company(BaseModel):
    ticker: str
    name: str
    sector: str
    pod: str
    priority: str = "core"
    on_book: bool = False
    reason: str = ""
    aliases: list[str] = Field(default_factory=list)


class WatchlistEntry(BaseModel):
    ticker: str
    name: str
    pod: str
    priority: str = "core"
    reason: str = ""


class DeskNote(BaseModel):
    ticker: str
    title: str
    body: str
    approved: bool = True


class ResearchRequest(BaseModel):
    question: str
    thread_id: str | None = None


class HitlResumeRequest(BaseModel):
    thread_id: str
    action: Literal["approve", "reject", "edit"]
    proposed: dict[str, Any] | None = None


class StatusOut(BaseModel):
    provider: str
    p50_ms: float
    cache_hits: int
    cache_total: int
    rate_remaining: int
