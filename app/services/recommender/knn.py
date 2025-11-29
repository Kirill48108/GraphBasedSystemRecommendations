from math import sqrt
from typing import Any, Dict, Iterable, List, cast

from app.models.recommendations import (
    RecommendationRequest,
    RecommendedItem,
)
from app.services.arango import arango_service
from app.services.recommender.base import Recommender


class KNNRecommender(Recommender):
    """
    k-NN по пользователям:
    - строим векторы предпочтений;
    - считаем косинусное сходство;
    - берём n ближайших соседей;
    - агрегируем их фильмы.
    """

    def __init__(self, n_neighbors: int = 20) -> None:
        self.n_neighbors = n_neighbors

    def recommend(self, request: RecommendationRequest) -> List[RecommendedItem]:
        db = arango_service.get_db()
        user_id = request.user_id
        k = request.k

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

        sims: List[tuple[str, float]] = []

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
                sims.append((other_user, sim))

        if not sims:
            return []

        sims.sort(key=lambda x: x[1], reverse=True)
        neighbors = sims[: self.n_neighbors]

        seen = set(target.keys())
        movie_scores: Dict[str, float] = {}

        for neighbor_id, sim in neighbors:
            profile = user_profiles[neighbor_id]
            for movie, w in profile.items():
                if movie in seen:
                    continue
                movie_scores[movie] = movie_scores.get(movie, 0.0) + sim * w

        ranked = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)[:k]

        return [
            RecommendedItem(
                item_id=movie_id,
                score=float(score),
                reason="knn_user_based",
            )
            for movie_id, score in ranked
        ]
