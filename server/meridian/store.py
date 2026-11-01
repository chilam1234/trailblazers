from __future__ import annotations

import threading
from typing import Any

from meridian.schemas import DeskNote, WatchlistEntry


class DeskStore:
    """In-process shared book, notes, traces, and latency samples."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.watchlist: dict[str, WatchlistEntry] = {}
        self.notes: list[DeskNote] = []
        self.traces: list[dict[str, Any]] = []
        self.latencies_ms: list[float] = []
        self.cache_hits = 0
        self.cache_total = 0

    def seed(self, entries: list[WatchlistEntry]) -> None:
        with self._lock:
            self.watchlist = {e.ticker: e for e in entries}

    def list_watchlist(self) -> list[WatchlistEntry]:
        with self._lock:
            return list(self.watchlist.values())

    def add(self, entry: WatchlistEntry) -> WatchlistEntry:
        with self._lock:
            self.watchlist[entry.ticker] = entry
            return entry

    def remove(self, ticker: str) -> WatchlistEntry | None:
        with self._lock:
            return self.watchlist.pop(ticker, None)

    def get(self, ticker: str) -> WatchlistEntry | None:
        with self._lock:
            return self.watchlist.get(ticker)

    def add_note(self, note: DeskNote) -> DeskNote:
        with self._lock:
            self.notes.append(note)
            return note

    def list_notes(self) -> list[DeskNote]:
        with self._lock:
            return list(self.notes)

    def record_trace(self, event: dict[str, Any]) -> None:
        with self._lock:
            self.traces.append(event)
            if len(self.traces) > 200:
                self.traces = self.traces[-200:]

    def list_traces(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(self.traces[-50:]))

    def record_latency(self, ms: float, cache_hit: bool) -> None:
        with self._lock:
            self.latencies_ms.append(ms)
            if len(self.latencies_ms) > 200:
                self.latencies_ms = self.latencies_ms[-200:]
            self.cache_total += 1
            if cache_hit:
                self.cache_hits += 1

    def p50_ms(self) -> float:
        with self._lock:
            if not self.latencies_ms:
                return 0.0
            ordered = sorted(self.latencies_ms)
            return ordered[len(ordered) // 2]


store = DeskStore()
