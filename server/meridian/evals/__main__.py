from __future__ import annotations

import json
import sys

from meridian.evals.runner import run_eval_suite
from meridian.settings import settings


def main() -> int:
    result = run_eval_suite()
    settings.last_run_path.parent.mkdir(parents=True, exist_ok=True)
    settings.last_run_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("gate", "mean", "cases", "p50_ms", "passed")}, indent=2))
    if not result["passed"]:
        print(f"EVAL GATE FAILED: mean {result['mean']:.4f} < {result['gate']}", file=sys.stderr)
        return 1
    print(f"EVAL GATE PASSED: mean {result['mean']:.4f} >= {result['gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
