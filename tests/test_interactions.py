from fastapi.testclient import TestClient


def get_token(client: TestClient) -> str:
    data = {
        "username": "admin",
        "password": "admin",
    }
    response = client.post("/api/v1/auth/token", data=data)
    assert response.status_code == 200
    return response.json()["access_token"]


def test_interaction_and_recommendations(client: TestClient) -> None:
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Записываем взаимодействие
    interaction_payload = {
        "user_id": "will_be_overwritten",  # в эндпоинте берётся user_id из токена
        "item_id": "movie_test_1",
        "type": "view",
    }
    resp_inter = client.post(
        "/api/v1/interactions", json=interaction_payload, headers=headers
    )
    assert resp_inter.status_code == 201
    inter_body = resp_inter.json()
    assert inter_body["item_id"] == "movie_test_1"
    assert inter_body["type"] == "view"

    # 2. Получаем рекомендации
    resp_rec = client.get("/api/v1/recommendations?algo=popular&k=10", headers=headers)
    assert resp_rec.status_code == 200
    rec_body = resp_rec.json()
    assert rec_body[
        "user_id"
    ]  # должен совпадать с user_id из токена (admin user_id в auth_users)
    assert "items" in rec_body
    assert isinstance(rec_body["items"], list)
