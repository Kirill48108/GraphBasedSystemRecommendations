from fastapi.testclient import TestClient

from .test_interactions import get_token


def test_ab_assign_is_deterministic(client: TestClient) -> None:
    """
    Проверяем, что /ab/assign детерминированно выдаёт один и тот же variant для одного user_id.
    """
    user_id = "user_ab_test"

    resp1 = client.get(f"/api/v1/ab/assign?user_id={user_id}")
    resp2 = client.get(f"/api/v1/ab/assign?user_id={user_id}")

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    v1 = resp1.json()["variant"]
    v2 = resp2.json()["variant"]
    assert v1 in ("A", "B")
    assert v1 == v2


def test_events_show_and_click(client: TestClient) -> None:
    """
    Проверяем, что /events принимает события show/click.
    """
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Вытаскиваем variant для пользователя через /ab/assign
    user_id = "user_events_test"
    ab_resp = client.get(f"/api/v1/ab/assign?user_id={user_id}")
    assert ab_resp.status_code == 200
    variant = ab_resp.json()["variant"]

    show_event = {
        "user_id": user_id,
        "item_id": "movie_event_1",
        "variant": variant,
        "type": "show",
    }
    click_event = {
        "user_id": user_id,
        "item_id": "movie_event_1",
        "variant": variant,
        "type": "click",
    }

    r1 = client.post("/api/v1/events", json=show_event, headers=headers)
    r2 = client.post("/api/v1/events", json=click_event, headers=headers)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["type"] == "show"
    assert r2.json()["type"] == "click"
