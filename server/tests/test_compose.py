from meridian.compose import citations_from, fixture_compose, grounded
from meridian.retrieve import retrieve


def test_fixture_composer_cites_nvda() -> None:
    docs = retrieve("NVIDIA data-center mix export-control", tickers=["NVDA"])
    text = fixture_compose("What is NVIDIA's data-center mix and export-control risk?", ["NVDA"], docs)
    assert "88%" in text
    assert "F-NVDA-10K" in text
    cites = citations_from(docs)
    assert grounded(text, cites)


def test_composer_survives_empty_docs() -> None:
    text = fixture_compose("unknown", [], [])
    assert "No fixture documents" in text
