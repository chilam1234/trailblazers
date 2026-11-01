from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from trailblazers.corpus import load_companies
from trailblazers.evals.runner import load_last_run, run_eval_suite
from trailblazers.gateway import bucket, gateway_call
from trailblazers.graph.graph import resume_graph, run_graph
from trailblazers.observability import recent_otel_spans
from trailblazers.schemas import HitlResumeRequest, ResearchRequest, WatchlistEntry
from trailblazers.settings import settings
from trailblazers.store import store


@asynccontextmanager
async def lifespan(_: FastAPI):
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
    yield


app = FastAPI(title="Trailblazers", version="0.4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "provider": "openai" if settings.has_openai else "fixture"}


@app.get("/api/status")
def status() -> dict:
    return {
        "provider": "openai" if settings.has_openai else "fixture",
        "p50_ms": round(store.p50_ms(), 3),
        "cache_hits": store.cache_hits,
        "cache_total": store.cache_total,
        "rate_remaining": int(bucket.tokens),
    }


@app.get("/api/companies")
def companies() -> list[dict]:
    on_book = {e.ticker for e in store.list_watchlist()}
    out = []
    for company in load_companies().values():
        item = company.model_dump()
        item["on_book"] = company.ticker in on_book
        out.append(item)
    return out


@app.get("/api/watchlist")
def watchlist() -> dict:
    return {
        "entries": [e.model_dump() for e in store.list_watchlist()],
        "notes": [n.model_dump() for n in store.list_notes()],
    }


@app.post("/api/research")
def research(req: ResearchRequest) -> dict:
    return gateway_call(req.question, lambda: run_graph(req.question, req.thread_id))


@app.post("/api/hitl/resume")
def hitl_resume(req: HitlResumeRequest) -> dict:
    return resume_graph(req.thread_id, req.action, req.proposed)


@app.get("/api/traces")
def traces() -> dict:
    return {"events": store.list_traces(), "otel": recent_otel_spans()}


@app.get("/api/evals")
def evals_get() -> dict:
    return load_last_run()


@app.post("/api/evals/run")
def evals_run() -> dict:
    return run_eval_suite()


def write_last_run(payload: dict) -> None:
    settings.last_run_path.parent.mkdir(parents=True, exist_ok=True)
    settings.last_run_path.write_text(json.dumps(payload, indent=2))
