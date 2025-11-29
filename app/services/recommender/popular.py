from typing import Any, Iterable, List, cast

from app.models.recommendations import (
    RecommendationRequest,
    RecommendedItem,
)
from app.services.arango import arango_service
from app.services.recommender.base import Recommender


class PopularRecommender(Recommender):
    """
    Рекомендации по популярности фильмов (по суммарному весу взаимодействий).
    """

    def recommend(self, request: RecommendationRequest) -> List[RecommendedItem]:
        db = arango_service.get_db()

        # AQL: собираем популярные фильмы с учётом веса, исключая уже просмотренные пользователем
        query = """
        LET userId = @user_id

        // Фильмы, с которыми пользователь уже взаимодействовал
        LET userItems = (
          FOR e IN interactions
            FILTER e._from == CONCAT("users/", userId)
            RETURN PARSE_IDENTIFIER(e._to).key
        )

        // Считаем популярность по всем пользователям
        FOR e IN interactions
          COLLECT movieId = PARSE_IDENTIFIER(e._to).key INTO group = e
          LET score = SUM(group[*].weight)
          // исключаем фильмы, которые пользователь уже видел
          FILTER movieId NOT IN userItems
          SORT score DESC
          LIMIT @k
          RETURN {
            movie_id: movieId,
            score: score
          }
        """

        bind_vars = {
            "user_id": request.user_id,
            "k": request.k,
        }

        cursor = db.aql.execute(query, bind_vars=bind_vars)  # type: ignore[arg-type]
        results_iter = cast(Iterable[dict[str, Any]], cursor)
        results = list(results_iter)

        items: List[RecommendedItem] = [
            RecommendedItem(
                item_id=doc["movie_id"],
                score=float(doc["score"]),
                reason="popular",
            )
            for doc in results
        ]

        return items
