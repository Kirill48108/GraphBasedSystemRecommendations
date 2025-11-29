from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.models.stats import (
    PopularityResponse,
    PopularityWindow,
    QualityMetrics,
)
from app.services.stats import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/popularity",
    response_model=PopularityResponse,
    status_code=status.HTTP_200_OK,
    summary="Популярные фильмы за период (офлайн-витрина, при отсутствии — online)",
)
async def get_popularity(
    window: PopularityWindow = Query(PopularityWindow.D7, description="Окно времени"),
    k: int = Query(10, ge=1, le=100, description="Размер топа"),
) -> PopularityResponse:
    try:
        # Сначала пытаемся прочитать офлайн-витрину
        items = stats_service.get_popularity_offline(window, k)
        if not items:
            # если пусто — считаем онлайн
            items = stats_service.get_popularity_online(window, k)
        return PopularityResponse(window=window, items=items)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при расчёте популярности: {exc}",
        ) from exc


@router.get(
    "/quality",
    response_model=QualityMetrics,
    status_code=status.HTTP_200_OK,
    summary="Качество рекомендаций (Hit@K, MAP@K) из офлайн-витрины",
)
async def get_quality_metrics(
    k: int = Query(10, ge=1, le=100, description="K для метрик"),
) -> QualityMetrics:
    """
    Возвращает офлайн-метрики качества рекомендаций, рассчитанные Airflow'ом.
    Если витрины ещё нет — вернёт нули с текущим timestamp.
    """
    try:
        metrics = stats_service.get_quality_offline(k)
        if metrics is not None:
            return metrics

        now = datetime.now(timezone.utc)
        return QualityMetrics(
            hit_at_k=0.0,
            map_at_k=0.0,
            k=k,
            calculated_at=now,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении метрик качества: {exc}",
        ) from exc
