import hashlib

from app.core.config import settings
from app.models.ab import ABVariant
from app.services.redis_cache import redis_cache


class ABService:
    def __init__(self) -> None:
        self._seed = settings.ab_seed
        self._default_variant = ABVariant(settings.default_variant)

    @staticmethod
    def _hash_to_float(value: str) -> float:
        """
        Хешируем строку и приводим к числу в [0.0, 1.0).
        """
        h = hashlib.sha256(value.encode("utf-8")).hexdigest()
        # Берём первые 8 байт хеша как int и нормируем
        n = int(h[:16], 16)
        return (n % 10_000_000) / 10_000_000.0

    def assign_variant(self, user_id: str) -> ABVariant:
        """
        Назначает вариант для пользователя (детерминированно) и кладёт в Redis.
        """
        key = f"ab:{user_id}"
        cached = redis_cache.get(key)
        if cached is not None and "variant" in cached:
            return ABVariant(cached["variant"])

        # Детерминированное разбиение 50/50 A/B
        r = self._hash_to_float(f"{self._seed}:{user_id}")
        variant = ABVariant.A if r < 0.5 else ABVariant.B

        redis_cache.set(
            key, {"variant": variant.value}, ttl_seconds=30 * 24 * 3600
        )  # 30 дней

        return variant


ab_service = ABService()
