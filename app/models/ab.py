from enum import Enum

from pydantic import BaseModel, Field


class ABVariant(str, Enum):
    A = "A"
    B = "B"


class ABAssignResponse(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    variant: ABVariant = Field(..., description="Назначенный вариант алгоритма")
