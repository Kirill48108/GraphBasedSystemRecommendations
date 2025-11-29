import json
from typing import Any, Optional, cast

import redis

from app.core.config import settings


class RedisCache:
    def __init__(self, url: str) -> None:
        self._client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        value = self._client.get(key)
        if value is None:
            return None
        return json.loads(cast(str, value))

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        serialized = json.dumps(value)
        self._client.set(key, serialized, ex=ttl_seconds)

    def delete(self, key: str) -> None:
        self._client.delete(key)


redis_cache = RedisCache(settings.redis_url)
