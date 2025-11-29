from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class PopularityWindow(str, Enum):
    D7 = "7d"
    D30 = "30d"
    D90 = "90d"


class PopularItem(BaseModel):
    item_id: str
    score: float


class PopularityResponse(BaseModel):
    window: PopularityWindow
    items: List[PopularItem]


class QualityMetrics(BaseModel):
    hit_at_k: float = Field(..., description="Hit@K")
    map_at_k: float = Field(..., description="MAP@K")
    k: int = Field(..., description="K для метрик")
    calculated_at: datetime = Field(..., description="Время расчёта метрик")
