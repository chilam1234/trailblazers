#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d "$ROOT/server/.venv" ]]; then
  python3 -m venv "$ROOT/server/.venv"
fi
"$ROOT/server/.venv/bin/pip" install -q -e "$ROOT/server[dev]"
if [[ ! -d "$ROOT/web/node_modules" ]]; then
  (cd "$ROOT/web" && npm install --no-fund --no-audit)
fi

export PYTHONPATH="$ROOT/server"
echo "== ruff =="
"$ROOT/server/.venv/bin/ruff" check "$ROOT/server/trailblazers" "$ROOT/server/tests"
echo "== pytest =="
"$ROOT/server/.venv/bin/pytest" -q "$ROOT/server/tests"
echo "== evals =="
"$ROOT/server/.venv/bin/python" -m trailblazers.evals
echo "== web typecheck =="
(cd "$ROOT/web" && npm run typecheck)
echo "prove ok"
