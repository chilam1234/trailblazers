# Trailblazers

This repository is [github.com/chilam1234/trailblazers](https://github.com/chilam1234/trailblazers). 

Trailblazers plans a question, retrieves synthetic 10-K / 8-K / tape chunks, drafts a cited briefing, and self-heals if the draft is ungrounded. Coverage writes (watchlist add/remove, morning-book desk notes) pause for human approval. A 20-case eval gate fails CI under a **0.92** mean.

No API key is required. When `OPENAI_API_KEY` is missing the **fixture composer** answers from the local corpus and the process does not crash. Fixtures are synthetic — not verbatim EDGAR. This slice has no WebGPU, no Rust, and no vLLM.

## 60-second demo

```bash
./scripts/dev.sh
```

1. Open [http://127.0.0.1:3000](http://127.0.0.1:3000).
2. Run the starter **NVDA briefing** — cited bottom line on data-center mix (88%) and export-control license denials.
3. Run **Add XOM** — HITL panel, approve, then confirm Exxon on [Watchlist](http://127.0.0.1:3000/watchlist).
4. Open [Eval board](http://127.0.0.1:3000/evals) — twenty goldens, gate pass, p50 on the fixture spine.

## How to run

```bash
cp .env.example .env          # OPENAI_API_KEY is optional
./scripts/dev.sh              # API :8000 + desk :3000
./scripts/smoke.sh            # health + one research call
./scripts/eval.sh             # python -m trailblazers.evals
./scripts/prove.sh            # ruff + pytest + evals + web typecheck
```

Optional Docker:

```bash
docker compose up --build
```

## Eval gate

```bash
python -m trailblazers.evals      # from server/ with PYTHONPATH set, or use ./scripts/eval.sh
./scripts/prove.sh
```

Twenty goldens in `fixtures/goldens/cases.json`:

- Research / tape cases (**R\***, **T\***) must **not** fire HITL.
- Watchlist / desk-note cases (**H\***) must pause for approval.
- Mean score **≥ 0.92** or CI fails (`.github/workflows/eval.yml`).

Last local run is written to `evals/last-run.json`.

## Layout

```
fixtures/   companies, filings, news, goldens, tools.mcp.json
server/     FastAPI trailblazers package
  trailblazers/app.py           HTTP
  trailblazers/gateway.py       token bucket, exact+Jaccard cache, provider fallback
  trailblazers/graph/           LangGraph plan → retrieve → draft → self-heal → HITL
  trailblazers/compose.py       fixture composer (default) + optional OpenAI
  trailblazers/evals/           20-case gate
web/        Next.js desk — citations, HITL, eval board, traces, watchlist
scripts/    dev.sh, prove.sh, smoke.sh, eval.sh
```

## Platforms handoff

| Piece | Where | Reuse |
|-------|--------|--------|
| MCP tools | `fixtures/tools.mcp.json` | `search_filings`, `search_news`, `get_company`, watchlist + desk-note writes |
| Eval suite | `python -m trailblazers.evals` | 20 goldens, 0.92 mean, HITL polarity checks |
| Trace format | `GET /api/traces` | `{name, elapsed_ms, attrs}` plus OpenTelemetry in-process spans |
| Gateway | `trailblazers/gateway.py` | token bucket, exact cache, Jaccard-near cache, OpenAI → fixture fallback |
| HITL | LangGraph `interrupt()` | approve / edit / reject on coverage writes only |

## Latency notes

On the fixture spine (no live LLM):

- Single NVDA briefing is typically **low-single-digit ms** in-process (eval p50 is usually under 10 ms on a laptop / agent VM).
- Exact and Jaccard cache short-circuit repeat / near-repeat questions at the gateway.
- Optional OpenAI path is used only when `OPENAI_API_KEY` is set; any provider error falls back to the fixture composer.

## Product intent

LangGraph **plan → retrieve → draft → self-heal**. HITL only on coverage writes. Lean FastAPI gateway (rate limit, cache, fallback, OTel). Fixture-first so a recruiter can clone and run without keys.
