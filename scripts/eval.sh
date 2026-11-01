#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/server"
PY="${ROOT}/server/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY="python3"; fi
cd "$ROOT/server"
"$PY" -m trailblazers.evals
