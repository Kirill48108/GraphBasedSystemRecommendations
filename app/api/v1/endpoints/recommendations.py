import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import settings
from app.core.security import get_current_user
from app.models.auth import UserInDB
from app.models.recommendations import (
    AlgorithmName,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommender import get_recommender
from app.services.redis_cache import redis_cache

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить персональные рекомендации фильмов",
)
async def get_recommendations(
    algo: AlgorithmName = Query(
        default=AlgorithmName.POPULAR,
        description="Алгоритм рекомендаций",
    ),
    k: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Количество рекомендаций",
    ),
    current_user: UserInDB = Depends(get_current_user),
) -> RecommendationResponse:
    """
    Возвращает список рекомендованных фильмов с учётом кэша Redis.
    Требует JWT; user_id берётся из токена.
    """
    user_id = current_user.user_id
    cache_key = f"rec:{user_id}:{algo.value}"
    ttl_seconds = settings.rec_ttl_hours * 3600

    t_start = time.perf_counter()

    cached = redis_cache.get(cache_key)
    if cached is not None:
        elapsed_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            "recommendations cache HIT user_id=%s algo=%s k=%d duration_ms=%.2f",
            user_id,
            algo.value,
            k,
            elapsed_ms,
        )
        return RecommendationResponse(
            user_id=user_id,
            algo=algo,
            items=cached["items"],
        )

    request = RecommendationRequest(user_id=user_id, algo=algo, k=k)
    recommender = get_recommender(algo)

    try:
        items = recommender.recommend(request)
    except Exception as exc:
        logger.exception(
            "recommendations error user_id=%s algo=%s: %s",
            user_id,
            algo.value,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при расчёте рекомендаций: {exc}",
        ) from exc

    items_payload = [item.model_dump() for item in items]
    redis_cache.set(
        cache_key,
        {"items": items_payload},
        ttl_seconds=ttl_seconds,
    )

    elapsed_ms = (time.perf_counter() - t_start) * 1000
    logger.info(
        "recommendations cache MISS user_id=%s algo=%s k=%d duration_ms=%.2f",
        user_id,
        algo.value,
        k,
        elapsed_ms,
    )

    return RecommendationResponse(
        user_id=user_id,
        algo=algo,
        items=items,
    )
