import logging
import time
from typing import Optional, cast

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import settings
from app.services.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Простое ограничение запросов:
    - ключ: rate:{user_or_ip}:{minute_timestamp}
    - значение: количество запросов в текущую минуту
    """

    def __init__(
        self, app: ASGIApp, max_requests_per_minute: Optional[int] = None
    ) -> None:
        super().__init__(app)
        self.max_requests = (
            max_requests_per_minute or settings.rate_limit_requests_per_minute
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # Разрешаем health-check и auth без лимита
        path = request.url.path
        if path.startswith("/api/v1/health") or path.startswith("/api/v1/auth/token"):
            return await call_next(request)

        identifier = self._get_identifier(request)
        if identifier is None:
            # если не смогли определить, считаем по IP
            identifier = request.client.host if request.client else "unknown"

        now = int(time.time())
        minute = now // 60
        key = f"rate:{identifier}:{minute}"

        try:
            raw_count = redis_cache._client.incr(key)
            count = int(cast(int, raw_count))
            if count == 1:
                # первый запрос в этом окне — ставим TTL ~60 сек
                redis_cache._client.expire(key, 60)
        except Exception as exc:
            # при проблемах с Redis не блокируем запрос, но логируем
            logger.warning("rate limiter: redis error: %s", exc)
            return await call_next(request)

        if count > self.max_requests:
            logger.warning(
                "rate limit exceeded identifier=%s count=%d", identifier, count
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Превышен лимит запросов. Попробуйте позже."},
            )

        return await call_next(request)

    def _get_identifier(self, request: Request) -> Optional[str]:
        """
        Пытаемся вытащить user_id из JWT токена, если он есть.
        """
        auth_header = request.headers.get("Authorization") or ""
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.jwt_algorithm]
            )
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except JWTError:
            return None
        return None
