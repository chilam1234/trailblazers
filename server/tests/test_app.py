from fastapi.testclient import TestClient

from trailblazers.app import app


def test_health_and_research_roundtrip() -> None:
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    resp = client.post("/api/research", json={"question": "What is NVIDIA's data-center mix and export-control risk?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "88%" in body["briefing"]
    companies = client.get("/api/companies")
    assert {c["ticker"] for c in companies.json()} >= {"AAPL", "NVDA", "MSFT", "JPM", "XOM"}
