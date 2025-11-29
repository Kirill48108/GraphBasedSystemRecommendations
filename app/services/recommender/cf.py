from math import sqrt
from typing import Any, Dict, Iterable, List, cast

from app.models.recommendations import (
    RecommendationRequest,
    RecommendedItem,
)
from app.services.arango import arango_service
from app.services.recommender.base import Recommender


class CFRecommender(Recommender):
    """
    User-based коллаборативная фильтрация.
    - строим профили пользователей по фильмам (веса взаимодействий);
    - считаем косинусное сходство;
    - агрегируем фильмы соседей, которые user ещё не смотрел.
    """

    def recommend(self, request: RecommendationRequest) -> List[RecommendedItem]:
        db = arango_service.get_db()
        user_id = request.user_id
        k = request.k

        # Собираем все взаимодействия
        query = """
        FOR e IN interactions
          LET u = PARSE_IDENTIFIER(e._from).key
          LET m = PARSE_IDENTIFIER(e._to).key
          RETURN {
            user_id: u,
            movie_id: m,
            weight: e.weight
          }
        """
        cursor = db.aql.execute(query)
        events_iter = cast(Iterable[dict[str, Any]], cursor)
        events = list(events_iter)

        # профили: user -> {movie: weight}
        user_profiles: Dict[str, Dict[str, float]] = {}
        for row in events:
            u = row["user_id"]
            m = row["movie_id"]
            w = float(row["weight"])
            user_profiles.setdefault(u, {})
            user_profiles[u][m] = user_profiles[u].get(m, 0.0) + w

        if user_id not in user_profiles:
            return []

        target = user_profiles[user_id]
        target_norm = sqrt(sum(w * w for w in target.values()))
        if target_norm == 0.0:
            return []

        # сходство с другими пользователями
        similarities: Dict[str, float] = {}
        for other_user, profile in user_profiles.items():
            if other_user == user_id:
                continue
            dot = 0.0
            for movie, w in target.items():
                if movie in profile:
                    dot += w * profile[movie]
            if dot == 0.0:
                continue
            other_norm = sqrt(sum(w * w for w in profile.values()))
            if other_norm == 0.0:
                continue
            sim = dot / (target_norm * other_norm)
            if sim > 0.0:
                similarities[other_user] = sim

        if not similarities:
            return []

        seen = set(target.keys())
        movie_scores: Dict[str, float] = {}

        for other_user, sim in similarities.items():
            profile = user_profiles[other_user]
            for movie, w in profile.items():
                if movie in seen:
                    continue
                movie_scores[movie] = movie_scores.get(movie, 0.0) + sim * w

        ranked = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)[:k]

        return [
            RecommendedItem(
                item_id=movie_id,
                score=float(score),
                reason="cf_user_based",
            )
            for movie_id, score in ranked
        ]
