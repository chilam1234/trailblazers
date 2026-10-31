from meridian.graph.graph import resume_graph, run_graph
from meridian.graph.nodes import classify
from meridian.schemas import WatchlistEntry
from meridian.store import store


def test_classify_intents() -> None:
    intent, tickers = classify("Add Exxon to the coverage watchlist.")
    assert intent == "watchlist_add"
    assert "XOM" in tickers
    intent, tickers = classify("Remove Apple from the watchlist.")
    assert intent == "watchlist_remove"
    assert "AAPL" in tickers
    intent, _ = classify("What is NVIDIA's data-center mix and export-control risk?")
    assert intent == "research"


def test_research_does_not_pause() -> None:
    result = run_graph("What is NVIDIA's data-center mix and export-control risk?", "t-r01")
    assert result["status"] == "ok"
    assert result["hitl"] is None
    assert any(c["id"] == "F-NVDA-10K" for c in result["citations"])
    assert "88%" in result["briefing"]


def test_watchlist_add_pauses_then_applies() -> None:
    store.seed(
        [
            WatchlistEntry(
                ticker="NVDA", name="NVIDIA Corporation", pod="TMT", priority="core", reason="seed"
            )
        ]
    )
    paused = run_graph("Add Exxon to the coverage watchlist.", "t-h13")
    assert paused["status"] == "paused"
    assert paused["hitl"] is not None
    assert paused["proposed"]["ticker"] == "XOM"
    done = resume_graph("t-h13", "approve", paused["proposed"])
    assert done["status"] == "ok"
    assert store.get("XOM") is not None


def test_watchlist_reject_does_not_write() -> None:
    paused = run_graph("Add Microsoft to the coverage watchlist.", "t-h19")
    assert paused["status"] == "paused"
    resume_graph("t-h19", "reject", paused["proposed"])
    assert store.get("MSFT") is None
