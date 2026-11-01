from trailblazers.retrieve import jaccard, retrieve, token_set
from trailblazers.tools import get_company, search_filings, search_news


def test_nvda_10k_is_top_filing() -> None:
    docs = search_filings("NVIDIA data-center mix export-control", tickers=["NVDA"])
    assert docs
    assert docs[0].id == "F-NVDA-10K"
    assert "88%" in docs[0].text


def test_apple_8k_buyback() -> None:
    docs = search_filings("incremental share repurchase authorization", tickers=["AAPL"], form="8-K")
    assert any(d.id == "F-AAPL-8K" for d in docs)


def test_news_export_tape() -> None:
    docs = search_news("NVIDIA export-control license denials", tickers=["NVDA"])
    assert any(d.id == "N-NVDA-EXPORT" for d in docs)


def test_get_company() -> None:
    card = get_company("XOM")
    assert card is not None
    assert card["pod"] == "Energy"


def test_jaccard_exact() -> None:
    assert jaccard(token_set("nvda mix"), token_set("nvda mix")) == 1.0
    assert jaccard(token_set("nvda mix"), token_set("unrelated text")) < 0.3


def test_retrieve_kind_filter() -> None:
    news = retrieve("Guyana Pioneer", kind="news")
    assert all(d.kind == "news" for d in news)
