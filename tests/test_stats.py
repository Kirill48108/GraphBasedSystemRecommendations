from fastapi.testclient import TestClient


def test_stats_popularity(client: TestClient) -> None:
    response = client.get("/api/v1/stats/popularity?window=7d&k=10")
    assert response.status_code == 200
    body = response.json()
    assert body["window"] == "7d"
    assert "items" in body
    assert isinstance(body["items"], list)


def test_stats_quality(client: TestClient) -> None:
    response = client.get("/api/v1/stats/quality?k=10")
    assert response.status_code == 200
    body = response.json()
    assert "hit_at_k" in body
    assert "map_at_k" in body
    assert body["k"] == 10
