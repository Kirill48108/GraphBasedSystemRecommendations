import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Используем localhost для Arango и Redis в тестах
    settings.arango_url = os.getenv("ARANGO_URL", "http://127.0.0.1:8529")
    settings.redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    with TestClient(app) as c:
        yield c
