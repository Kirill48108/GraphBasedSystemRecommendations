from fastapi.testclient import TestClient


def test_auth_token_admin(client: TestClient) -> None:
    # Пара логин/пароль должны совпадать с DEMO_ADMIN_USERNAME/PASSWORD в .env
    data = {
        "username": "admin",
        "password": "admin",
    }
    response = client.post("/api/v1/auth/token", data=data)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
