# Meridian fixture spine

Synthetic coverage universe for the research desk. **Not verbatim EDGAR.**
Numbers, item headings, and tape copy are invented so the composer, retrieval,
and 20-case eval gate can run offline without an API key.

| Ticker | Name | Pod | Seeded watchlist |
|--------|------|-----|------------------|
| AAPL | Apple Inc. | TMT | yes |
| NVDA | NVIDIA Corporation | TMT | yes |
| MSFT | Microsoft Corporation | TMT | no |
| JPM | JPMorgan Chase & Co. | FIG | no |
| XOM | Exxon Mobil Corporation | Energy | no |

## Layout

- `companies/` — coverage cards (`get_company`)
- `filings/` — synthetic 10-K / 8-K chunks (`search_filings`)
- `news/` — synthetic tape (`search_news`)
- `goldens/cases.json` — 20 eval cases (research must not HITL; watchlist/desk-note must)
- `tools.mcp.json` — MCP tool descriptors for platforms handoff
