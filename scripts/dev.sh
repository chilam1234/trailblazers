#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d "$ROOT/server/.venv" ]]; then
  python3 -m venv "$ROOT/server/.venv"
  "$ROOT/server/.venv/bin/pip" install -q -e "$ROOT/server[dev]"
fi
if [[ ! -d "$ROOT/web/node_modules" ]]; then
  (cd "$ROOT/web" && npm install --no-fund --no-audit)
fi

export PYTHONPATH="$ROOT/server"
export MERIDIAN_API="${MERIDIAN_API:-http://127.0.0.1:8000}"

echo "Meridian API  → http://127.0.0.1:8000"
echo "Meridian desk → http://127.0.0.1:3000"
echo "Fixture composer is default unless OPENAI_API_KEY is set."

"$ROOT/server/.venv/bin/uvicorn" meridian.app:app --app-dir "$ROOT/server" --host 0.0.0.0 --port 8000 &
API_PID=$!
cleanup() { kill "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd "$ROOT/web" && npm run dev)
