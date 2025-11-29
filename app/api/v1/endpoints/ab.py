from fastapi import APIRouter, HTTPException, Query, status

from app.models.ab import ABAssignResponse
from app.services.ab import ab_service

router = APIRouter(prefix="/ab", tags=["ab"])


@router.get(
    "/assign",
    response_model=ABAssignResponse,
    status_code=status.HTTP_200_OK,
    summary="Назначить A/B-вариант для пользователя",
)
async def assign_ab_variant(
    user_id: str = Query(..., description="ID пользователя"),
) -> ABAssignResponse:
    """
    Назначает (или возвращает ранее назначенный) A/B-вариант для пользователя.
    """
    try:
        variant = ab_service.assign_variant(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при назначении варианта: {exc}",
        ) from exc

    return ABAssignResponse(user_id=user_id, variant=variant)
