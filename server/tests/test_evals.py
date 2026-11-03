from trailblazers.evals.runner import load_goldens, run_eval_suite
from trailblazers.settings import settings


def test_twenty_goldens() -> None:
    cases = load_goldens()
    assert len(cases) == 20
    assert all(c["id"] for c in cases)
    research = [c for c in cases if not c["hitl"]]
    writes = [c for c in cases if c["hitl"]]
    assert research
    assert writes


def test_eval_gate() -> None:
    result = run_eval_suite()
    assert result["cases"] == 20
    assert result["mean"] >= settings.eval_gate
    assert result["passed"] is True
