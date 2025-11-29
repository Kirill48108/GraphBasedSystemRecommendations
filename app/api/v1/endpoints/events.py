from fastapi import APIRouter, HTTPException, status

from app.models.events import EventCreate, EventResponse
from app.services.arango import arango_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Логировать события показов/кликов (A/B)",
)
async def create_event(event: EventCreate) -> EventResponse:
    """
    Записывает событие show/click для пользователя, фильма и A/B-варианта.
    """
    try:
        event_id = arango_service.create_event(event)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при записи события: {exc}",
        ) from exc

    return EventResponse(
        id=event_id,
        user_id=event.user_id,
        item_id=event.item_id,
        variant=event.variant,
        type=event.type,
        timestamp=event.timestamp,
    )
