from __future__ import annotations

import json
import statistics
import time
from typing import Any

from trailblazers.corpus import load_companies
from trailblazers.graph.graph import run_graph
from trailblazers.schemas import WatchlistEntry
from trailblazers.settings import settings
from trailblazers.store import store


def load_goldens() -> list[dict[str, Any]]:
    path = settings.fixtures_dir / "goldens" / "cases.json"
    return json.loads(path.read_text())


def _reset_book() -> None:
    seeded = [
        WatchlistEntry(
            ticker=c.ticker,
            name=c.name,
            pod=c.pod,
            priority=c.priority,
            reason=c.reason or "Seeded coverage.",
        )
        for c in load_companies().values()
        if c.on_book
    ]
    store.seed(seeded)
    store.notes.clear()


def score_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    misses: list[str] = []
    expect_hitl = bool(case.get("hitl"))
    got_hitl = result.get("status") == "paused" or result.get("hitl") is not None
    if expect_hitl != got_hitl:
        misses.append("hitl")
    hay = " ".join(
        [
            result.get("briefing") or "",
            json.dumps(result.get("proposed") or {}),
            json.dumps(result.get("hitl") or {}),
            " ".join(c.get("id", "") for c in result.get("citations") or []),
        ]
    )
    for token in case.get("must_contain") or []:
        if token.lower() not in hay.lower():
            misses.append(f"fact:{token}")
    cited = {c.get("id") for c in result.get("citations") or []}
    if result.get("proposed") and case.get("kind") == "desk_note":
        cited |= {
            item
            for item in (case.get("must_cite") or [])
            if item in (result.get("briefing") or "") or item in json.dumps(result.get("proposed") or {})
        }
    for cid in case.get("must_cite") or []:
        in_brief = cid in (result.get("briefing") or "")
        in_cites = cid in cited
        in_proposed = cid in json.dumps(result.get("proposed") or {})
        if not (in_brief or in_cites or in_proposed):
            misses.append(f"cite:{cid}")
    if case.get("ticker"):
        blob = json.dumps(result.get("proposed") or result.get("hitl") or {})
        if case["ticker"] not in blob and case["ticker"] not in (result.get("briefing") or ""):
            misses.append(f"ticker:{case['ticker']}")
    score = 0.0 if misses else 1.0
    if misses and len(misses) == 1 and misses[0].startswith("fact:"):
        score = 0.5
    return {
        "id": case["id"],
        "query": case["query"],
        "score": score,
        "misses": misses,
        "hitl": got_hitl,
        "elapsed_ms": result.get("elapsed_ms", 0),
    }


def run_eval_suite() -> dict[str, Any]:
    _reset_book()
    cases = load_goldens()
    rows: list[dict[str, Any]] = []
    times: list[float] = []
    for case in cases:
        started = time.perf_counter()
        result = run_graph(case["query"], thread_id=f"eval-{case['id']}")
        elapsed = (time.perf_counter() - started) * 1000
        result["elapsed_ms"] = round(elapsed, 3)
        times.append(elapsed)
        rows.append(score_case(case, result))
    mean = sum(r["score"] for r in rows) / len(rows) if rows else 0.0
    p50 = statistics.median(times) if times else 0.0
    payload = {
        "gate": settings.eval_gate,
        "mean": round(mean, 4),
        "cases": len(rows),
        "p50_ms": round(p50, 3),
        "passed": mean >= settings.eval_gate,
        "results": rows,
    }
    settings.last_run_path.parent.mkdir(parents=True, exist_ok=True)
    settings.last_run_path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def load_last_run() -> dict[str, Any]:
    path = settings.last_run_path
    if path.exists():
        return json.loads(path.read_text())
    return {"gate": settings.eval_gate, "mean": None, "cases": 0, "results": []}
