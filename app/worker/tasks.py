from typing import List, cast

from app.services.redis_cache import redis_cache
from app.worker.celery_app import celery_app


@celery_app.task(name="invalidate_recommendations_cache")
def invalidate_recommendations_cache(user_id: str) -> None:
    """
    Инвалидация кэша рекомендаций для пользователя по всем алгоритмам/вариантам.
    Упрощённо: удаляем ключи по шаблону rec:{user_id}:*
    """
    pattern = f"rec:{user_id}:*"
    # Для небольшой нагрузки допустимо KEYS; затем можно заменить на SCAN
    raw_keys = redis_cache._client.keys(pattern)
    keys = cast(List[str], raw_keys)
    if keys:
        redis_cache._client.delete(*keys)
