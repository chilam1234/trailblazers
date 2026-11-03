#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/server"
cd "$ROOT/server"
PY="${ROOT}/server/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY="python3"; fi
"$PY" - <<'PY'
from fastapi.testclient import TestClient
from trailblazers.app import app

client = TestClient(app)
health = client.get("/health")
assert health.status_code == 200, health.text
assert health.json()["ok"] is True
resp = client.post("/api/research", json={"question": "What is NVIDIA's data-center mix and export-control risk?"})
assert resp.status_code == 200, resp.text
body = resp.json()
assert body["status"] == "ok"
assert "88%" in body["briefing"]
print("smoke ok", body["provider"], body.get("elapsed_ms"), "ms")
PY
