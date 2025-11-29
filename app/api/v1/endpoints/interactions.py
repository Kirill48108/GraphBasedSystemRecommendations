from fastapi import APIRouter, HTTPException, status

from app.models.interactions import InteractionCreate, InteractionResponse
from app.services.arango import arango_service
from app.worker.tasks import invalidate_recommendations_cache

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post(
    "",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Записать взаимодействие пользователя с фильмом",
)
async def create_interaction(interaction: InteractionCreate) -> InteractionResponse:
    """
    Создаёт ребро взаимодействия (user -> movie) в графе ArangoDB и инвалидирует кэш.
    """
    try:
        edge_id = arango_service.create_interaction(interaction)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при записи взаимодействия: {exc}",
        ) from exc

    # Асинхронно инвалидируем кэш рекомендаций для пользователя
    try:
        invalidate_recommendations_cache.delay(interaction.user_id)
    except Exception:
        # На этом этапе можно просто залогировать, но не падать по HTTP
        pass

    weight = arango_service._compute_weight(
        interaction
    )  # можно вынести в публичный метод

    return InteractionResponse(
        id=edge_id,
        user_id=interaction.user_id,
        item_id=interaction.item_id,
        type=interaction.type,
        value=interaction.value,
        timestamp=interaction.timestamp,
        weight=weight,
    )
