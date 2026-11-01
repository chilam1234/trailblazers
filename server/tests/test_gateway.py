import pytest
from fastapi import HTTPException

from trailblazers.gateway import ResponseCache, TokenBucket


def test_token_bucket_allows_then_limits() -> None:
    bucket = TokenBucket(rate_per_min=60, burst=2)
    assert bucket.take() >= 0
    assert bucket.take() >= 0
    with pytest.raises(HTTPException) as err:
        bucket.take()
    assert err.value.status_code == 429


def test_exact_and_jaccard_cache() -> None:
    cache = ResponseCache(threshold=0.8)
    cache.put("nvidia data-center mix", {"briefing": "88%"})
    hit, how = cache.get("nvidia data-center mix")
    assert hit is not None
    assert how == "exact"
    near, how_near = cache.get("nvidia data center mix")
    assert near is not None
    assert how_near in {"exact", "jaccard"}
    miss, _ = cache.get("completely unrelated agriculture query")
    assert miss is None
