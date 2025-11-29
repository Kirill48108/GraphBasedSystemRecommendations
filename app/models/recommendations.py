from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AlgorithmName(str, Enum):
    POPULAR = "popular"
    CF = "cf"  # collaborative filtering (user-based)
    KNN = "knn"  # k-nearest neighbors
    PR = "pr"  # personalized PageRank
    HYBRID = "hybrid"  # гибридный скоринг


class RecommendationRequest(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    algo: AlgorithmName = Field(
        default=AlgorithmName.POPULAR,
        description="Алгоритм рекомендаций",
    )
    k: int = Field(default=10, ge=1, le=100, description="Количество рекомендаций")


class RecommendedItem(BaseModel):
    item_id: str
    score: float
    reason: Optional[str] = None  # можно использовать для простых объяснений


class RecommendationResponse(BaseModel):
    user_id: str
    algo: AlgorithmName
    items: List[RecommendedItem]
