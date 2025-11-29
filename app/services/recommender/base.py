from abc import ABC, abstractmethod
from typing import List

from app.models.recommendations import (
    RecommendationRequest,
    RecommendedItem,
)


class Recommender(ABC):
    """
    Базовый интерфейс для всех алгоритмов рекомендаций.
    """

    @abstractmethod
    def recommend(self, request: RecommendationRequest) -> List[RecommendedItem]:
        """
        Возвращает список рекомендованных фильмов для пользователя.
        """
        raise NotImplementedError
