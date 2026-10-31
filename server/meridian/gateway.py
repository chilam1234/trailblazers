from __future__ import annotations

import threading
import time
from typing import Any, Callable

from fastapi import HTTPException

from meridian.observability import span
from meridian.retrieve import jaccard, token_set
from meridian.settings import settings
from meridian.store import store


class TokenBucket:
    def __init__(self, rate_per_min: int, burst: int) -> None:
        self.rate = rate_per_min / 60.0
        self.burst = float(burst)
        self.tokens = float(burst)
        self.updated = time.monotonic()
        self._lock = threading.Lock()

    def take(self) -> float:
        with self._lock:
            now = time.monotonic()
            self.tokens = min(self.burst, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            if self.tokens < 1.0:
                raise HTTPException(status_code=429, detail="rate limited")
            self.tokens -= 1.0
            return self.tokens


class ResponseCache:
    """Exact key plus Jaccard-near hit. Research answers only."""

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold
        self._exact: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def key(question: str) -> str:
        return " ".join(question.lower().split())

    def get(self, question: str) -> tuple[dict[str, Any] | None, str]:
        key = self.key(question)
        with self._lock:
            if key in self._exact:
                return self._exact[key], "exact"
            q_tokens = token_set(question)
            best_score = 0.0
            best: dict[str, Any] | None = None
            for cached_key, value in self._exact.items():
                score = jaccard(q_tokens, token_set(cached_key))
                if score > best_score:
                    best_score = score
                    best = value
            if best is not None and best_score >= self.threshold:
                return best, "jaccard"
        return None, ""

    def put(self, question: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._exact[self.key(question)] = value


bucket = TokenBucket(settings.rate_limit_per_min, settings.rate_burst)
cache = ResponseCache(settings.cache_jaccard_threshold)


def gateway_call(question: str, runner: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    remaining = bucket.take()
    started = time.perf_counter()
    with span("gateway", question=question[:80]):
        cached, how = cache.get(question)
        if cached is not None:
            elapsed = (time.perf_counter() - started) * 1000
            store.record_latency(elapsed, True)
            return {
                **cached,
                "cache": f"{how} hit",
                "elapsed_ms": round(elapsed, 3),
                "rate_remaining": int(remaining),
            }
        result = runner()
        elapsed = (time.perf_counter() - started) * 1000
        result = {
            **result,
            "cache": "miss",
            "elapsed_ms": round(elapsed, 3),
            "rate_remaining": int(remaining),
        }
        if result.get("status") == "ok" and result.get("intent") == "research":
            cache.put(question, {k: v for k, v in result.items() if k != "elapsed_ms"})
        store.record_latency(elapsed, False)
        return result
