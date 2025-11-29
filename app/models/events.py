from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.ab import ABVariant


class EventType(str, Enum):
    SHOW = "show"
    CLICK = "click"


class EventCreate(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    item_id: str = Field(..., description="ID фильма")
    variant: ABVariant = Field(..., description="A/B-вариант алгоритма")
    type: EventType = Field(..., description="Тип события (show/click)")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Время события (UTC)",
    )


class EventResponse(BaseModel):
    id: str = Field(..., description="ID события в хранилище")
    user_id: str
    item_id: str
    variant: ABVariant
    type: EventType
    timestamp: datetime
