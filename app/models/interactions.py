from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    VIEW = "view"
    LIKE = "like"
    RATING = "rating"


class InteractionCreate(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    item_id: str = Field(..., description="ID фильма")
    type: InteractionType = Field(..., description="Тип взаимодействия")
    # значение для рейтинга 1–5, для view/like можно опустить

    value: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Значение рейтинга 1-5 (если type=rating)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Время взаимодействия (UTC)",
    )


class InteractionResponse(BaseModel):
    id: str = Field(..., description="ID ребра взаимодействия в ArangoDB")
    user_id: str
    item_id: str
    type: InteractionType
    value: Optional[int] = None
    timestamp: datetime
    weight: float = Field(..., description="Вес взаимодействия")
