from fastapi.testclient import TestClient

from .test_interactions import get_token


def test_explain_popular(client: TestClient) -> None:
    """
    Проверяем, что /explain возвращает объяснение и не падает.
    """
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Сначала получим рекомендации по popular, возьмём один фильм
    rec_resp = client.get("/api/v1/recommendations?algo=popular&k=1", headers=headers)
    assert rec_resp.status_code == 200
    rec_body = rec_resp.json()
    items = rec_body["items"]
    if not items:
        # Если нет фильмов (совсем пустая БД), просто пропустим тест
        return

    item_id = items[0]["item_id"]
    user_id = rec_body["user_id"]

    explain_resp = client.get(
        f"/api/v1/explain?user_id={user_id}&item_id={item_id}&algo=popular",
        headers=headers,
    )
    assert explain_resp.status_code == 200
    body = explain_resp.json()
    assert body["user_id"] == user_id
    assert body["item_id"] == item_id
    assert body["algo"] == "popular"
    assert isinstance(body["explanation"], str)
    assert body["explanation"]
