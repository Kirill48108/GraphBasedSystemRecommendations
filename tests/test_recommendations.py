from fastapi.testclient import TestClient

from .test_interactions import get_token  # используем хелпер из другого теста


def test_recommendations_algorithms(client: TestClient) -> None:
    """
    Проверяем, что все заявленные алгоритмы отдаёт API без ошибок.
    Для простоты используем одного и того же пользователя,
    которому уже создали какие-то взаимодействия в других тестах.
    """
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    algos = ["popular", "cf", "knn", "pr", "hybrid"]

    for algo in algos:
        resp = client.get(f"/api/v1/recommendations?algo={algo}&k=5", headers=headers)
        assert resp.status_code == 200, f"algo={algo} status={resp.status_code}"
        body = resp.json()
        assert body["algo"] == algo
        assert "items" in body
        assert isinstance(body["items"], list)
