from fastapi import APIRouter, HTTPException, Query, status

from app.models.explain import ExplainRequest, ExplainResponse
from app.models.recommendations import AlgorithmName
from app.services.explain import explain_service

router = APIRouter(prefix="/explain", tags=["explain"])


@router.get(
    "",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
    summary="Объяснение, почему фильм был рекомендован пользователю",
)
async def explain_recommendation(
    user_id: str = Query(..., description="ID пользователя"),
    item_id: str = Query(..., description="ID фильма"),
    algo: AlgorithmName = Query(..., description="Алгоритм рекомендации"),
) -> ExplainResponse:
    """
    Возвращает текстовое объяснение для пары пользователь–фильм.
    Пока использует простые правила на основе типа алгоритма.
    """
    try:
        req = ExplainRequest(user_id=user_id, item_id=item_id, algo=algo)
        resp = explain_service.explain(req)
        return resp
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации объяснения: {exc}",
        ) from exc
